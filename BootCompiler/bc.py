import re,sys

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

	def compileWord(self,word,comment,address = None):
		address = self.pointer if address is None else address 							# convert address.
		if address == self.pointer:														# allocate word if required
			self.code.append(None)
		self.code[address >> 2] = word 													# save in memory
		if self.isListing:
			print("{0:08x} {1:08x}    {2}".format(address,word,comment))
		if address == self.pointer:														# advance one word size
			self.pointer += 4
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

###############################################################################################################################################################
#												Back End for Virtual Machine
###############################################################################################################################################################

class VMBackEnd(BackEndBaseClass):
	pass

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

ws = WordStream(["demo.c4"])
be = BackEndBaseClass()
be.createDefinition("dup")
be.createDefinition("forget")
be.createDefinition("__main")
print(be.code)