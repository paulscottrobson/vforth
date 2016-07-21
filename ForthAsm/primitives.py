# **************************************************************************************************************************
# **************************************************************************************************************************
#
#												PRIMITIVE WORD CLASSES
#
# **************************************************************************************************************************
# **************************************************************************************************************************

# **************************************************************************************************************************
#									Manages lists of primitive words and conversion to from.
# **************************************************************************************************************************

class PrimitiveWord:
	def __init__(self):																							# list of primitive words
		primitives = """																					
				@	! 	c@	c! 	+!	+ 	- 	* 	/ 	and	or	xor
				not  	0= 	0>	0<	0-	1+	1- 	2* 	2/	dup	drop	
				swap	rot	over	pick 	;	r> 	>r	, 
				$br 	$0br  $lit
				"""
		self.primitives = {}																					# hash primitives -> opcode
		self.primitiveList = [] 																				# vector opcode -> primitives
		primitives = primitives.replace("\n"," ").replace("\t"," ").lower()										# preprocess list
		opcodeID = 0																							# create hash and vector
		for word in primitives.split(" "):
			if word != "":
				self.primitives[word] = opcodeID
				self.primitiveList.append(word)
				opcodeID += 1
		self.createIncludeFile()																				# create C file

	def getPrimitive(self,id):
		return self.primitiveList[id] if id < len(self.primitiveList) else None 								# id to primitive if exists

	def isPrimitive(self,word):
		return self.primitives[word] if word in self.primitives else None 										# primitive to id if exists

	def createIncludeFile(self):
		h = open("__primitives.h","w")			
		for i in range(0,len(self.primitiveList)):																# write out each opcode as a #define
			h.write("#define OP_{0} ({1})\n".format(self.expandControls(self.primitiveList[i]),i))
		pList = ",".join(['"'+x+'"' for x in self.primitiveList])
		h.write("#ifdef INCLUDE_PRIMITIVE_STATIC\n") 
		h.write("static const char *_primitives[] = { "+pList+"};\n")											# static char * array of names
		h.write("#endif\n")
		h.close()

	def expandControls(self,word):
		word = word.upper().replace(">R","_TO_R_").replace("R>","_FROM_R_")										# replace controls with alphanumerics
		word = word.replace("@","_READ_").replace("!","_WRITE_").replace("+","_ADD").replace("-","_SUB_")
		word = word.replace("*","_MUL_").replace("/","_DIV_").replace("=","_EQUALS_")
		word = word.replace(">","_GREATER_").replace("<","_LESS_").replace(";","_SEMICOLON_")
		word = word.replace("$","_DOLLAR_").replace(",","_COMMA_")
		while word.find("__") > 0:																				# remove __, leading and trailing _
			word = word.replace("__","_")
		if word[0] == "_":
			word = word[1:]
		if word[-1] == "_":
			word = word[:-1]
		return word.upper()																						# and capitalises.

