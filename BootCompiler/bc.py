
###############################################################################################################################################################
#																Information on Primitives
###############################################################################################################################################################
class PrimitiveStore:
	def __init__(self):
		primitives = """
			@	! 	c@	c! 	+!	+ 	- 	* 	/ 	and	or	xor
			not  	0= 	0>	0<	0-	1+	1- 	2* 	2/	dup	drop	
			swap	rot	over	;	r> 	>r	#0if
			""".lower().replace("\t"," ").replace("\n","")														# list of all primitives
		self.primitiveList = [x for x in primitives.split() if x != ""]											# convert to a list
		self.primitiveFind = {}																					# create the hash look up.
		for i in range(0,len(self.primitiveList)):
			self.primitiveFind[self.primitiveList[i]] = i
	def getPrimitiveID(self,name):																				# simple functions to extract data
		return self.primitiveFind[name] if name in self.primitiveFind else None
	def getPrimitiveName(self,id):
		return self.primitiveList[id] if id >= 0 and id < len(self.primitiveList) else None

###############################################################################################################################################################
#																		Base class for Backends
###############################################################################################################################################################

class BackEndBaseClass:
	def __init__(self):
		self.code = []																							# code words.
		self.address = 0																						# current address.
		self.prInfo = PrimitiveStore()																			# probably useful :)
		self.compileWord(0,"(Total size of code)")
		self.compileWord(0,"(Head of dictionary linked list)")

	def getAddress(self):
		return self.address

	def compileWord(self,w,desc = ""):
		print("{0:08x}:{1:08x}     {2}".format(self.address,w,desc))
		self.code.append(w)
		self.address += 4
		self.code[0] = self.address

	def generateHeader(self,name):
		currentHeader = self.code[1]																			# previous head
		self.code[1] = self.getAddress()																		# new head is here.
		offset = self.getAddress() - currentHeader if currentHeader > 0 else 0 									# offset back to dictionary head.
		self.compileWord(offset,"link to previous")
		currentWord = 0 																						# constructing word.
		letters = ""
		for c in name:
			if (currentWord & 0xFF000000) != 0:																	# No space ?
				self.compileWord(currentWord | 0x80000000,"dict:"+letters)										# output current word
				currentWord = 0
				letters = ""
			currentWord = (currentWord << 8) + ord(c)															# shift char in
			letters += c
		self.compileWord(currentWord,"dict:"+letters)

	def generateLiteral(self,number):
		assert False,"generateLiteral missing"
	def generateCall(self,address):
		assert False,"generateCall missing"
	def generatePrimitive(self,prID):
		assert False,"generatePrimitive missing"

###############################################################################################################################################################
#																	Back end class for virtual machine
###############################################################################################################################################################

class VMBackEnd(BackEndBaseClass):
	def generateLiteral(self,number):
		n = number & 0xFFFFFFFF 																				# convert to 32 bit unsigned int.
		top2 = n >> 30 																							# the top two digits must be 00 or 11
		assert top2 == 0 or top2 == 3,"Cannot generate literal constant out of range"
		self.compileWord(n & 0x7FFFFFFF,"Push {0}".format(number))												
	def generateCall(self,address):
		offset = address - (self.getAddress() + 4)																# work out offset.
		assert abs(offset) <= 0x0FFFFFFF,"Call out of range"
		if offset >= 0:
			self.compileWord(0x80000000+offset,"Call {0:0x}".format(address))
		else:
			self.compileWord(0x90000000-offset,"Call {0:0x}".format(address))
	def generatePrimitive(self,prID):
		name = self.prInfo.getPrimitiveName(prID)																# get name to validate it
		assert name is not None,"Unknown primitive ID:"+str(word)
		self.compileWord(0xF0000000+prID,name) 																	# compile primitive, very simple.

vb = VMBackEnd()
vb.generateLiteral(42)
vb.generateLiteral(-2)
vb.generateCall(0)
vb.generateCall(42)
vb.generatePrimitive(0)
vb.generatePrimitive(27)
vb.generateHeader("dup")
vb.generateHeader("increment")

print(vb.code[:2])
