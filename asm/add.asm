// Author : chenkun <ckmx945@gmail.com>

@i
M=1
@sum
M=0
(LOOP)
@i
D=M
@100
D=D-A
@END
D;JGT
@i
D=M
@sum
M=M+D
@i
M=M+1
@LOOP
0;JMP
(END)
@END
0;JMP
