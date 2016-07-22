import sys
from primitives import PrimitiveWord
from vmbackend import VMBackEnd

b = VMBackEnd(256)
b.compileAllocate(2)
b.compileLiteral(42)
b.compileLiteral(-2)
b.compileCall(514)
b.compileCall(256)
b.compilePrimitive(4)
w = b.getHere()
b.compileBranch(True)
b.setBranchTarget(w,w)
b.compilePrimitive(27)
ph = 256
ph = b.compileHeader("increment",ph)
