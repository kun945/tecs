// Author : chenkun <ckmx945@gamil.com>
@R3
M=0
@R2
M=0

(LOOP)
@R3
D=M
@R0
D=D-M
@END
D;JGE
@R1
D=M
@R2
M=M+D
@R3
M=M+1
@LOOP
0;JMP

(END)
@END
0;JMP
