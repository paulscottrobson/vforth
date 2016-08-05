import re,sys

###############################################################################################################################################################
#												Exception Handler
###############################################################################################################################################################

class ForthException(Exception):
	def __init__(self,msg):
		print(msg)
		sys.exit(1)

###############################################################################################################################################################
#																Information on Primitives
###############################################################################################################################################################

class PrimitiveStore:
	def __init__(self):
		primitives = """
			@	! 	c@	c! 	+!	+ 	- 	* 	/ 	and	or	xor
			not  	0= 	0>	0<	0-	1+	1- 	2* 	2/	dup	drop	
			swap	rot	over	;	r> 	>r  $hwio
			""".lower().replace("\t"," ").replace("\n","")														# list of all primitives
		self.primitiveList = [x for x in primitives.split() if x != ""]											# convert to a list
		self.primitiveFind = {}																					# create the hash look up.
		for i in range(0,len(self.primitiveList)):
			self.primitiveFind[self.primitiveList[i]] = i
		self.generateHeaderFile()																				# update header file.

	def getPrimitiveID(self,name):																				# simple functions to extract data
		return self.primitiveFind[name] if name in self.primitiveFind else None

	def getPrimitiveName(self,id):
		return self.primitiveList[id] if id >= 0 and id < len(self.primitiveList) else None

	def getPrimitiveList(self):
		return self.primitiveList

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
#												  Backend parent class
###############################################################################################################################################################

class BackEndBaseClass:
	def __init__(self,listing = True):
		self.isListing = listing 														# save if listing
		self.pointer = 0 																# pointer into base class
		self.code = [] 																	# no code.
		self.prInfo = PrimitiveStore()													# primitive info
		self.compileWord(0,"(head of dictionary)")										# word headers
		self.compileWord(0,"(next free memory)")
		self.compileWord(0,"(offset to __main)")

	def getAddress(self):
		return self.pointer 

	def compileWord(self,word,comment,address = None):
		address = self.pointer if address is None else address 							# convert address.
		if address == self.pointer:														# allocate word if required
			self.code.append(None)
		self.code[address >> 2] = word 													# save in memory
		if self.isListing:
			print("{0:08x} {1:08x}    {2}".format(address,word,comment))
		if address == self.pointer:														# advance one word size
			self.pointer += self.getWordSize()
			if len(self.code) > 1:
				self.code[1] = self.pointer

	def createDefinition(self,definingWord):
		offset = 0 if self.code[0] == 0 else self.pointer - self.code[0]				# work out offset
		headerAddress = self.pointer 													# remember new head
		self.compileWord(offset,"link to {0:08x}".format(self.code[0]))					# assemble reference back.
		self.code[0] = headerAddress 													# maintain link.
		wordCount = (len(definingWord)+3)/4 											# how many defining words
		for i in range(0,wordCount):													# for each word
			words = 0 																	# build up the word from char data
			for ch in definingWord[i*4:i*4+4]:
				words = (words << 8) | ord(ch)
			if i < wordCount-1:															# the last one has bit 31 clear.
				words |= 0x80000000														# others have bit 31 set.
			self.compileWord(words,'"'+definingWord[i*4:i*4+4]+'"')						# define it.
		if definingWord == "__main":													# found __main
			self.code[2] = self.pointer 

	def writeBinary(self,fileName):
		h = open(fileName,"wb")
		for b in self.code:
			h.write(chr((b >> 0) & 0xFF))
			h.write(chr((b >> 8) & 0xFF))
			h.write(chr((b >> 16) & 0xFF))
			h.write(chr((b >> 24) & 0xFF))
		h.close()

	def createPrimitiveDefinitions(self,dictionary):												
		for word in self.prInfo.getPrimitiveList():										# create execute and compile versions.
			self.createPrimitive(word,dictionary)

	def createPrimitive(self,word,dictionary):
		reject = word == ">r" or word == "r>" or word == ";"							# these use return stack, no execution version
		if not reject:																	
			self.createDefinition(word)													# simple execution word.
			self.generatePrimitive(word)
			self.generatePrimitive(";")

		self.createDefinition(word+"|")													# word to compile primitives
		self.generateConstant(self.prInfo.getPrimitiveID(word))							# get primitive word
		assert "," in dictionary,"The code does not include a definition for ,"
		self.generateCall(dictionary[","],",")											# call word compile.
		self.generatePrimitive(";")													

###############################################################################################################################################################
#												Back End for Virtual Machine
###############################################################################################################################################################

class VMBackEnd(BackEndBaseClass):

	def getWordSize(self):
		return 4

	def generateConstant(self,constant):
		uconstant = constant & 0xFFFFFFFF 												# 32 bit unsigned value.
		upperBits = uconstant >> 30 													# check bits 30 and 31 are same, e.g. can sign extend
		if upperBits == 1 or upperBits == 2:
			raise ForthException("Cannot compile constant {0:08x}".format(constant))
		self.compileWord(uconstant & 0x7FFFFFFF,str(constant))

	def generatePrimitive(self,word):
		primitiveID = self.prInfo.getPrimitiveID(word)									# get the ID
		self.compileWord(primitiveID|0xF0000000,word)									# compile it

	def generateCall(self,target,wordName):
		offset = target - (self.getAddress()+4)											# offset.
		self.compileWord(0xC0000000 | (offset & 0x0FFFFFFF),"call "+wordName)			# compile relative call

	def generateBackwardBranch(self,target):
		offset = target - (self.getAddress()+4)											# offset.
		self.compileWord(0xD0000000 | (offset & 0x0FFFFFFF),"br {0:08x}".format(target)) # compile relative branch

	def generateData(self,data):
		self.compileWord(data & 0xFFFFFFFF,"data "+str(data))							# raw data

	def generateForwardBranchIfZero(self):
		self.compileWord(0xE0000000,"bz <undefined>")									# incomplete forward branch

	def patchForwardBranchIfZero(self,target):									
																						# patch up forward branch.
		self.compileWord(0xE0000000+self.getAddress()-(target+4),"bz {0:08x}".format(self.getAddress(),target),target)

###############################################################################################################################################################
#														Word source
###############################################################################################################################################################

class WordStream:
	def __init__(self,fileList = None):
		if fileList is None:															# load in from forth.make
			fileList = [x.strip() for x in open("vforth.make").readlines() if x.strip() != ""]
		self.words = []
		for f in fileList:																# for each file
			src = open(f).readlines()													# read in the source
			src = [x if x.find("//") < 0 else x[:x.find("//")] for x in src]			# remove comments
			src = " ".join(src).replace("\t"," ").replace("\n"," ").lower()				# one long string, no tab/return
			for w in src.split():														# split into words
				if w != "":																# append non null
					self.words.append(w)
		self.pointer = 0																# index into word stream

	def endOfStream(self):																# check end of stream
		return self.pointer >= len(self.words)

	def get(self):																		# get next word, "" if none.
		w = "" if self.endOfStream() else self.words[self.pointer]
		self.pointer += 1
		return w

###############################################################################################################################################################
#																	Compiler
###############################################################################################################################################################

class Compiler:
	def __init__(self,wordStream,backEnd):

		self.wordStream = wordStream 													# remember the word stream
		self.backEnd = backEnd 															# remember the backend.
		self.currentEntry = None 														# current entry for tail recursion
		self.vocabulary = {}															# defined words
		self.prInfo = PrimitiveStore() 													# primitive word information
		self.openIf = None 																# address of open if

		while not self.wordStream.endOfStream():										# keep compiling until complete.
			word = self.wordStream.get()												# get next word.

			if word == ':':																# word definition
				name = self.wordStream.get()											# get word to define.
				if name == "":
					raise ForthException("Missing word name in definition")
				self.backEnd.createDefinition(name)										# create the definition
				self.currentEntry = self.backEnd.getAddress() 							# store current address.
				self.vocabulary[name] = self.backEnd.getAddress() 						# store call address in the vocabulary list.

			elif self.prInfo.getPrimitiveID(word) is not None:							# is it a primitive word.
				self.backEnd.generatePrimitive(word)									# generate code for that primitive.
				if word == ";": 														# if ; close any open if..then structures.
					self.closeThen()

			elif re.match("^\\-?\\d+$",word) is not None:								# check for decimal number
				self.backEnd.generateConstant(int(word))

			elif re.match("^\\$[0-9a-f]+$",word) is not None:							# check for hexadecimal number
				self.backEnd.generateConstant(int(word[1:],16))

			elif word == "wordsize":													# push word size
				self.backEnd.generateConstant(self.backEnd.getWordSize())

			elif word == "alloc":
				count = self.wordStream.get()											# how many to do.
				if re.match("^\\d+$",count) is None:
					raise ForthException("Cannot alloc "+count)
				for i in range(0,int(count)):
					self.backEnd.generateData(0)

			elif word == "if":															# if keyword.
				if self.openIf is not None:
					raise ForthException("Cannot nest if..then")
				self.openIf = self.backEnd.getAddress() 								# create address
				self.backEnd.generateForwardBranchIfZero()								# create blank forward blank

			elif word == "then":														# then closes if.
				self.closeThen()

			elif word == "self":
				if self.currentEntry is None:
					raise ForthException("No current definition")
				self.backEnd.generateBackwardBranch(self.currentEntry)

			else:
				if word not in self.vocabulary:											# check word is known
					raise ForthException("Word '"+word+"' is not known.")
				self.backEnd.generateCall(self.vocabulary[word],word)					# generate the call

		self.backEnd.createPrimitiveDefinitions(self.vocabulary)						# create the primitive words.
		self.backEnd.writeBinary("a.out")												# output the results.

	def closeThen(self):
		if self.openIf is not None:														# open If ?
			self.backEnd.patchForwardBranchIfZero(self.openIf)
			self.openIf = None

ws = WordStream()
be = VMBackEnd(False)
Compiler(ws,be)