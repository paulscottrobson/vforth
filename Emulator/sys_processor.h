// *******************************************************************************************************************************
// *******************************************************************************************************************************
//
//		Name:		processor.h
//		Purpose:	Processor Emulation (header)
//		Created:	21st June 2016
//		Author:		Paul Robson (paul@robsons.org.uk)
//
// *******************************************************************************************************************************
// *******************************************************************************************************************************

#ifndef _PROCESSOR_H
#define _PROCESSOR_H

typedef unsigned int LONG32; 														// 32 bit type.
typedef unsigned short WORD16;														// 8 and 16 bit types.
typedef unsigned char  BYTE8;

void CPUReset(void);
BYTE8 CPUExecuteInstruction(void);

#define RST_RSP 	0x80000
#define RST_DSP 	0x7F800

#ifdef INCLUDE_DEBUGGING_SUPPORT													// Only required for debugging

typedef struct __CPUSTATUS {
	long pc,rsp,dsp,cycles;
} CPUSTATUS;

CPUSTATUS *CPUGetStatus(void);
BYTE8 CPUExecute(LONG32 breakPoint1,LONG32 breakPoint2);
LONG32 CPUGetStepOverBreakpoint(void);
LONG32 CPUReadMemory(LONG32 address);
void CPUWriteMemory(LONG32 address,LONG32 data);
void CPULoadBinary(const char *fileName);
#endif
#endif