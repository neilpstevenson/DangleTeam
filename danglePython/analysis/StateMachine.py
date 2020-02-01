# Simple state machine helper class
class StateMachine:

	def __init__(self, initialState = None):
		self.states = {}
		self.state = initialState
		
	# Add a new possible state
	def addState(self, stateId, enterStateFunc, processFunc, exitStateFunc):
		self.states[stateId] = (enterStateFunc, processFunc, exitStateFunc)
		
	def process(self):
		# Call state processing function
		if self.state != None and self.states[self.state][1] != None:
			self.states[self.state][1]()
		
	def changeState(self, newState):
		if self.state != newState:
			print(f"State change: {self.state} to {newState}")
			# Call Exit state
			if self.state != None and self.states[self.state][2] != None:
				self.states[self.state][2]()
			# Change state
			self.state = newState
			# Call Enter state
			if self.state != None and self.states[self.state][0] != None:
				self.states[self.state][0]()
