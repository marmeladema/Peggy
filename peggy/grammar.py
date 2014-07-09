class Grammar:
	def __init__(self):
		self.rules = {}
		
	def addRule(self, rule):
		rule.grammar = self
		self.rules[rule.name] = rule
	
	def getRule(self, name):
		return self.rules[name]
	
	def optimize(self):
		for name in self.rules:
			self.rules[name].optimize()

	def finalize(self):
		for name in self.rules:
			self.rules[name].finalize()