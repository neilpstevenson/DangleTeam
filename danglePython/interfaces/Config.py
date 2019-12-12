import json

class Config:
	def __init__(self, filename='config.json'):
		self.filename = filename
		try:
			with open(self.filename, 'r') as f:
				self.config = json.loads(f)
			self.configChanged = False
		except:
			self.config = {}
			self.configChanged = True

	def get(self, key, default):
		if key in self.config:
			return self.config[key]
		else:
			self.config[key] = default
			self.configChanged = True
			return default
	 
	def set(self, key, value):
		self.config[key] = value
		self.configChanged = True
			
	def save(self):
		if self.configChanged:
			with open(self.filename, 'w+') as f:
				json.dumps(self.config, f, indent=2)
			self.configChanged = False

