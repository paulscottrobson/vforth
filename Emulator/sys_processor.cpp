// *******************************************************************************************************************************
// *******************************************************************************************************************************
//
//		Name:		sys_processor.c
//		Purpose:	Processor Emulation.
//		Created:	25th July 2016
//		Author:		Paul Robson (paul@robsons.org.uk)
//
// *******************************************************************************************************************************
// *******************************************************************************************************************************

#include <stdlib.h>
#include <stdio.h>
#include "sys_processor.h"
#include "sys_debug_system.h"
#include "hardware.h"
#include "__primitives.h"

static void _CPUExecutePrimitive(BYTE8 opcode);

// *******************************************************************************************************************************
//														   Timing
// *******************************************************************************************************************************

#define FRAME_RATE		(60)														// Frames per second (60)
#define CYCLES_PER_FRAME (1000*1000)												// Cycles per frame (100k)

// *******************************************************************************************************************************
//														CPU / Memory
// *******************************************************************************************************************************

static LONG32 memory[0x40000]; 														// 256k words of memory. (1M Bytes) 00000-FFFFF
static LONG32 pctr;
static LONG32 rsp;
static LONG32 dsp;
static LONG32 cycles;
static BYTE8* bMemory = (BYTE8 *)memory;											// Access memory byte wise.

// *******************************************************************************************************************************
//															Stack
// *******************************************************************************************************************************

#define PUSHD(v) { dsp -= 4;memory[dsp >> 2] = (v); }
#define PUSHR(v) { rsp -= 4;memory[rsp >> 2] = (v); }

#define PULLD(tgt) { tgt = memory[dsp >> 2];dsp += 4; }
#define PULLR(tgt) { tgt = memory[rsp >> 2];rsp += 4; }

#define TOSD() 	memory[dsp >> 2]
#define TOSD2() memory[(dsp >> 2)+1]
#define TOSD3() memory[(dsp >> 2)+2]

#define CHECK(a) if (((a) & 3) != 0) { exit(fprintf(stderr,"Address failure %08x",a)); }

// *******************************************************************************************************************************
//														Reset the CPU
// *******************************************************************************************************************************

void CPUReset(void) {
	HWIReset();
	pctr = 0x00000;
	rsp = RST_RSP;
	dsp = RST_DSP;
	cycles = 0;
	int base = 0;																	// We can test the relocation.

	pctr = memory[base/4+2]+base;													// Get the start address
	PUSHD(base); 																	// Get the base address
}

// *******************************************************************************************************************************
//												Execute a single instruction
// *******************************************************************************************************************************

BYTE8 CPUExecuteInstruction(void) {

	LONG32 instruction = memory[pctr >> 2];											// Fetch instruction
	pctr = (pctr + 4) & 0xFFFFC;													// Bump PC
	LONG32 n;

	switch (instruction >> 28) {													// Upper 4 bits.

		case 8:																		// 8x relative call 
			PUSHR(pctr);
			pctr = (pctr + (instruction & 0x0FFFFFFF)) & 0xFFFFC;
			break;
		case 9:																		// 9x relative bramch
			pctr = (pctr + (instruction & 0x0FFFFFFF)) & 0xFFFFC;
			break;
		case 10:																	// Ax relative branch if zero.
			PULLD(n);
			if (n == 0) {
				pctr = (pctr + (instruction & 0x0FFFFFFF)) & 0xFFFFC;
			}
			break;
		case 15:																	// Fx primitive
			_CPUExecutePrimitive(instruction & 0xFF);
			break;
		default:
			instruction = instruction & 0x7FFFFFFF;									// make 31 bit constant
			if ((instruction & 0x40000000) != 0) instruction |= 0x80000000; 		// sign extend.
			PUSHD(instruction);														// Push on Data Stack.
			break;
	}

	cycles++;
	if (cycles < CYCLES_PER_FRAME) return 0;										// Not completed a frame.
	cycles = cycles - CYCLES_PER_FRAME;												// Adjust this frame rate.
	return FRAME_RATE;																// Return frame rate.
}

// *******************************************************************************************************************************
//												Execute primitives
// *******************************************************************************************************************************

static void _CPUExecutePrimitive(BYTE8 opcode) {
	LONG32 n1,n2;
	switch (opcode) {
		case OP_READ:																// @ Read word. (address - data)
			CHECK(TOSD())									
			TOSD() = memory[(TOSD() >> 2) & 0xFFFFF];
			break;
		case OP_STORE:																// ! Write word. (data address -)
			PULLD(n1);PULLD(n2);CHECK(n1);
			memory[(n1 >> 2) & 0xFFFFF] = n2;
			break;
		case OP_C_READ:																// C@ Read byte (address - data)
			TOSD() = bMemory[TOSD() & 0xFFFFF];
			break;
		case OP_C_STORE:															// C! Write byte (data address -)
			PULLD(n1);PULLD(n2);
			bMemory[n1 & 0xFFFFF] = n2 & 0xFF;
			break;
		case OP_ADD_STORE:															// +! Add word to memory (additive address -)
			PULLD(n1);PULLD(n2);CHECK(n1);
			memory[(n1 >> 2) & 0xFFFFF] += n2;
			break;
		case OP_ADD:																// + add two numbers (n1 n2 - n1+n2)
			PULLD(n1);TOSD() = TOSD() + n1;
			break;
		case OP_SUB:																// - subtract two numbers (n1 n2 - n1-n2)
			PULLD(n1);TOSD() = TOSD() - n1;
			break;
		case OP_MUL:																// * multiply two numbers (n1 n2 - n1*n2)
			PULLD(n1);TOSD() = TOSD() * n1;
			break;
		case OP_DIV:																// / divide two numbers (n1 n2 - n1/n2 or 0 if n2 is 0
			PULLD(n1);TOSD() = (n1 != 0) ? TOSD() / n1 : 0;
			break;
		case OP_AND:																// AND bitwise and two numbers (n1 n2 - n1&n2)										
			PULLD(n1);TOSD() = TOSD() & n1;
			break;
		case OP_OR:																	// OR bitwise or two numbers (n1 n2 - n1|n2)
			PULLD(n1);TOSD() = TOSD() | n1;
			break;
		case OP_XOR:																// XOR bitwise xor two numbers (n1 n2 - n1^n2)
			PULLD(n1);TOSD() = TOSD() ^ n1;
			break;
		case OP_NOT:																// NOT 1's complement TOS (n1 - ~n1)
			TOSD() = TOSD() ^ 0xFFFFFFFF;
			break;
		case OP_0_EQUALS:															// 0= Push tos = 0 on stack (n1 - (n1 == 0))
			TOSD() = (TOSD() == 0) ? 0xFFFFFFFF : 0;
			break;
		case OP_0_GREATER:															// 0> Push tos > 0 on stack (n1 - (n1 > 0))
			n1 = TOSD();
			TOSD() = ((n1 & 0x80000000) == 0 && n1 != 0) ? 0xFFFFFFFF: 0;
			break;
		case OP_0_LESS:																// 0< Push tos < 0 on stack (n1 - (n1 < 0))
			TOSD() = ((TOSD() & 0x80000000) != 0) ? 0xFFFFFFFF : 0;
			break;
		case OP_0_SUB:																// 0- negate (n1 - -n1-n2)
			TOSD() = (-TOSD()) & 0xFFFFFFFF;
			break;
		case OP_1_ADD:																// 1+ increment (n1 - n1+1)
			TOSD() = (TOSD() + 1) & 0xFFFFFFFF;
			break;
		case OP_1_SUB:																// 1- decrement (n1 - n1-1)
			TOSD() = (TOSD() - 1) & 0xFFFFFFFF;
			break;
		case OP_2_MUL:																// 2* double (logical shift) (n1 - n1 << 1)
			TOSD() = (TOSD() << 1) & 0xFFFFFFFF;
			break;
		case OP_2_DIV:																// 2/ halve (logical shift) (n1 - n1 >> 1)
			TOSD() = (TOSD() >> 1) & 0x7FFFFFFF;
			break;
		case OP_DUP:																// DUP duplicate (n1 - n1 n1)
			n1 = TOSD();PUSHD(n1);															
			break;
		case OP_DROP:																// DROP drop TOS (n1 - )
			PULLD(n1);
			break;
		case OP_SWAP:																// SWAP swap top two (n1 n2 - n2 n1)
			n1 = TOSD();TOSD() = TOSD2();TOSD2() = n1;
			break;
		case OP_ROT:																// ROT rotate top three (n1 n2 n3 - n2 n2 n1)
			n1 = TOSD3();TOSD3() = TOSD2();TOSD2() = TOSD();TOSD() = n1;
			break;
		case OP_OVER:																// OVER dup 2nd (n1 n2 - n1 n2 n1)
			n1 = TOSD2();PUSHD(n1);
			break;
		case OP_SEMICOLON:															// ; return from subroutine
			PULLR(pctr);
			break;
		case OP_FROM_R:																// R> transfer from return to data
			PULLR(n1);PUSHD(n1);
			break;
		case OP_TO_R:																// >R transfer from data to return.
			PULLD(n1);PUSHR(n1);
			break;
		case OP_DOLLAR_HWIO:
			PULLD(n1);																// Pull command
			switch(n1) {
				case 0: n2 = HWIGetKey();PUSHD(n2);break;							// 0 $HWIO key gets key or zero.
				case 1:	PULLD(n2);HWIWriteScreenAddress(n2);break;					// addr 1 $HWIO sets write address
				case 2: PULLD(n2);HWIWriteScreenMemory(n2);break;					// addr 2 $HWIO writes to screen.
			}
			break;
	}
}

#ifdef INCLUDE_DEBUGGING_SUPPORT

// *******************************************************************************************************************************
//		Execute chunk of code, to either of two break points or frame-out, return non-zero frame rate on frame, breakpoint 0
// *******************************************************************************************************************************

BYTE8 CPUExecute(LONG32 breakPoint1,LONG32 breakPoint2) { 
	do {
		BYTE8 r = CPUExecuteInstruction();											// Execute an instruction
		if (r != 0) return r; 														// Frame out.
	} while (pctr != breakPoint1 && pctr != breakPoint2);							// Stop on breakpoint.
	return 0; 
}

// *******************************************************************************************************************************
//									Return address of breakpoint for step-over, or 0 if N/A
// *******************************************************************************************************************************

LONG32 CPUGetStepOverBreakpoint(void) {
	BYTE8 opcode = memory[pctr >> 2] >> 28;
	if (opcode != 8) return 0;														// Not a call.
	return (pctr+4) & 0xFFFFF;														// Instruction after next.	
}

// *******************************************************************************************************************************
//												Read/Write Memory
// *******************************************************************************************************************************

LONG32 CPUReadMemory(LONG32 address) {
	return memory[(address / 4) & 0x3FFFF] & 0xFFFFFFFF;
}

void CPUWriteMemory(WORD16 address,LONG32 data) {
	memory[(address/4) & 0x3FFFF] = data & 0xFFFFFFFF;
}

// *******************************************************************************************************************************
//												Load a binary file into RAM
// *******************************************************************************************************************************

#include <stdio.h>

void CPULoadBinary(const char *fileName) {
	FILE *f = fopen(fileName,"rb");
	BYTE8 *ram = (BYTE8 *)memory;
	ram += 0;
	while (!feof(f)) {
		fread(ram,1,16384,f);
		ram += 16384;
	}
	fclose(f);
}

// *******************************************************************************************************************************
//											Retrieve a snapshot of the processor
// *******************************************************************************************************************************

static CPUSTATUS s;																	// Status area

CPUSTATUS *CPUGetStatus(void) {
	s.pc = pctr;s.dsp = dsp;s.rsp = rsp;s.cycles = cycles;
	return &s;
}

#endif
