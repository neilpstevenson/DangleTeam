// Simple RPi 3B+ implemenatoin for the reference InveSense MPU6050 drivers
#include <time.h>
#include <stdio.h>
#include <sys/types.h>
#include <sys/stat.h>
#include <fcntl.h>
#include <errno.h>
#include <unistd.h>
#include <stdlib.h>
#include <string.h>
#include <stdint.h>
#include <linux/i2c-dev.h>
#include <sys/ioctl.h>

#define DEBUG_MESG 0

int OpenI2C(unsigned char slave_addr, unsigned char reg_addr)
{
	static int fd = -1;
	if (fd < 0)
	{
		fd = open("/dev/i2c-1", O_RDWR);

		if (fd < 0) {
			fprintf(stderr, "Failed to open device: %s\n", strerror(errno));
			return(-1);
		}
		if (ioctl(fd, I2C_SLAVE, slave_addr) < 0) {
			fprintf(stderr, "Failed to select device: %s\n", strerror(errno));
			return(-1);
		}
#if DEBUG_MESG
		fprintf(stderr, "Opened device ok: %02x, reg=%02x\n", slave_addr, reg_addr);
#endif
	}
	if (ioctl(fd, I2C_SLAVE, slave_addr) < 0) {
		fprintf(stderr, "Failed to select device: %s\n", strerror(errno));
		return(-1);
	}
	return fd;
}


int i2c_write(unsigned char slave_addr, unsigned char reg_addr,
	unsigned char length, unsigned char const *data)
{
	int fd = OpenI2C(slave_addr, reg_addr);
	int count = -1;
	if (fd >= 0)
	{
		unsigned char *data2 = malloc(length + 1);
		*data2 = reg_addr;
		memcpy(data2 + 1, data, length);
		count = write(fd, data2, length+1);
#if DEBUG_MESG
		fprintf(stderr, "i2c_write written %d of %d, reg %02x\n", length+1, count, reg_addr);
		for (int i = 0; i < count; i++)
			printf("%02x ", data2[i]);
		printf("\n");
#endif
		free(data2);
	}

	return count!=(length+1);
}

int i2c_read(unsigned char slave_addr, unsigned char reg_addr,
	unsigned char length, unsigned char *data)
{
	int fd = OpenI2C(slave_addr, reg_addr);
	int count = -1;
	if (write(fd, &reg_addr, 1) != 1) {
		fprintf(stderr, "Failed to write reg: %s\n", strerror(errno));
		return(-1);
	}
	if (fd >= 0)
	{
		count = read(fd, data, length);
#if DEBUG_MESG
		fprintf(stderr, "i2c_read read %d of  %d, reg %02x\n", length, count, reg_addr);
		for (int i = 0; i < count; i++)
			printf("%02x ", data[i]);
		printf("\n");
#endif
	}

	return count!=length;
}

int delay_ms(unsigned long num_ms)
{
	usleep(num_ms * 1000UL);
	return 0;
}

int get_ms(unsigned long *count)
{
	struct timespec ts;
	timespec_get(&ts, TIME_UTC);
	*count = ts.tv_sec * 1000L + (ts.tv_nsec / 1000000L);
	return 0;
}

int reg_int_cb(struct int_param_s *int_param)
{
	return 0;
}