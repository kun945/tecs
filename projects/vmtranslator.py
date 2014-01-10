#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Filename:     vmtranslator.py
# Author:       chenkun<ckmx945@gmail.com>
# CreateDate:   2013-07-26

import os
import sys
import types
import string

(C_UNKNOW, C_ARITHMETIC, C_PUSH, C_POP, C_LABEL, C_GOTO, \
        C_IF, C_FUNCTION, C_RETURN, C_CALL) = range(10)
(SUCESS, FAIL, NOMORELINE, NOMOREFILE, OPENFAIL, COMTYPEERR) = \
        (0, -1, -2, -3, -4, -5)

class vmParser:
    def __init__(self, path):
        self.cdict = {}.fromkeys(
                ('add', 'sub', 'neg', 'eq', 'gt', 'lt', 
                    'and', 'or', 'not'), C_ARITHMETIC, 
                )
        self.cdict['push'] = C_PUSH
        self.cdict['pop'] = C_POP
        self.cdict['label'] = C_LABEL
        self.cdict['goto'] = C_GOTO
        self.cdict['if-goto'] = C_IF
        self.cdict['function'] = C_FUNCTION
        self.cdict['return'] = C_RETURN
        self.cdict['call'] = C_CALL
        self.cdict[''] = C_UNKNOW
        self.filelist = []
        if os.path.isfile(path):
            self.filelist.append(path)
        elif os.path.isdir(path):
            for root, dirs, files in os.walk(path):
                for f in files:
                    if os.path.splitext(f)[1] == ".vm":
                        self.filelist.append(root+"/"+f)
        self.findex = 0
        self.curline = 0
        self.curfd = None
        self.errstr = None
        self.path = path
        self.pername = None
    def vpGetCurrentFileName(self):
        #print self.findex, self.filelist
        return self.filelist[self.findex-1]
    def vpGetPathAndPername(self):
        if self.path != None and self.pername != None:
            return self.path, self.pername
        if os.path.isdir(self.path):
            self.pername = os.path.basename(self.path)
        elif os.path.isfile(self.path):
            path = os.path.dirname(self.path)
            temp = os.path.basename(self.path)
            self.pername = os.path.splitext(temp)[0]
            self.path = path
        return self.path, self.pername

    def vpPrintCommandDict(self):
        print self.cdict

    def vpGetCommanLine(self):
        ret = FAIL
        data = "" 
        while True:
            if self.curfd != None:
                data = self.curfd.readline()
                if data == None or len(data) <= 0:
                    self.curfd.close()
                    self.curline = 0
                    self.curfd = None
                    continue
                else:
                    #print data
                    self.curline += 1
                    data = data.strip()
                    tlen = len(data)
                    if tlen <= 0:
                        continue
                    if tlen >= 2 and data[0] == '/' and data[1] == '/':
                        continue
                    if tlen >= 1 and (data[0] == '\n' or data[0] == '\r'):
                        continue
                    dlen = tlen - 1
                    if dlen > 0 and data[dlen] == '\n':
                        data = data[0:dlen]
                    data = data.split('//')[0]
                    ret = SUCESS
                    data = data.strip()
                    break
            else:
                if self.findex < len(self.filelist):
                    self.curfd = open(self.filelist[self.findex], 'r')
                    if self.curfd == None:
                       self.errstr = "open " + \
                               self.filelist[self.findex] + " fail."
                       ret = OPENFAIL
                       data = ""
                       break
                    else:
                       self.findex += 1
                       continue
                else:
                    self.errstr = "no more file."
                    ret = SUCESS
                    data = ""
                    break
        return ret, data

    @staticmethod
    def vpParserCommand(data):
        pp = []
        offset = None
        array = data.split(' ')
        for temp in array:
            if temp == '':
                continue
            pp.append(temp.strip())
        return pp

    def vpGetCurrentLine(self):
        return self.curline

    def vpCommandType(self, data):
        com = data.split(' ')[0]
        if com in self.cdict:
            return self.cdict[com]
        else:
            self.errstr = "unknow comand type: %s" %data
            return C_UNKNOW
    def vpClose(self):
        if self.curfd != None:
            self.curfd.close()

    def vpGetErrorStr(self):
        error = self.errstr
        self.errstr = None 
        return error

class vmCodeWrite:
    def __init__(self, path, pername):
        self.pername = pername
        self.savename = path + "/" + pername + ".asm"
        self.funname = ["null"]
        self.funcount = 1
        self.callcount = 0
        self.jpcount = 0
        self.fd = None
        self.errstr = None
        self.posdict = {
                "local":"LCL", "argument":"ARG", "this":"THIS", 
                "that":"THAT", "temp":"R5", "pointer":"R3"
                }

    def vcOpen(self):
        self.fd = open(self.savename, 'w')
        if self.fd == None:
            self.errstr = "open " + self.savename + " fail."
            return False
        else:
            return True

    def vcTestSet(self, sp, lcl, arg, this, that):
        buf = "@%d\nD=A\n@LCL\nM=D\n" %lcl
        self.fd.write(buf)
        buf = "@%d\nD=A\n@ARG\nM=D\n" %arg
        self.fd.write(buf)
        buf = "@%d\nD=A\n@SP\nM=D\n" %sp
        self.fd.write(buf)
        buf = "@%d\nD=A\n@THIS\nM=D\n" %this
        self.fd.write(buf)
        buf = "@%d\nD=A\n@THAT\nM=D\n" %that
        self.fd.write(buf)

    def vcCodePushPop(self, com, path):
        asm = ""
        comstr = ""
        for temp in com:
            comstr += "%s " %temp
        if len(com) != 3:
            self.errstr = \
                    "push or pop command format error: %s" %comstr
            return FAIL
        command = com[0]
        segment = com[1]
        index = com[2]
        try:
            offset = string.atoi(index)
        except ValueError:
            self.errstr = \
                    "push or pop command 'index' format error: %s" %index
            return FAIL
        if offset == None:
            self.errstr = \
                    "push or pop command 'index' format error: %s" %index
            return FAIL
        if segment == "constant":
            asm += "@%d\nD=A\n" %offset
        elif segment == "temp" or segment == "pointer":
            asm += "@%s\nD=A\n" %self.posdict[segment]
        elif segment == "static":
            sym = self.vcGetFilePername(path)
            asm +=  "@%s.%d\nD=A\n" %(sym, offset)
        else:
            if segment in self.posdict:
                asm += "@%s\nD=M\n" %self.posdict[segment]
            else:
                self.errstr = \
                        "push command 'segment' format error: %s" %segment
                return FAIL
        if offset > 0 and segment != "constant" and segment != "static":
            asm += "@%d\nD=D+A\n" %offset
        if command == "push":
            if segment != "constant":
                asm += "A=D\nD=M\n"
            asm += "@SP\nAM=M+1\nA=A-1\nM=D\n"
        else:
            if segment ==  "constant":
                self.errstr = \
                        "push command 'segment' format error: %s" %segment
                return FAIL
            asm += "@R13\nM=D\n@SP\nAM=M-1\nD=M\nM=0\n@R13\nA=M\nM=D\n"

        if asm != "":
            self.fd.write("//" + comstr + "\n")
            self.fd.write(asm)
        return SUCESS

    def vcCodeArithmetic(self, com):
        asm = "@SP\nA=M-1\n"
        if com == "neg":
            asm += "M=-M\n"
        elif com == "not":
            asm += "M=!M\n"
        else:
            asm += "D=M\n@SP\nAM=M-1\nM=0\nA=A-1\n"
            if com == "add":
                asm += "M=M+D\n"
            elif com == "sub":
                asm += "M=M-D\n"
            elif com == "and":
                asm += "M=M&D\n"
            elif com == "or":
                asm += "M=M|D\n"
            else:
                asm += "D=M-D\n@__TRUE__.%d\n" %self.jpcount
                if com == "eq":
                    asm += "D;JEQ\n"
                elif com == "lt":
                    asm += "D;JLT\n"
                elif com == "gt":
                    asm += "D;JGT\n"
                else:
                    self.errstr = \
                        "arithmetic command format error: %s" %com
                    return FAIL
                asm += "@SP\nA=M-1\nM=0\n@__FALSE__.%d\n0;JMP\n" \
                        "(__TRUE__.%d)\n@SP\nA=M-1\nM=-1\n(__FALSE__.%d)\n" \
                        %(self.jpcount, self.jpcount, self.jpcount)
                self.jpcount += 1
        self.fd.write("//" + com + "\n")
        self.fd.write(asm)
        return  SUCESS

    def vcCodeLable(self, com):
        asm = ""
        comstr = ""
        for temp in com:
            comstr += "%s " %temp
        if len(com) != 2:
            self.errstr = \
                    "lable command format error: %s" %comstr
            return FAIL
        command = com[0]
        lable = com[1]
        #asm += "(%s$%s)\n" %(self.funname[self.funcount-1], lable)
        asm += "(%s.%d)\n" %(lable, self.callcount)
        self.fd.write("//"+comstr+"\n")
        self.fd.write(asm)
        return SUCESS

    def vcCodeGoto(self, com):
        asm = ""
        comstr = ""
        for temp in com:
            comstr += "%s " %temp
        if len(com) != 2:
            self.errstr = \
                    "goto command format error: %s" %comstr
            return FAIL
        command = com[0]
        lable = com[1]
        #asm += "@%s$%s\n" %(self.funname[self.funcount-1], lable)
        asm += "@%s.%d\n" %(lable, self.callcount)
        asm += "0;JMP\n"
        self.fd.write("//"+comstr+"\n")
        self.fd.write(asm)
        return SUCESS

    def vcCodeIF(self, com):
        asm = ""
        comstr = ""
        for temp in com:
            comstr += "%s " %temp
        if len(com) != 2:
            self.errstr = \
                    "goto command format error: %s" %comstr
            return FAIL
        command = com[0]
        lable = com[1]
        asm += "@SP\nAM=M-1\nD=M\nM=0\n"
        #asm += "@%s$%s\n" %(self.funname[self.funcount-1], lable)
        asm += "@%s.%d\n" %(lable, self.callcount)
        asm += "D;JNE\n"
        self.fd.write("//"+comstr+"\n")
        self.fd.write(asm)
        return SUCESS

    def vcCodeFunction(self, com):
        asm = ""
        comstr = ""
        argc = 0
        for temp in com:
            comstr += "%s " %temp
        if len(com) != 3:
            self.errstr = \
                    "function command format error: %s" %comstr
            return FAIL
        try:
            argc = string.atoi(com[2])
        except ValueError:
            self.errstr = \
                    "function command 'argc' format error: %s" %com[2]
            return FAIL
        command = com[0]
        funname = com[1]
        asm += "(%s)\n" %funname
        if argc > 0 :
            asm += "@%d\nD=A\n" %argc
            asm += "(%s$__LOCAL_INIT__)\n" %funname
            asm += "@SP\nAM=M+1\nA=A-1\nM=0\n"
            asm += "@%s$__LOCAL_INIT__\n" %funname
            asm += "D=D-1;JGT\n"
        self.funname.append(funname)
        self.funcount += 1
        self.fd.write("//"+comstr+"\n")
        self.fd.write(asm)
        #print "funcount count=%d, push name=%s" %(self.funcount, funname)
        return SUCESS

    def vcCodeCall(self, com):
        asm = ""
        comstr = ""
        push = "@SP\nM=M+1\nA=M-1\nM=D\n"
        argc = 0
        for temp in com:
            comstr += "%s " %temp
            
        if len(com) != 3:
            self.errstr = \
                    "call command format error: %s" %comstr
            return FAIL
        try:
            argc = string.atoi(com[2])
        except ValueError:
            self.errstr = \
                    "call command format error: %s" %comstr
            return FAIL
        command = com[0]
        funname = com[1]
        argpos = argc + 5
        asm += "@__RETURN_ADDRESS__.%d\nD=A\n%s" %(self.callcount, push)
        asm += "@LCL\nD=M\n" + push
        asm += "@ARG\nD=M\n" + push
        asm += "@THIS\nD=M\n" + push
        asm += "@THAT\nD=M\n" + push
        asm += "@SP\nD=M\n@LCL\nM=D\n@%d\nD=D-A\n@ARG\nM=D\n" %argpos
        asm += "@%s\n0;JMP\n" %funname
        asm += "(__RETURN_ADDRESS__.%d)\n" %self.callcount
        self.callcount += 1
        self.fd.write("//"+comstr+"\n")
        self.fd.write(asm)
        return SUCESS

    def vcCodeReturn(self, com):
        asm = "@LCL\nD=M\n@R13\nM=D\n"
        asm += "@5\nA=D-A\nD=M\n@R14\nM=D\n"
        asm += "@SP\nAM=M-1\nD=M\n@ARG\nA=M\nM=D\n"
        asm += "@ARG\nD=M\n@SP\nM=D+1\n"
        asm += "@R13\nAM=M-1\nD=M\nM=0\n@THAT\nM=D\n"
        asm += "@R13\nAM=M-1\nD=M\nM=0\n@THIS\nM=D\n"
        asm += "@R13\nAM=M-1\nD=M\nM=0\n@ARG\nM=D\n"
        asm += "@R13\nAM=M-1\nD=M\nM=0\n@LCL\nM=D\n"
        asm += "@R14\nA=M\n0;JMP\n"
        #self.funcount -= 1
        #funname = self.funname.pop()
        #print "funcount count=%d, pop name=%s" %(self.funcount, funname)
        self.fd.write("//" + com + "\n")
        self.fd.write(asm)
        return SUCESS

    def vcCodeInit(self):
        asm = "//set stack\n@256\nD=A\n@SP\nM=D\n"
        self.fd.write(asm)
        return self.vcCodeCall(["call", "Sys.init", "0"])
        
    def vcClose(self):
        self.fd.close
        self.fd = None
    def vcRemove(self):
        os.remove(self.savename)

    def vcGetErrorStr(self):
        error = self.errstr
        self.errstr = None
        return error

    @staticmethod
    def vcGetFilePername(path):
        name = os.path.basename(path)
        return os.path.splitext(name)[0]

#FILE = "./SimpleAdd.vm"
#FILE = "./FibonacciElement"
#FILE = "./SimpleFunction"
#FILE = "./StaticsTest"
#FILE = "./BasicLoop"
FILE = "./FibonacciSeries"
#FILE = "./test"

def vmDBG(c, p, s):
    name = p.vpGetCurrentFileName()
    line = p.vpGetCurrentLine()
    print "[%s] <line:%05d>: %s" %(name, line, s)

if __name__ == "__main__":
    #if len(sys.argv) != 2:
    #    print "usage: %s <vm file/paht>" %sys.argv[0]
    #    exit(-1)
    #FILE = sys.argv[1]
    parser = vmParser(FILE)
    path, pername = parser.vpGetPathAndPername()
    if path == None or pername == None:
        exit(-1)
    code = vmCodeWrite(path, pername)
    if code.vcOpen() != True:
        print code.vcGetErrorStr()
        exit(-1)
    #code.vcTestSet(256, 0, 0, 0, 0)
    #code.vcCodeInit()
    data = ""
    ret = FAIL
    ret, data = parser.vpGetCommanLine()
    while ret == SUCESS and len(data) > 0:
        ctype = parser.vpCommandType(data)
        print data
        if ctype == C_PUSH or ctype == C_POP:
            path = parser.vpGetCurrentFileName()
            com = parser.vpParserCommand(data)
            if code.vcCodePushPop(com, path) != SUCESS:
                vmDBG(code, parser, code.vcGetErrorStr())
                break
        elif ctype == C_ARITHMETIC:
            if code.vcCodeArithmetic(data) != SUCESS:
                vmDBG(code, parser, code.vcGetErrorStr())
                break
        elif ctype == C_LABEL:
            com = parser.vpParserCommand(data)
            if code.vcCodeLable(com) != SUCESS:
                vmDBG(code, parser, code.vcGetErrorStr())
                break
        elif ctype == C_IF:
            com = parser.vpParserCommand(data)
            if code.vcCodeIF(com) != SUCESS:
                vmDBG(code, parser, code.vcGetErrorStr())
                break
        elif ctype == C_GOTO:
            com = parser.vpParserCommand(data)
            if code.vcCodeGoto(com) != SUCESS:
                vmDBG(code, parser, code.vcGetErrorStr())
                break
        elif ctype == C_CALL:
            com = parser.vpParserCommand(data)
            if code.vcCodeCall(com) != SUCESS:
                vmDBG(code, parser, code.vcGetErrorStr())
                break
        elif ctype == C_FUNCTION:
            com = parser.vpParserCommand(data)
            if code.vcCodeFunction(com) != SUCESS:
                vmDBG(code, parser, code.vcGetErrorStr())
                break
        elif ctype == C_RETURN:
            if code.vcCodeReturn(data) != SUCESS:
                vmDBG(code, parser, code.vcGetErrorStr())
                break
        else:
            vmDBG(code, parser, parser.vpGetErrorStr())
            break
        ret , data = parser.vpGetCommanLine()
    code.vcClose()
    parser.vpClose()
    if ret == SUCESS and len(data) == 0:
        print "+++++++++++++++++++++++++++++++++++++"
        exit(0)
    code.vcRemove()
    exit(-1)
