import sys
from primitives import PrimitiveWord
from vmbackend import VMBackEnd

b = VMBackEnd()
b.compileAllocate(2)
b.compileLiteral(42)
b.compileLiteral(-2)
b.compileCall(514)
w = b.getHere()
b.compileBranch(True)
b.setBranchTarget(w,128)
b.compilePrimitive(4)
#b.compilePrimitive(27)
ph = b.compileHeader("increment",123)
