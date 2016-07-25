@echo off
python ..\BootCompiler\bc.py utility.src video.src main.src
vmforth.exe a.out
