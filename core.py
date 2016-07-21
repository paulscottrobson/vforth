#
#	This script creates two files for the primitive words listed below ; one is the Forth code declaring the
#	compilation word  and creating the actual execution word itself.
#
#	So for example for |dup we create a word which compiles the opcode and , when it executes
#	And then create a definition dup where this word is called. Remember, EVERYTHING is executed, some
#	words compile as a side effect.
#
def deComment(s):
	s = s.replace(">r","toRStack").replace("r>","fromRStack")
	s = s.replace("@","Read").replace("!","store")
	s = s.replace("<","Less").replace(">","Greater").replace("=","Equals")
	s = s.replace("+","Add").replace("-","Sub").replace("*","Mul").replace("/","Div")
	s = s.replace(";","Semi")

	return s[0].upper()+s[1:]

primitives = """

@ ! C@ C! +!  															## memory access primitives

0< 0= 0> 0- NOT 1+ 1- 2* 2/ 											## unary operators

+ - * / AND OR XOR 														## binary operators

R> >R DUP DROP SWAP ROT OVER PICK 										## stack manipulation

; 																		## return compiler

""".split("\n")

primitives = [x if x.find("##") < 0 else x[:x.find("##")] for x in primitives]				# remove comments
primitives = [x.strip().replace("\t"," ") for x in primitives]								# tabs in space.
primitives = " ".join(primitives).strip().lower()											# one long string with whitespaces

prInfo = []
n = 0
for word in primitives.split(" "):
	if word != "":
		p = { "opcode":n, "forth":word, "label":deComment(word) }
		prInfo.append(p)
		n = n + 1
#
#	tribar is a definition, basically red. |x is a compiled word (green) and x is an immediate word 
#	which would be in yellow.
#
#	| works for numbers, so 23 pushes 23 on the stack and |23 compiles .LIT 23
#
# 	the first lot are (for example) ||| |dup |23 |, |;  these define words that compile the code to execute the word when executed
#	creates a definition |dup compiles code to push 23 on the stack, compiles code to compile tos as a word, compiles a return.
#
#	the second are (for example) ||| dup |dup |; these define words which actually execute the word.
#	creates a definition dup, compiles the code that does a dup (e.g. 23 ,) by running |dup, compiles a return.
#
#	normally you just define the word, so you might do ||| increment 1 + ; you do not need to define |increment it
#	is assumed to involve compiling a threaded call to increment if it is not present (?)
#
h = open("corecompilers.4th","w")
h.write("// Automatically generated\n")
for p in prInfo:
	h.write("||| |{0} |{1} |, |;\n".format(p["forth"],p["opcode"]))						# the words that compile |DUP.
for p in prInfo:
	h.write("||| {0} |{0} |;\n".format(p["forth"],p["opcode"]))							# the words that execute DUP.
h.close()

h = open("coredefinitions.h","w")
h.write("// Automatically generated\n")

for p in prInfo:
	h.write("#define OP_{0:12} ({1})\n".format(p["label"],p["opcode"]))

pList = ['"'+x["forth"]+'"' for x in prInfo]
h.write("#ifdef INCLUDE_PRIMITIVE_TEXT\n")
h.write("static const char *_primitives[] = { "+",".join(pList)+"};\n");
h.write("#endif")
h.close()