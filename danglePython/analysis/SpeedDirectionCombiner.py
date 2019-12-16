from interfaces.SensorInterface import SensorInterface

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
	
	def nonLinearTransform(self, rawForwardTorque, rawSteerTorque):
		# Apply non-linear transform
		nominal = rawForwardTorque + rawSteerTorque
		# For the speeding up wheel, just use the nominal squared
		if rawForwardTorque > 0.02 and nominal >= rawForwardTorque*0.95:
			return nominal*nominal
		elif rawForwardTorque < -0.02 and nominal <= rawForwardTorque*0.95:
			return -nominal*nominal
		# For a slowing wheel, stop the wheel
		elif rawForwardTorque > 0.02 and nominal >= 0.0:
			return 0.0
		elif rawForwardTorque < -0.02 and nominal <= 0.0:
			return 0.0
		# Where we are turning in the spot, use the steer value only
		else:
			return rawSteerTorque * 1.3
			
			
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
		print(f"rawForwardTorque: {rawForwardTorque:4.2f}, rawSteerTorque: {rawSteerTorque:4.2f}, scaledValue: {scaledValue:4.2f}")
		if scaledValue > self.max:
			return self.max
		elif scaledValue < self.min:
			return self.min
		return scaledValue
