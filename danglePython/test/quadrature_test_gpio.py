import time
import pigpio

# Toggle GPIO lines like a quadrature encoder

PIN_A = 20
PIN_B = 21
PIN_C = 22
PIN_D = 12

pi = pigpio.pi()
pi.set_mode(PIN_A, pigpio.OUTPUT)
pi.set_mode(PIN_B, pigpio.OUTPUT)
pi.set_mode(PIN_C, pigpio.OUTPUT)
pi.set_mode(PIN_D, pigpio.OUTPUT)

for i in range(1000):
	for p in range(4):
		pi.write(PIN_B, (0 if p == 0 or p == 1 else 1))
		pi.write(PIN_A, (0 if p == 0 or p == 3 else 1))
		#pi.write(PIN_A, (0 if i < 300 or i > 500 else 1))
		pi.write(PIN_D, (0 if p == 0 or p == 1 else 1))
		pi.write(PIN_C, (0 if p == 0 or p == 3 else 1))
		#time.sleep(0.001)
print(f"{i}")
