import json

class Config:
	def __init__(self, filename='config.json'):
		self.filename = filename
		try:
			with open(self.filename, 'r') as f:
				self.config = json.loads(f.read())
		except:
			self.config = {}

	def get(self, key, default):
		if key in self.config:
			return self.config[key]
		else:
			self.config[key] = default
			return default
	 
	def set(self, key, value):
		self.config[key] = value
			
	def save(self):
		with open(self.filename, 'w+') as f:
			f.write(json.dumps(self.config))

#c = Config()
#print( c.get("test1", "defaultval") )
#c.set("test1", "updated")
#print( c.get("test1", "defaultval") )
#print( c.get("testInt", 0) )
#c.set("testInt", c.get("testInt", 0) + 1 )
#print( c.get("testInt", 0) )
#c.save()
