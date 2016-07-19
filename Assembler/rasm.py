# **************************************************************************************************************************
#
#													RISC VM Assembler.
#
# **************************************************************************************************************************

class AssemblerError(Exception):
	pass

# **************************************************************************************************************************
#												Stores a collection of code
# **************************************************************************************************************************

class CodeBucket:
	def __init__(self):
		self.code = [ None ] * 16 														# code starts at offset 64
		self.pointer = 64 																# this is the code pointer.

	def getPointer(self):
		return self.pointer

	def write(self,value):
		self.code.append(value)
		print("{0:06x} {1:08x}".format(self.pointer,value))
		self.pointer += 4

# **************************************************************************************************************************
#												Stores a collection of labels
# **************************************************************************************************************************

class  LabelBucket:
	def __init__(self):
		self.clearBucket()																# clear it.

	def define(self,labelNumber,address):
		if labelNumber < 0 or labelNumber > 9:											# validation
			raise AssemblerError("Labels are 0-9 only. Factor your code")
		if address % 4 != 0:
			raise AssemblerError("Address must be on word boundary")
		if self.addresses[labelNumber] is not None:
			raise AssemblerError("Label duplicated.")
		self.addresses[labelNumber] = address 											# assign it.

	def clearBucket(self):
		self.addresses = [ None ] * 10 													# the 10 addresses for labels 0-9
		self.references = [ [] ] * 10 													# addresses referred to.

	def backPatch(self):							
		pass 

# **************************************************************************************************************************
#															Assembler
# **************************************************************************************************************************

class RISCAssembler:
	def __init__(self):
		self.code = CodeBucket() 														# code goes here
		self.labels = LabelBucket() 													# labels go here
		self.definitions = {} 															# known definitions
		self.lineNumber = 1
		self.previousDeclaration = 0 													# last declaration for FORTH stack.
		self.conditions = [ "xx","z","lt","le","xx","nz","ge","gt"]						# condition codes.

	def assemble(self,sourceList):
		for l in sourceList:															# for each line.
			l = l if l.find("//") < 0 else l[:l.find("//")]								# remove comments
			l = l.replace("\t"," ").strip().lower()										# tidy tabs and strip, make L/C
			if l != "":																	# assemble non blank lines.
				self.assembleLine(l)
			self.lineNumber += 1 														# bump line number.

	def assembleLine(self,l):
		if l[:3] == "ret":																# handle RET 
			l = "mov"+l[3:]+" r15,r14"													# becomes mov r15,r14
		self.line = l 																	# save line to grab stuff.

		if l[0] == "+":																	# is it an allocation +<nnn>
			for i in range(0,int(l[1:].strip())):										# pad out with that many words
				self.code.write(0)

		if l[0] == ".":																	# label definition.
			self.labels.define(int(l[1:].strip()),self.code.getPointer())

		if l[0] == ":":																	# code block definition
			self.labels.backPatch()														# backpatch labels
			self.labels.clearBucket()													# and clear the labels.
			defStart = self.code.getPointer()
			if l[1:] in self.definitions:
				raise AssemblerError(l[1:]+" has been defined twice")
			if self.previousDeclaration == 0:											# first dec , link field is 0
				self.code.write(0xC0000000)												
			else:																		# second dec, link field is offset.
				self.code.write(0xC0000000+(self.code.getPointer()-self.previousDeclaration)) 				
			self.writeDefinitionRecord(l[1:])											# write out the definition record.
			self.previousDeclaration = defStart 										# update address previous declaration.
			self.definitions[l[1:]] = self.code.getPointer() 							# save code address for this word.

		if l[0] == 'b':																	# B or BL
			word = 0x80000000 															# branch is bit 31.
			self.line = self.line[1:] 													# skip B
			if self.line != "" and self.line[0] == 'l':									# is it BL ?
				word = word | 0x08000000 												# set bit 27 the link bit.				
				self.line = self.line[1:]
			word = word | self.getConditionCode() 										# add in condition code if any
			print(self.line)
			self.code.write(word)

	def writeDefinitionRecord(self,name):
		n = (len(name)+3) / 4 															# how many words to write out.
		for section in range(0,n):
			chars = name[section*4:section*4+4]											# get the chunk out.
			word = 0
			for c in chars:																# build the word up out of chars
				word = (word << 7) | (ord(c) & 0x7F)
			word = word | 0x40000000 													# set condition to never.
			if section == n-1: 															# mark end with bit 31.
				word = word | 0x80000000
			self.code.write(word)														# write that word out.

	def getConditionCode(self):
		ccode = 0 																		# condition code defaults to always (0)
		if self.line != "" and self.line[0] != ' ':										# is there a code ?
			for p in range(1,8):
				if self.line[:len(self.conditions[p])] == self.conditions[p]:			# found a match
					ccode = p  															# remember it
					self.line = self.line[len(self.conditions[p]):] 					# remove it
					break 																# break loop
		self.line = self.line.strip()													# remove leading spaces.
		return ccode << 28 																# shift into correct position

ra = RISCAssembler() 																	# create risc assembler
src = """
	+2 						// Skip 8 words
	:at

	:freddie
	.2
	blz at
	bge  .2
	bl 	.2
""".split("\n")
ra.assemble(src)
print(ra.definitions)
