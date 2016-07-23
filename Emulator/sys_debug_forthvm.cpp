// *******************************************************************************************************************************
// *******************************************************************************************************************************
//
//		Name:		sys_debug_forthvm.c
//		Purpose:	Debugger Code (System Dependent)
//		Created:	21st June 2016
//		Author:		Paul Robson (paul@robsons->org.uk)
//
// *******************************************************************************************************************************
// *******************************************************************************************************************************

#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#include "gfx.h"
#include "sys_processor.h"
#include "debugger.h"

#define DBGC_ADDRESS 	(0x0F0)														// Colour scheme.
#define DBGC_DATA 		(0x0FF)														// (Background is in main.c)
#define DBGC_HIGHLIGHT 	(0xFF0)

// *******************************************************************************************************************************
//											This renders the debug screen
// *******************************************************************************************************************************

static const char *labels[] = { "PCTR","DSP","RSP","BRK", NULL };

void DBGXRender(int *address,int runMode) {
	CPUSTATUS *s = CPUGetStatus();
	GFXSetCharacterSize(42,25);
	DBGVerticalLabel(25,0,labels,DBGC_ADDRESS,-1);									// Draw the labels for the register

	GFXNumber(GRID(34,0),s->pc,16,5,GRIDSIZE,DBGC_DATA,-1);
	GFXNumber(GRID(34,1),s->dsp,16,5,GRIDSIZE,DBGC_DATA,-1);
	GFXNumber(GRID(34,2),s->rsp,16,5,GRIDSIZE,DBGC_DATA,-1);
	GFXNumber(GRID(34,3),address[3],16,5,GRIDSIZE,DBGC_DATA,-1);

	for (int i = 0;i < 2;i++) {
		int x = 25 + i*9;
		int y = 5;
		const char *st = (i == 0) ? "DATA":"RETURN";
		GFXString(GRID(x+4-strlen(st)/2,y),st,GRIDSIZE,DBGC_ADDRESS,-1);
		y++;
		int topOfStack = (i == 0) ? RST_DSP:RST_RSP;
		int stack = (i == 0) ? s->dsp:s->rsp;
		int colour = DBGC_HIGHLIGHT;
		while (stack < topOfStack && y <= 15) {
			long n = CPUReadMemory(stack) & 0xFFFFFFFF;
			GFXNumber(GRID(x,y),n,16,8,GRIDSIZE,colour,-1);
			colour = DBGC_DATA;
			y++;
			stack += 4;
		}
	}
	for (int y = 17;y < 25;y++) {
		int addr = (address[1] + (y - 17) * 16) & 0xFFFFC;
		GFXNumber(GRID(1,y),addr,16,8,GRIDSIZE,DBGC_ADDRESS,-1);
		for (int x = 0;x < 4;x++) {
			LONG32 n = CPUReadMemory(addr);
			GFXNumber(GRID(10+x*9,y),n,16,8,GRIDSIZE,DBGC_DATA,-1);
			addr = (addr + 4) & 0xFFFFC;
		}
	}

	for (int y = 0;y < 16;y++) {
		int addr = (address[0]+y*4) & 0xFFFFC;
		int isBrk = (addr == address[3]);
		long code = CPUReadMemory(addr) & 0xFFFFFFFF;
		GFXNumber(GRID(0,y),addr,16,5,GRIDSIZE,isBrk ? DBGC_HIGHLIGHT:DBGC_ADDRESS,-1);
		GFXNumber(GRID(6,y),code,16,8,GRIDSIZE,isBrk ? DBGC_HIGHLIGHT:DBGC_DATA,-1);
	}
	if (runMode) {
		SDL_Rect rc;rc.x = rc.y = 200;rc.w = rc.h = 300;
		GFXRectangle(&rc,0xFF00FF);
	}

/*
	#define DN(v,w) GFXNumber(GRID(18,n++),v,16,w,GRIDSIZE,DBGC_DATA,-1)			// Helper macro

	n = 0;
	DN(s->d,2);DN(s->df,1);DN(s->p,1);DN(s->x,1);DN(s->t,2);DN(s->ie,1);			// Registers
	DN(s->pc,4);DN(s->r[s->x],4);DN(s->cycles,4);DN(address[3],4);					// Others

	for (int i = 0;i < 16;i++) {													// 16 bit registers
		sprintf(buffer,"R%x",i);
		GFXString(GRID(i % 4 * 8,i/4+12),buffer,GRIDSIZE,DBGC_ADDRESS,-1);
		GFXString(GRID(i % 4 * 8+2,i/4+12),":",GRIDSIZE,DBGC_HIGHLIGHT,-1);
		GFXNumber(GRID(i % 4 * 8+3,i/4+12),s->r[i],16,4,GRIDSIZE,DBGC_DATA,-1);
	}

	int a = address[1];																// Dump Memory.
	for (int row = 17;row < 23;row++) {
		GFXNumber(GRID(2,row),a,16,4,GRIDSIZE,DBGC_ADDRESS,-1);
		GFXCharacter(GRID(6,row),':',GRIDSIZE,DBGC_HIGHLIGHT,-1);
		for (int col = 0;col < 8;col++) {
			GFXNumber(GRID(7+col*3,row),CPUReadMemory(a),16,2,GRIDSIZE,DBGC_DATA,-1);
			a = (a + 1) & 0xFFFF;
		}		
	}

	int p = address[0];																// Dump program code. 
	int opc;

	for (int row = 0;row < 11;row++) {
		int isPC = (p == ((s->pc) & 0xFFFF));										// Tests.
		int isBrk = (p == address[3]);
		GFXNumber(GRID(0,row),p,16,4,GRIDSIZE,isPC ? DBGC_HIGHLIGHT:DBGC_ADDRESS,	// Display address / highlight / breakpoint
																	isBrk ? 0xF00 : -1);
		opc = CPUReadMemory(p);p = (p + 1) & 0xFFFF;								// Read opcode.
		strcpy(buffer,_mnemonics[opc]);												// Work out the opcode.
		char *at = buffer+strlen(buffer)-2;											// 2nd char from end
		if (*at == '.') {															// Operand ?
			if (at[1] == '1') {
				sprintf(at,"%02x",CPUReadMemory(p));
				p = (p+1) & 0xFFFF;
			}
		}
		GFXString(GRID(5,row),buffer,GRIDSIZE,isPC ? DBGC_HIGHLIGHT:DBGC_DATA,-1);	// Print the mnemonic
	}


	int width = 64;																	// Get screen display resolution.
	int height = 32;
	int ramAddress = HWIGetDisplayAddress();

	SDL_Rect rc;rc.x = _GFXX(21);rc.y = _GFXY(1)/2;									// Whole rectangle.
	rc.w = 11 * GRIDSIZE * 6;rc.h = 5 *GRIDSIZE * 8; 										
	if (runMode != 0) {
		rc.w = WIN_WIDTH * 8 / 10;rc.h = WIN_HEIGHT * 4/10;
		rc.x = WIN_WIDTH/2-rc.w/2;rc.y = WIN_HEIGHT - rc.h - 64;
	}
	rc.w = rc.w/64*64;rc.h = rc.h/32*32;											// Make it /64 /32

	if (!HWIIsScreenOn()) {															// Screen off, show static.
		SDL_Rect rcp;		
		rcp.w = rcp.h = rc.w/256;if (rcp.w == 0) rcp.w = rcp.h = 1;
		GFXRectangle(&rc,0x00000000);
		for (rcp.x = rc.x;rcp.x <= rc.x+rc.w;rcp.x += rcp.w)
			for (rcp.y = rc.y;rcp.y <= rc.y+rc.h;rcp.y += rcp.h) {
				if (rand() & 1) GFXRectangle(&rcp,0xFFFFFF);
			}
		return;		
	}

	SDL_Rect rcPixel;rcPixel.h = rc.h/32;rcPixel.w = rc.w / 64;						// Pixel rectangle.
	SDL_Rect rcDraw;rcDraw.w = rcPixel.w/2;rcDraw.h = rcPixel.h/2;
	GFXRectangle(&rc,0x0);															// Fill it black
	for (int j = 0;j < height;j++) {
		for (int i = 0;i < width;i += 8) {
			BYTE8 vRam = CPUReadMemory(ramAddress++);
			for (int b = 0;b < 8;b++) {
				if (vRam & (0x80 >> b))
				{
					rcDraw.x =  rc.x + (i+b) * rcPixel.w;
					rcDraw.y = rc.y + j * rcPixel.h;
					GFXRectangle(&rcDraw,0xFFFFFF);
				}
			}
		}
	}
*/
}	