// *******************************************************************************************************************************
// *******************************************************************************************************************************
//
//		Name:		processor.c
//		Purpose:	Processor Emulation.
//		Created:	21st June 2016
//		Author:		Paul Robson (paul@robsons.org.uk)
//
// *******************************************************************************************************************************
// *******************************************************************************************************************************

#include <stdlib.h>
#ifdef WINDOWS
#include <stdio.h>
#endif
#include "sys_processor.h"
#include "sys_debug_system.h"

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

// *******************************************************************************************************************************
//															Stack
// *******************************************************************************************************************************

#define PUSHD(v) { dsp -= 4;memory[dsp >> 2] = (v); }
#define PUSHR(v) { rsp -= 4;memory[rsp >> 2] = (v); }

#define PULLD(v,tgt) { tgt = memory[dsp >> 2];dsp += 4; }
#define PULLR(v,tgt) { tgt = memory[rsp >> 2];rsp += 4; }

// *******************************************************************************************************************************
//														Reset the CPU
// *******************************************************************************************************************************

void CPUReset(void) {
	pctr = 0x00000;
	rsp = RST_RSP;
	dsp = RST_DSP;
	cycles = 0;

	memory[0] = 42;
	memory[1] = -2 & 0x7FFFFFFF;
	memory[2] = 0x80000008;
}

// *******************************************************************************************************************************
//												Execute a single instruction
// *******************************************************************************************************************************

BYTE8 CPUExecuteInstruction(void) {

	LONG32 instruction = memory[pctr >> 2];											// Fetch instruction
	pctr = (pctr + 4) & 0xFFFFC;													// Bump PC

	switch (instruction >> 28) {													// Upper 4 bits.

		case 8:																		// 8x relative call forward
			PUSHR(pctr);
			pctr = (pctr + (instruction & 0x0FFFFFFF)) & 0xFFFFC;
			break;
		case 9:																		// 9x relative call backward
			PUSHR(pctr);
			pctr = (pctr - (instruction & 0x0FFFFFFF)) & 0xFFFFC;
			break;
		case 10:																	// Ax relative branch backward.
			pctr = (pctr - (instruction & 0x0FFFFFFF)) & 0xFFFFC;
			break;
		case 15:																	// Fx primitive
			// TODO: Do primitives.
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

#ifdef INCLUDE_DEBUGGING_SUPPORT

// *******************************************************************************************************************************
//		Execute chunk of code, to either of two break points or frame-out, return non-zero frame rate on frame, breakpoint 0
// *******************************************************************************************************************************

BYTE8 CPUExecute(LONG32 breakPoint) { 
	do {
		BYTE8 r = CPUExecuteInstruction();											// Execute an instruction
		if (r != 0) return r; 														// Frame out.
	} while (pctr != breakPoint);													// Stop on breakpoint.
	return 0; 
}

// *******************************************************************************************************************************
//									Return address of breakpoint for step-over, or 0 if N/A
// *******************************************************************************************************************************

LONG32 CPUGetStepOverBreakpoint(void) {
	return (pctr+1) & 0xFFFFF;														// Instruction after next.
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
//	FILE *f = fopen(fileName,"rb");
//	fread(ramMemory,1,MEMORYSIZE,f);
//	fclose(f);
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
