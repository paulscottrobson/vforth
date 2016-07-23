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

#ifdef INCLUDE_DEBUGGING_SUPPORT													// Only required for debugging

typedef struct __CPUSTATUS {
	int pc,rsp,dsp,cycles;
} CPUSTATUS;

CPUSTATUS *CPUGetStatus(void);
BYTE8 CPUExecute(LONG32 breakPoint);
LONG32 CPUGetStepOverBreakpoint(void);
LONG32 CPUReadMemory(LONG32 address);
void CPUWriteMemory(LONG32 address,LONG32 data);
void CPULoadBinary(const char *fileName);
#endif
#endif