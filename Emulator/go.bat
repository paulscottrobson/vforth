@echo off
python ..\BootCompiler\bc.py utility.c4 video.c4 input.c4 main.c4
vmforth.exe a.out
