import re,sys

###############################################################################################################################################################
#																Information on Primitives
###############################################################################################################################################################

class PrimitiveStore:
	def __init__(self):
		primitives = """
			@	! 	c@	c! 	+!	+ 	- 	* 	/ 	and	or	xor
			not  	0= 	0>	0<	0-	1+	1- 	2* 	2/	dup	drop	
			swap	rot	over	;	r> 	>r	#0if $hwio
			""".lower().replace("\t"," ").replace("\n","")														# list of all primitives
		self.primitiveList = [x for x in primitives.split() if x != ""]											# convert to a list
		self.primitiveFind = {}																					# create the hash look up.
		for i in range(0,len(self.primitiveList)):
			self.primitiveFind[self.primitiveList[i]] = i
	def getPrimitiveID(self,name):																				# simple functions to extract data
		return self.primitiveFind[name] if name in self.primitiveFind else None
	def getPrimitiveName(self,id):
		return self.primitiveList[id] if id >= 0 and id < len(self.primitiveList) else None
	def generateHeaderFile(self):
		h = open("__primitives.h","w")
		h.write("#define COUNT_PRIMITIVES ({0})\n".format(len(self.primitiveList)))
		for i in range(0,len(self.primitiveList)):
			h.write("#define OP_{1} ({0})\n".format(i,self.identProcess(self.primitiveList[i])))
		h.write("#ifdef PRIMITIVE_STATIC\n")
		p = ",".join(['"'+x+'"' for x in self.primitiveList])
		h.write("static const char *_primitives[] = {"+p+"};\n")
		h.write("#endif\n")
		h.close()

	def identProcess(self,word):
		word = word.replace(";","_semicolon_").replace("r>","_from_r_").replace(">r","_to_r_")					# convert forth word name to legit C identifier
		word = word.replace("@","_read_").replace("!","_store_").replace("+","_add_").replace("-","_sub_")
		word = word.replace("*","_mul_").replace("/","_div_").replace("=","_equals_")
		word = word.replace(">","_greater_").replace("<","_less_").replace("#","_notequals_")
		word = word.replace("$","_dollar_")
		while word.find("__") >= 0:
			word = word.replace("__","_")
		if word[0] == '_':
			word = word[1:]
		if word[-1] == "_":
			word = word[:-1]
		return word.upper()

###############################################################################################################################################################
#																		Base class for Backends
###############################################################################################################################################################

class BackEndBaseClass:
	def __init__(self,display = False):
		self.code = []																							# code words.
		self.address = 0																						# current address.
		self.prInfo = PrimitiveStore()																			# probably useful :)
		self.displayListing = display 																			# listing on ?
		self.localDictionary = {} 																				# local dictionary copy.
		self.compileWord(0,"(Total size of code)")																# header words
		self.compileWord(0,"(Head of dictionary linked list)")
		self.compileWord(0,"(Offset of first word)")

	def getAddress(self):
		return self.address
	def isListing(self):
		return self.displayListing

	def compileWord(self,w,desc = "",suppress = False):
		mask = (1 << (self.getWordSize()*8))-1																	# mask for values.
		if self.isListing() and not suppress:
			fmt = "0{0}x".format(self.getWordSize()*2)															# how to format values
			fmtStr = "{0:"+fmt+"} {1:"+fmt+"}    {2}"															# create format string
			print(fmtStr.format(self.address,w & mask,desc))													# display it.
		assert (w & mask) == w,"Data overflow in"
		self.code.append(w)
		self.address += self.getWordSize()
		self.code[0] = self.address

	def write(self,fileName,incFileName):
		h = open(fileName,"wb")
		codeList = []
		for c in self.code:
			for b in range(0,self.getWordSize()):
				h.write(chr(c & 255))
				codeList.append("0x{0:x}".format(c & 255))
				c = c >> 8
		h.close()
		h2 = open(incFileName,"w")
		h2.write(",".join(codeList))
		h2.close()

	def generateHeader(self,name):
		currentHeader = self.code[1]																			# previous head
		self.code[1] = self.getAddress()																		# new head is here.
		offset = self.getAddress() - currentHeader if currentHeader > 0 else 0 									# offset back to dictionary head.
		self.compileWord(offset,"link to previous")
		currentWord = 0 																						# constructing word.
		letters = ""
		testMask = 0xFF << (self.getWordSize()*8-8)
		for c in name:
			if (currentWord & testMask) != 0:																	# No space ?
				self.compileWord(currentWord | 1 << (self.getWordSize()*8-1),"dict:"+letters)					# output current word
				currentWord = 0
				letters = ""
			currentWord = (currentWord << 8) + ord(c)															# shift char in
			letters += c
		self.compileWord(currentWord,"dict:"+letters)
		self.localDictionary[name] = self.getAddress()															# save execution adddress
		if name == "__main":
			self.code[2] = self.getAddress()
		self.loopAddress = self.getAddress() 																	# the loop address for this.

	def findDictionaryEntry(self,name):
		return self.localDictionary[name] if name in self.localDictionary else None
	def getCurrentDefinition(self):
		return self.loopAddress
	def getWord(self,address):
		return self.code[address/self.getWordSize()]

	def getWordSize(self):
		assert False,"getWordSize missing"
	def generateLiteral(self,number):
		assert False,"generateLiteral missing"
	def generateCall(self,address):
		assert False,"generateCall missing"
	def generatePrimitive(self,prID):
		assert False,"generatePrimitive missing"
	def generateLoop(self):
		assert False,"generateLoop missing"


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
		offset = address - (self.getAddress() + self.getWordSize())												# work out offset.
		assert abs(offset) <= 0x0FFFFFFF,"Call out of range"
		if offset >= 0:
			self.compileWord(0x80000000+offset,"Call {0:0x}".format(address))
		else:
			self.compileWord(0x90000000-offset,"Call {0:0x}".format(address))
	def generatePrimitive(self,prID):
		name = self.prInfo.getPrimitiveName(prID)																# get name to validate it
		assert name is not None,"Unknown primitive ID:"+str(name)
		self.compileWord(0xF0000000+prID,name) 																	# compile primitive, very simple.
	def generateLoop(self):
		offset = self.getAddress() + self.getWordSize() - self.getCurrentDefinition();							# how far back to go
		self.compileWord(0xA0000000+offset,"Restart")
	def getWordSize(self):
		return 4

###############################################################################################################################################################
#																			Simple Compiler
###############################################################################################################################################################

class Compiler:
	def __init__(self,backEnd):
		self.backEnd = backEnd 																					# save compiler backend
		self.prInfo = PrimitiveStore()																			# primitive information
		self.prInfo.generateHeaderFile() 																		# generate include file for primitives

	def compileFile(self,fileName):
		self.compileText(open(fileName).readlines())

	def compileText(self,source):
		source = [x if x.find("//") < 0 else x[:x.find("//")] for x in source]									# remove comments
		source = [x.replace("\t"," ").replace("\n"," ") for x in source]										# remove tabs and any newlines
		source = [x.strip().lower() for x in source if x.strip() != ""]											# strip spaces, remove blank lines.
		for s in source:
			if self.backEnd.isListing():
				print("\nCode :: "+s)
			for w in s.split(" "):																				# split into bits
				if w != "":																						# ignore empty lines
					self.compileWord(w)

	def compileWord(self,word):
		prID = self.prInfo.getPrimitiveID(word) 																# is word a primitive ?
		if prID is not None:																					
			self.backEnd.generatePrimitive(prID)
		elif word == "$wordsize":																				# push wordsize on stack
			self.backEnd.generateLiteral(self.backEnd.getWordSize())
		elif word[:3] == "+++":																					# allocate working space.
			for i in range(0,int(word[3:])):
				self.backEnd.compileWord(0,"",True)
		elif word == "$loop":
			self.backEnd.generateLoop()
		elif word[0] == ':':																					# definition header
			assert len(word) > 1,"No definition word"
			self.backEnd.generateHeader(word[1:])
		elif re.match("^\\-?\\d+$",word):																		# is it a decimal word ?
			self.backEnd.generateLiteral(int(word))
		elif re.match("^\\$[0-9a-f]+$",word):																	# is it a hexadecimal word ?
			self.backEnd.generateLiteral(int(word[1:],16))
		else:
			addr = self.backEnd.findDictionaryEntry(word)
			assert addr is not None,"Unknown word "+word
			self.backEnd.generateCall(addr)

backEnd = VMBackEnd(True)
cm = Compiler(backEnd)
if len(sys.argv) > 1:
	for f in sys.argv[1:]:
		cm.compileFile(f)
	backEnd.write("a.out","__boot.h")
	print(backEnd.code[:4])

# TODO: 3rd word (for main)
# TODO: hexadecimal constants &xxxxxx
