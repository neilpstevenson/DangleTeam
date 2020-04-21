#include <stdio.h>
#include <stdint.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <math.h>
#ifdef USE_SHARED_MEMORY
#include <sys/shm.h>		//Used for shared memory
#endif
#ifdef USE_MEMORY_MAPPED_FILE
#include <sys/mman.h>
#include <fcntl.h>
#endif

#include "core/driver/eMPL/inv_mpu.h"
#include "core/driver/eMPL/inv_mpu_dmp_motion_driver.h"

#define min(a,b) ((a>b)?b:a)
#define max(a,b) ((a<b)?b:a)

/* Data requested by client. */
#define PRINT_ACCEL     (0x01)
#define PRINT_GYRO      (0x02)
#define PRINT_QUAT      (0x04)

#define ACCEL_ON        (0x01)
#define GYRO_ON         (0x02)
#define COMPASS_ON      (0x04)

#define MOTION          (0)
#define NO_MOTION       (1)

/* Starting sampling rate. */
#define DEFAULT_MPU_HZ  (200)
#define COMPASS_SAMPLE_RATE_HZ	(5)

#define FLASH_SIZE      (512)
#define FLASH_MEM_START ((void*)0x1800)

#ifdef USE_SHARED_MEMORY
void *shared_memory1_pointer = (void *)0;
int shared_memory1_id;
#endif 

#if defined(USE_MEMORY_MAPPED_FILE) || defined(USE_SHARED_MEMORY)
#define SHARED_BUFFER_SIZE 1024

struct shared_reading_struct {
	unsigned long timestamp;
	float accel[3];
	float gyro[3];
	float quaternion[4];
	unsigned long flags;
};

struct mmap_memory_struct {
	unsigned long sample_number;
	unsigned short oldest_sample;
	unsigned short latest_sample;
	unsigned short buffer_size;
	unsigned char orientation;
	unsigned char tap_count;
	unsigned char tap_direction;
	unsigned char dummy[3];
	float mag[3];
	struct shared_reading_struct shared_readings_buffer[SHARED_BUFFER_SIZE];
};

struct mmap_memory_struct *mmap_memory;
#endif

struct hal_s {
	unsigned char sensors;
	unsigned char dmp_on;
	unsigned char wait_for_tap;
	volatile unsigned char new_gyro;
	unsigned short report;
	unsigned short dmp_features;
	unsigned char motion_int_mode;
};
static struct hal_s hal = { 0 };

/* The sensors can be mounted onto the board in any orientation. The mounting
 * matrix seen below tells the MPL how to rotate the raw data from thei
 * driver(s).
 * TODO: The following matrices refer to the configuration on an internal test
 * board at Invensense. If needed, please modify the matrices to match the
 * chip-to-body matrix for your particular set up.
 */
#define HORIZONTAL_ORIENTATION
#if defined HORIZONTAL_ORIENTATION
static signed char gyro_orientation[9] = { -1,  0,  0,
										    0, -1,  0,
										    0,  0,  1 };  // 4/5/2 == -Z-Y+X orientation, i.e. mounted horizontally
#elif defined VERTICAL_ORIENTATION
static signed char gyro_orientation[9] = {  0,  0, -1,
										   -1,  0,  0,
										    0,  1,  0 };  // mounted on short edge
#else
static signed char gyro_orientation[9] = {  0, -1,  0,
										    0,  0, -1,
										    1,  0,  0 };  // mounted on long edge
#endif

/* These next two functions converts the orientation matrix (see
 * gyro_orientation) to a scalar representation for use by the DMP.
 * NOTE: These functions are borrowed from Invensense's MPL.
 */
static inline unsigned short inv_row_2_scale(const signed char *row)
{
	unsigned short b;

	if (row[0] > 0)
		b = 0;
	else if (row[0] < 0)
		b = 4;
	else if (row[1] > 0)
		b = 1;
	else if (row[1] < 0)
		b = 5;
	else if (row[2] > 0)
		b = 2;
	else if (row[2] < 0)
		b = 6;
	else
		b = 7;      // error
	return b;
}

static inline unsigned short inv_orientation_matrix_to_scalar(
	const signed char *mtx)
{
	unsigned short scalar;

	/*
	   XYZ  010_001_000 Identity Matrix
	   XZY  001_010_000
	   YXZ  010_000_001
	   YZX  000_010_001
	   ZXY  001_000_010
	   ZYX  000_001_010
	 */

	scalar = inv_row_2_scale(mtx);
	scalar |= inv_row_2_scale(mtx + 3) << 3;
	scalar |= inv_row_2_scale(mtx + 6) << 6;


	return scalar;
}

/* Handle sensor on/off combinations. */
static void setup_gyro(void)
{
	unsigned char mask = 0;
	if (hal.sensors & ACCEL_ON)
		mask |= INV_XYZ_ACCEL;
	if (hal.sensors & GYRO_ON)
		mask |= INV_XYZ_GYRO;
#ifdef MPU9250
	if (hal.sensors & COMPASS_ON)
		mask |= INV_XYZ_COMPASS;
#endif
	
	/* If you need a power transition, this function should be called with a
	 * mask of the sensors still enabled. The driver turns off any sensors
	 * excluded from this mask.
	 */
	mpu_set_sensors(mask);
	if (!hal.dmp_on)
		mpu_configure_fifo(mask);
}

void tap_cb(unsigned char direction, unsigned char count)
{
	fprintf(stderr, "tap: %d, %d\n", direction, count);
	
	mmap_memory->tap_count = count;
	mmap_memory->tap_direction = direction;
	
	//Check pedometer reading
	unsigned long ped_count;
	if(dmp_get_pedometer_step_count(&ped_count) >= 0)
		fprintf(stderr, "pedometer: %ld\n", ped_count);

#ifdef MPU9250	
	short compass_data[3];
	unsigned long timestamp;
	if(mpu_get_compass_reg(compass_data, &timestamp) >= 0)
	{
		float angle = atan2(compass_data[1], compass_data[2]) * 180.0 / M_PI;
		fprintf(stderr, "compass: %d,%d,%d = %fdeg\n", compass_data[0], compass_data[1], compass_data[2], angle);
	}
#endif
}

void android_orient_cb(unsigned char orient)
{
	fprintf(stderr, "orient: %d\n",orient);
	mmap_memory->orientation = 0;
}

#ifdef MPU9250
void compass_calibrate(float *bias, float *scale) 
{
	short mag_max[3] = {-32767, -32767, -32767}, mag_min[3] = {32767, 32767, 32767};

	fprintf(stderr, "Mag Calibration for compass\n"); 
	fprintf(stderr, "Wave device in a figure eight until done!\n");
	
	// Setup mag sensor
	mpu_set_compass_sample_rate(100);

	sleep(1);

	// shoot for ~fifteen seconds of mag data
	int sample_count = 1500;  // at 100 Hz ODR, new mag data is available every 10 ms
	char have_readings = 0;
	for(int ii = 0; ii < sample_count; ii++) 
	{
		short mag_raw[3];
		if(mpu_get_compass_reg(mag_raw, NULL) >= 0)
		{
			for (int jj = 0; jj < 3; jj++) 
			{
			  if(mag_raw[jj] > mag_max[jj]) mag_max[jj] = mag_raw[jj];
			  if(mag_raw[jj] < mag_min[jj]) mag_min[jj] = mag_raw[jj];
			}
			have_readings = 1;
		}
		usleep(10000);	// limit to 100/sec
	}
	
	// Restore sample rate 
	mpu_set_compass_sample_rate(COMPASS_SAMPLE_RATE_HZ);

	if(!have_readings)
	{
		fprintf(stderr, "Error: no compass found.\n"); 
		return;
	}
	
	fprintf(stderr, "Results:\n"); 
	fprintf(stderr, " mag x,y,z min/max: %d/%d, %d/%d, %d/%d\n",
		mag_min[0], mag_max[0], mag_min[1], mag_max[1], mag_min[2], mag_max[2] );

    // Get hard iron correction
	short mag_bias[3];
    mag_bias[0]  = (mag_max[0] + mag_min[0])/2;  // get average x mag bias in counts
    mag_bias[1]  = (mag_max[1] + mag_min[1])/2;  // get average y mag bias in counts
    mag_bias[2]  = (mag_max[2] + mag_min[2])/2;  // get average z mag bias in counts

    bias[0] = (float) mag_bias[0]; //*_mRes*magCalibration[0];  // save mag biases in G for main program
    bias[1] = (float) mag_bias[1]; //*_mRes*magCalibration[1];   
    bias[2] = (float) mag_bias[2]; //*_mRes*magCalibration[2];  

	fprintf(stderr, " bias: x,y,z: %d, %d, %d\n",
		mag_bias[0], mag_bias[1], mag_bias[2] );

    // Get soft iron correction estimate
	float mag_scale[3];
    mag_scale[0]  = (mag_max[0] - mag_min[0])/2.0;  // get average x axis max chord length in counts
    mag_scale[1]  = (mag_max[1] - mag_min[1])/2.0;  // get average y axis max chord length in counts
    mag_scale[2]  = (mag_max[2] - mag_min[2])/2.0;  // get average z axis max chord length in counts

    float avg_rad = (mag_scale[0] + mag_scale[1] + mag_scale[2]) / 3.0;

    scale[0] = avg_rad/mag_scale[0];
    scale[1] = avg_rad/mag_scale[1];
    scale[2] = avg_rad/mag_scale[2];
	
	fprintf(stderr, " scale: x,y,z: %4.2f,  %4.2f,  %4.2f\n",
		scale[0], scale[1], scale[2] );

	fprintf(stderr, "Mag Calibration done.\n"); 
}
#endif

int main(int argc, char**argv)
{
	fprintf(stderr, "=================== Neil's mpu9250 Gyro/Accel/Compass Test ==================\n");
	char debug = argc > 1;
	char calibrateCompass = 0;
	
	unsigned char accel_fsr;
	unsigned short gyro_rate, gyro_fsr;
	short compass_data_max[3], compass_data_min[3];
	memset(compass_data_max, 0, sizeof(compass_data_max));
	memset(compass_data_min, 0, sizeof(compass_data_min));
	
#ifdef USE_SHARED_MEMORY	
	// Open the shared memory to pass to other apps
	shared_memory1_id = shmget((key_t)4324527, sizeof(struct mmap_memory_struct), 0666 | IPC_CREAT);		//<<<<< SET THE SHARED MEMORY KEY    (Shared memory key , Size in bytes, Permission flags)
	if (shared_memory1_id == -1)
	{
		fprintf(stderr, "Shared memory shmget() failed\n");
		exit(EXIT_FAILURE);
	}
	//Make the shared memory accessible to the program
	shared_memory1_pointer = shmat(shared_memory1_id, (void *)0, 0);
	if (shared_memory1_pointer == (void *)-1)
	{
		fprintf(stderr, "Shared memory shmat() failed\n");
		exit(EXIT_FAILURE);
	}
	fprintf(stderr, "Shared memory attached at %X\n", (int)shared_memory1_pointer);
	//Assign the shared_memory segment
	mmap_memory = (struct mmap_memory_struct *)shared_memory1_pointer;
#endif

#ifdef USE_MEMORY_MAPPED_FILE
    int mmap_fd = open("/dev/shm/mpu_values_shared.mmf", O_RDWR | O_CREAT | O_TRUNC, 0600); //6 = read+write for me!
    lseek(mmap_fd, sizeof(*mmap_memory)-1, SEEK_SET);
    write(mmap_fd, "\0", 1);
    mmap_memory = (struct mmap_memory_struct*)mmap(NULL, sizeof(*mmap_memory), PROT_READ | PROT_WRITE, MAP_SHARED, mmap_fd, 0);
	if (mmap_memory == (void *)-1)
	{
		fprintf(stderr, "Memory mapped file open failed\n");
		exit(EXIT_FAILURE);
	}
#endif
	unsigned long sample_count = 0;
	mmap_memory->latest_sample = 0;
	mmap_memory->oldest_sample = 0;
	mmap_memory->buffer_size = SHARED_BUFFER_SIZE;

	/* Set up gyro.
	 * Every function preceded by mpu_ is a driver function and can be found
	 * in inv_mpu.h.
	 */
	int result = mpu_init(0);
	if (result)
	{
		fprintf(stderr, "mpu_init returned %d\n", result);
		exit(result);
	}

	/* If you're not using an MPU9150 AND you're not using DMP features, this
	 * function will place all slaves on the primary bus.
	 * mpu_set_bypass(1);
	 */

	fprintf(stderr, "Initialising sensors and configuring...\n");
	/* Get/set hardware configuration. Start gyro. */
	 /* Wake up all sensors. */
	mpu_set_sensors(INV_XYZ_GYRO | INV_XYZ_ACCEL | INV_XYZ_COMPASS);
	/* Push both gyro and accel data into the FIFO. */
	mpu_configure_fifo(INV_XYZ_GYRO | INV_XYZ_ACCEL);
	mpu_set_sample_rate(DEFAULT_MPU_HZ);
	mpu_set_gyro_fsr(1000); //default is 2000, min is 250
	/* Read back configuration in case it was set improperly. */
	mpu_get_sample_rate(&gyro_rate);
	mpu_get_gyro_fsr(&gyro_fsr);
	mpu_get_accel_fsr(&accel_fsr);
	unsigned short compass_rate;
	mpu_get_compass_sample_rate(&compass_rate);
	fprintf(stderr, "mpu_get_sample_rate=%d, mpu_get_gyro_fsr=%d, mpu_get_accel_fsr=%d,compass_rate=%d\n", gyro_rate, gyro_fsr, accel_fsr, compass_rate);

	/* Initialize HAL state variables. */
	memset(&hal, 0, sizeof(hal));
	hal.sensors = ACCEL_ON | GYRO_ON | COMPASS_ON;
	hal.report = PRINT_QUAT;

	/* To initialize the DMP:
	 * 1. Call dmp_load_motion_driver_firmware(). This pushes the DMP image in
	 *    inv_mpu_dmp_motion_driver.h into the MPU memory.
	 * 2. Push the gyro and accel orientation matrix to the DMP.
	 * 3. Register gesture callbacks. Don't worry, these callbacks won't be
	 *    executed unless the corresponding feature is enabled.
	 * 4. Call dmp_enable_feature(mask) to enable different features.
	 * 5. Call dmp_set_fifo_rate(freq) to select a DMP output rate.
	 * 6. Call any feature-specific control functions.
	 *
	 * To enable the DMP, just call mpu_set_dmp_state(1). This function can
	 * be called repeatedly to enable and disable the DMP at runtime.
	 *
	 * The following is a short summary of the features supported in the DMP
	 * image provided in inv_mpu_dmp_motion_driver.c:
	 * DMP_FEATURE_LP_QUAT: Generate a gyro-only quaternion on the DMP at
	 * 200Hz. Integrating the gyro data at higher rates reduces numerical
	 * errors (compared to integration on the MCU at a lower sampling rate).
	 * DMP_FEATURE_6X_LP_QUAT: Generate a gyro/accel quaternion on the DMP at
	 * 200Hz. Cannot be used in combination with DMP_FEATURE_LP_QUAT.
	 * DMP_FEATURE_TAP: Detect taps along the X, Y, and Z axes.
	 * DMP_FEATURE_ANDROID_ORIENT: Google's screen rotation algorithm. Triggers
	 * an event at the four orientations where the screen should rotate.
	 * DMP_FEATURE_GYRO_CAL: Calibrates the gyro data after eight seconds of
	 * no motion.
	 * DMP_FEATURE_SEND_RAW_ACCEL: Add raw accelerometer data to the FIFO.
	 * DMP_FEATURE_SEND_RAW_GYRO: Add raw gyro data to the FIFO.
	 * DMP_FEATURE_SEND_CAL_GYRO: Add calibrated gyro data to the FIFO. Cannot
	 * be used in combination with DMP_FEATURE_SEND_RAW_GYRO.
	 */
	fprintf(stderr, "Loading DMP firmware..\n");
	dmp_load_motion_driver_firmware();
	dmp_set_orientation(
		inv_orientation_matrix_to_scalar(gyro_orientation));

	// Setup tap detection
	dmp_set_tap_thresh(7, 1);
	dmp_set_tap_time_multi(500);
	dmp_register_tap_cb(tap_cb);

	// Setup orientation change detection
	dmp_register_android_orient_cb(android_orient_cb);
	
	/*
	 * Known Bug -
	 * DMP when enabled will sample sensor data at 200Hz and output to FIFO at the rate
	 * specified in the dmp_set_fifo_rate API. The DMP will then sent an interrupt once
	 * a sample has been put into the FIFO. Therefore if the dmp_set_fifo_rate is at 25Hz
	 * there will be a 25Hz interrupt from the MPU device.
	 *
	 * There is a known issue in which if you do not enable DMP_FEATURE_TAP
	 * then the interrupts will be at 200Hz even if fifo rate
	 * is set at a different rate. To avoid this issue include the DMP_FEATURE_TAP
	 */
	hal.dmp_features = DMP_FEATURE_6X_LP_QUAT 
		| DMP_FEATURE_TAP 
		| DMP_FEATURE_ANDROID_ORIENT 
		| DMP_FEATURE_SEND_RAW_ACCEL 
		| DMP_FEATURE_SEND_CAL_GYRO 
		| DMP_FEATURE_GYRO_CAL;
	dmp_enable_feature(hal.dmp_features);
	dmp_set_fifo_rate(DEFAULT_MPU_HZ);
	mpu_set_dmp_state(1);
	hal.dmp_on = 1;

	fprintf(stderr, "Starting gyro..\n");

	setup_gyro();

	// Enable auto-calibration of the gyro (requires 8 seconds of no motion)
	dmp_enable_gyro_cal(1);

#ifdef MPU9250
	if(debug)
	{
		// New self test
		long selftest_gyro[3];
		long selftest_accel[3];
		int selftest_result = mpu_run_6500_self_test(selftest_gyro, selftest_accel, 1);
		fprintf(stderr, "Self test returned 0x%02x.  gyro bias: %ld, %ld, %ld; accel bias: %ld, %ld, %ld\n", selftest_result,
			selftest_gyro[0], selftest_gyro[1], selftest_gyro[2],
			selftest_accel[0], selftest_accel[1], selftest_accel[2]);
	}
#endif
	
	hal.report |= (PRINT_GYRO | PRINT_ACCEL | PRINT_QUAT);

#ifdef MPU9250
	// Calibrate the compass
	float mag_compass_bias[3] = {0,0,0}, mag_compass_scale[3] = {1,1,1};
	if(calibrateCompass)
	{
		compass_calibrate(mag_compass_bias, mag_compass_scale);
	}
#endif

	fprintf(stderr, "Running...\n");

	while (1) {

		unsigned long sensor_timestamp;
		usleep(1000);//Limit to 200/second
		
		{
			short gyro[3], accel[3], sensors;
			float gx = 0, gy = 0, gz = 0;
			float ax = 0, ay = 0, az = 0;
			float qw = 0, qx = 0, qy = 0, qz = 0;

			unsigned char more;
			long quat[4];
			/* This function gets new data from the FIFO when the DMP is in
			 * use. The FIFO can contain any combination of gyro, accel,
			 * quaternion, and gesture data. The sensors parameter tells the
			 * caller which data fields were actually populated with new data.
			 * For example, if sensors == (INV_XYZ_GYRO | INV_WXYZ_QUAT), then
			 * the FIFO isn't being filled with accel data.
			 * The driver parses the gesture data to determine if a gesture
			 * event has occurred; on an event, the application will be notified
			 * via a callback (assuming that a callback function was properly
			 * registered). The more parameter is non-zero if there are
			 * leftover packets in the FIFO.
			 */
			// Flush the FIFO
			for (more = 1; more;)
			{
				sensors = 0;
				dmp_read_fifo(gyro, accel, quat, &sensor_timestamp, &sensors,
					&more);
				if (!more)
					hal.new_gyro = 0;
			}
			/* Gyro and accel data are written to the FIFO by the DMP in chip
			 * frame and hardware units. This behavior is convenient because it
			 * keeps the gyro and accel outputs of dmp_read_fifo and
			 * mpu_read_fifo consistent.
			 */
	//		fprintf(stderr, "sensors: %02x, hal.report: %02x\n", sensors, hal.report);
			char hasValue = 0;
			if (sensors & INV_XYZ_GYRO && hal.report & PRINT_GYRO)
			{
				gx = gyro[0] / (32768.0 / gyro_fsr);
				gy = gyro[1] / (32768.0 / gyro_fsr);
				gz = gyro[2] / (32768.0 / gyro_fsr);
				hasValue = 1;

				if(debug)
					fprintf(stderr, "Gyro xyz: % 2.4fdps, % 2.4fdps, % 2.4fdps\n", gx, gy, gy);
			}

			if (sensors & INV_XYZ_ACCEL && hal.report & PRINT_ACCEL)
			{
				ax = accel[0] / (32768.0 / accel_fsr);
				ay = accel[1] / (32768.0 / accel_fsr);
				az = accel[2] / (32768.0 / accel_fsr);
				hasValue = 1;

				if(debug)
					fprintf(stderr, "Accel xyz: % 2.4fG, % 2.4fG, % 2.4fG\n", ax, ay, az );
			}

			/* Unlike gyro and accel, quaternions are written to the FIFO in
			 * the body frame, q30. The orientation is set by the scalar passed
			 * to dmp_set_orientation during initialization.
			 */
			if (sensors & INV_WXYZ_QUAT && hal.report & PRINT_QUAT)
			{
				qw = quat[0] / (float)0x40000000L;
				qx = quat[1] / (float)0x40000000L;
				qy = quat[2] / (float)0x40000000L;
				qz = quat[3] / (float)0x40000000L;
				hasValue = 1;

				if(debug)
					fprintf(stderr, "Quat wxyz: % 2.4f, % 2.4f, % 2.4f, % 2.4f\n", qw, qx, qy, qz);
			}
			
#ifdef MPU9250
			// Get compass data, but only at 1/20th of the rate
			if(hasValue && sample_count % (DEFAULT_MPU_HZ/COMPASS_SAMPLE_RATE_HZ) == 0)
			{
				short compass_data[3];
				if(mpu_get_compass_reg(compass_data, NULL) >= 0)
				{
					float mag_calibrated[3];
					mag_calibrated[0] = (compass_data[0] - mag_compass_bias[0]) * mag_compass_scale[0];
					mag_calibrated[1] = (compass_data[1] - mag_compass_bias[1]) * mag_compass_scale[1];
					mag_calibrated[2] = (compass_data[2] - mag_compass_bias[2]) * mag_compass_scale[2];
					
					if(debug)
					{
						float angle = atan2(mag_calibrated[1], mag_calibrated[0]) * 180.0 / M_PI;
						fprintf(stderr, "compass: %d,%d,%d (calibrated %4.1f,%4.1f,%4.1f) => %4.1fdeg\n", 
							compass_data[0], compass_data[1], compass_data[2], 
							mag_calibrated[0], mag_calibrated[1], mag_calibrated[2], 
							angle);
					}
					
					mmap_memory->mag[0] = mag_calibrated[0];
					mmap_memory->mag[1] = mag_calibrated[1];
					mmap_memory->mag[2] = mag_calibrated[2];
				}
			}
#endif

			if(hasValue)
			{
				sample_count++;
			
#if defined(USE_SHARED_MEMORY) || defined(USE_MEMORY_MAPPED_FILE)	
				unsigned short new_sample = mmap_memory->latest_sample + 1;
				if(new_sample >= SHARED_BUFFER_SIZE)
				{
					new_sample = 0;
				}
				unsigned short oldest_sample = mmap_memory->oldest_sample;
				if(oldest_sample == new_sample)
				{
					oldest_sample++;
					if(oldest_sample >= SHARED_BUFFER_SIZE)
					{
						oldest_sample = 0;
					}
				}
				// First write the date to the buffer	
				mmap_memory->shared_readings_buffer[new_sample].timestamp = sensor_timestamp;
				mmap_memory->shared_readings_buffer[new_sample].accel[0] = ax;
				mmap_memory->shared_readings_buffer[new_sample].accel[1] = ay;
				mmap_memory->shared_readings_buffer[new_sample].accel[2] = az;
				mmap_memory->shared_readings_buffer[new_sample].gyro[0] = gx;
				mmap_memory->shared_readings_buffer[new_sample].gyro[1] = gy;
				mmap_memory->shared_readings_buffer[new_sample].gyro[2] = gz;
				mmap_memory->shared_readings_buffer[new_sample].quaternion[0] = qw;
				mmap_memory->shared_readings_buffer[new_sample].quaternion[1] = qx;
				mmap_memory->shared_readings_buffer[new_sample].quaternion[2] = qy;
				mmap_memory->shared_readings_buffer[new_sample].quaternion[3] = qz;
				mmap_memory->shared_readings_buffer[new_sample].flags = 0;
				// Update the buffer info
				mmap_memory->sample_number = sample_count;
				mmap_memory->latest_sample = new_sample;
				mmap_memory->oldest_sample = oldest_sample;

				if(debug)
					fprintf(stderr, "#%lu: Time %lu: buffer: %d -> %d\n", sample_count, sensor_timestamp, oldest_sample, new_sample );
#endif	
			}
		}
	}

	return 0;
}

