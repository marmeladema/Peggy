generators = {}

class Generator:
	def __init__(self):
		self.lines = []
		self.block_depth = 0
		self.resetStack()

	def add(self, line, block = 0, index=None):
		if index is None:
			self.lines.append('\t'*(self.block_depth) + line)
		else:
			self.lines.insert(index, '\t'*(self.block_depth) + line)

	def resetStack(self):
		self.stack_depth = -1
		self.max_stack_depth = -1

	def push(self):
		self.stack_depth += 1
		if self.stack_depth > self.max_stack_depth:
			self.max_stack_depth = self.stack_depth

	def pop(self):
		self.stack_depth -= 1