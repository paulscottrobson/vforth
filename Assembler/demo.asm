	:at
	+2 						// Skip 8 words

	:freddie
	b .2
	bl .2
	.2 						// label 2
	bz at 					// call another word
	bge  .2 				// call a label
	bl 	.2

	addnz @r11,r4
	xor r11,-242
	and r11,242
	mov r1,4,7

