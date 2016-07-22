# **************************************************************************************************************************
# **************************************************************************************************************************
#
#											  FORTH VM BACKEND CLASSES
#
# **************************************************************************************************************************
# **************************************************************************************************************************

from primitives import PrimitiveWord

# **************************************************************************************************************************
#													Back End for VM
# **************************************************************************************************************************

class VMBackEnd:
	def __init__(self, base = 0):
		self.base = base 																						# code generated offset from here
		self.pointer = self.base 																				# current pointer
		self.code = [] 																							# code words
		self.isLastReturn = True 																				# true if last was return.
		self.primitives = PrimitiveWord()																		# primitive information
		self.opcodeBR = self.primitives.isPrimitive("$br")|0x80000000
		self.opcode0BR = self.primitives.isPrimitive("$0br")|0x80000000
		self.opcodeReturn = self.primitives.isPrimitive(";")|0x80000000
	def getHere(self):
		return self.pointer																						# current pointer

	def getWordSize(self):
		return 4																								# word size.

	def compileHeader(self,name,previousHeader):
		branchAddr = self.getHere()																				# where the branch over header for fall through is
		if not self.isLastReturn:																				# do we need it.
			self.compileBranch(False)																			# compile branch w/o address
		newHeader = self.getHere()																				# the new header pointer
		self._compileWord(newHeader-previousHeader if previousHeader > 0 else 0)								# address of previous relative backwards if any.
		self.compileIdentifier(name)
		if not self.isLastReturn:																				# patch the branch over address
			self.setBranchTarget(branchAddr,self.getHere())
		self.isLastReturn = False																				# not previously a return now.
		return newHeader																						# return next in chain.

	def compileIdentifier(self,name):
		currentWord = 0x0 																						# make word up.
		for c in name:
			if (currentWord & 0xFF000000) != 0:																	# if current word is full.
				self._compileWord(currentWord | 0x80000000)														# compile with bit 31 set.
				currentWord = 0																					# new word
			currentWord = (currentWord << 8) | ord(c)															# add current character code in.
		self._compileWord(currentWord)																			# compile the final word.

	def compileAllocate(self,count):
		for i in range(0,count):																				# compile that many 0x00
			self._compileWord(0x0)
		self.isLastReturn = False

	def compileLiteral(self,literal): 		
		literal = literal & 0xFFFFFFFF 																			# make 32 bit value
		topBits = literal >> 30 														 						# look at top 2 bits.
		assert topBits == 0 or topBits == 3,"Literal out of range" 												# must be 00x or 11x else can't sign extend
		self._compileWord(literal & 0x7FFFFFFF)																	# compile code for literal in.
		self.isLastReturn = False

	def compileCall(self,address): 		
		offset = address-(self.getHere()+4)
		if offset < 0:
			self._compileWord(0x90000000 - offset)
		else:
			self._compileWord(0xA0000000 + offset)
		self.isLastReturn = False

	def compilePrimitive(self,primitive):	
		assert self.primitives.getPrimitive(primitive) is not None,"Unknown primitive "+str(primitive)			# check legit
		primitive |= 0x80000000
		self._compileWord(primitive)																			# compile primitive
		self.isLastReturn = (primitive == self.opcodeReturn)													# record if last was ;

	def compileBranch(self,isConditional):	
		self._compileWord(self.opcode0BR if isConditional else self.opcodeBR)									# compile $0br or $br
		self._compileWord(0)																					# no address yet
		self.isLastReturn = False

	def setBranchTarget(self,branchAddress,targetAddress):
		addr = (branchAddress - self.base)/4																	# convert to index in word array
		op = self.code[addr] 																					# check op is $0BR or $BR
		assert op == self.opcode0BR or op == self.opcodeBR
		self.code[addr+1] = (targetAddress - (branchAddress + 8)) & 0xFFFFFFFF									# update target address
		print("{0:08x} {1:08x} Rel Patch {2:08x}".format(branchAddress+4,self.code[addr+1],targetAddress))

	def _compileWord(self,word):
		print("{0:08x} {1:08x} {2}".format(self.pointer,word,self.decode(word)))								# output word
		self.code.append(word)																					# add to vector
		self.pointer += self.getWordSize()																		# update pointer

	def decode(self,word):
		rv = "?"																								# lazy convert back to mnemonic code.
		if (word & 0x80000000) == 0:
			if (word & 0x40000000) == 0:
				word = word & 0x3FFFFFFF
			else:
				word = (word & 0x7FFFFFFF) - 0x80000000
			rv = str(word)
		elif (word >> 28) == 8:
			rv = self.primitives.getPrimitive(word & 0xFF)
		else:
			offset = word & 0x0FFFFFFF
			if (word >> 28) == 9:
				offset = -offset
			rv = "call {0:08x}".format(offset)
		return rv
