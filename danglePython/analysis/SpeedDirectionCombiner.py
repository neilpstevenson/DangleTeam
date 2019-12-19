from interfaces.SensorInterface import SensorInterface
from interfaces.Config import Config

class SpeedDirectionCombiner(SensorInterface):
	""" Class to combine a speed with a direction adjustment in a non-linear fasion.  This
	is intended to compensate for real-world motors that won't accelerate from stationary easily
	and tend to coast once going.
	"""
	
	def __init__(self, forwardTorque, steerTorque, min = -1.0, max = 1.0, scaling = 1.0, offset = 0.0):
		SensorInterface.__init__(self)
		self.forwardTorque = forwardTorque
		self.steerTorque = steerTorque
		self.min = min
		self.max = max
		self.scaling = scaling
		self.offset = offset
		# Get config
		config = Config()
		self.speedsteerSlow = config.get("speedsteer.slow", 0.6)
		self.speedsteerMedDecel = config.get("speedsteer.med.decel", 0.7)
		config.save()
	
	def nonLinearTransform(self, rawForwardTorque, rawSteerTorque):
		if (rawForwardTorque < self.speedsteerSlow and rawForwardTorque > -self.speedsteerSlow) and (rawSteerTorque > 0.05 or rawSteerTorque < -0.05):
			# Attempting to spin at slow speed or stationary
			nominal = (rawForwardTorque*rawForwardTorque if rawForwardTorque>=0.0 else -rawForwardTorque*rawForwardTorque) + rawSteerTorque
			return nominal
		elif (rawSteerTorque > 0.05 and rawForwardTorque >= 0.0) or (rawSteerTorque < -0.05 and rawForwardTorque <= 0.0):
			# Attempting to turn at higher speed, same wheel
			combined = rawForwardTorque*self.speedsteerMedDecel + rawSteerTorque
			nominal = combined*combined if combined>=0.0 else -combined*combined
			return nominal
		elif (rawSteerTorque > 0.05 and rawForwardTorque < 0.0) or (rawSteerTorque < -0.05 and rawForwardTorque > 0.0):
			# Attempting to turn at higher speed, different wheel
			combined = rawForwardTorque*self.speedsteerMedDecel + rawSteerTorque
			nominal = combined*combined if combined>=0.0 else -combined*combined
			return nominal
		else:
			# Not really turning much
			combined = rawForwardTorque + rawSteerTorque
			nominal = combined*combined if combined>=0.0 else -combined*combined
			return nominal
		#else:
		#	# square of both
		#	nominal += rawSteerTorque*rawSteerTorque if rawSteerTorque>=0.0 else -rawSteerTorque*rawSteerTorque
		#	return nominal
		## Apply non-linear transform
		#nominal = rawForwardTorque + rawSteerTorque
		## For the speeding up wheel, just use the nominal squared
		#if rawForwardTorque > 0.02 and nominal >= rawForwardTorque*0.95:
		#	return nominal*nominal
		#elif rawForwardTorque < -0.02 and nominal <= rawForwardTorque*0.95:
		#	return -nominal*nominal
		## For a slowing wheel, stop the wheel
		#elif rawForwardTorque > 0.02 and nominal >= 0.0:
		#	return 0.0
		#elif rawForwardTorque < -0.02 and nominal <= 0.0:
		#	return 0.0
		## Where we are turning in the spot, use the steer value only
		#else:
		#	return rawSteerTorque * 1.3
			
			
	def getValue(self):
		if type(self.forwardTorque) is list:
			rawForwardTorque = sum(map(lambda x: x.getValue(), self.forwardTorque))
		else:
			rawForwardTorque = self.forwardTorque.getValue()
		if type(self.steerTorque) is list:
			rawSteerTorque = sum(map(lambda x: x.getValue(), self.steerTorque))
		else:
			rawSteerTorque = self.steerTorque.getValue()	
		scaledValue = self.nonLinearTransform(rawForwardTorque, rawSteerTorque)*self.scaling + self.offset
		print(f"forward: {rawForwardTorque:4.2f}, steer: {rawSteerTorque:4.2f}, result: {scaledValue:4.2f}")
		if scaledValue > self.max:
			return self.max
		elif scaledValue < self.min:
			return self.min
		return scaledValue
