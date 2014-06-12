class Generator:
	def __init__(self):
		self.lines = []
		self.stack_depth = 0
		self.block_depth = 0

	def add(self, line, block = 0):
		self.lines.append('\t'*(self.block_depth) + line)