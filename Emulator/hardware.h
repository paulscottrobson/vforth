// *******************************************************************************************************************************
// *******************************************************************************************************************************
//
//		Name:		hardware.h
//		Purpose:	Hardware Interface (header)
//		Created:	25th July 2016
//		Author:		Paul Robson (paul@robsons.org.uk)
//
// *******************************************************************************************************************************
// *******************************************************************************************************************************

#ifndef _HARDWARE_H
#define _HARDWARE_H

void HWIReset(void);
BYTE8 HWIProcessKey(BYTE8 key,BYTE8 isRunMode);
WORD16 HWIReadScreenMemory(int x,int y);
void HWIWriteScreenAddress(LONG32 address);
void HWIWriteScreenMemory(LONG32 data);
BYTE8 HWIGetKey(void);
#endif
