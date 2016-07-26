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

ps = PrimitiveStore()
ps.generateHeaderFile()