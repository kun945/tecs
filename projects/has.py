#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Filename:     has.py
# Author:       chenkun<ckmx945@gmail.com>
# CreateDate:   2013-07-24

import os
import sys
import types
import string
import binascii

(U_COMMAND, A_COMMAND, C_COMMAND, L_COMMAND) = range(4) #U_COMMAND is unknow command
COMMAND = {
        U_COMMAND:"U_COMMAND", A_COMMAND:"A_COMMAND", C_COMMAND:"C_COMMAND", L_COMMAND:"L_COMMAND"
        }
(COMPLIE_UNKNOW, COMPLIE_SUCESS, COMPLIE_FAIL) = range(3) #complie status


class hasParser:
    def __init__(self, path):
        self.path = path
        self.line = 0
        self.data = None
        self.ctype = U_COMMAND
        self.fd = None
        self.error = None
        self.table = symbolTable()

    def hasOpen(self):
        if self.fd == None:
            self.fd = open(self.path, 'r')
        if self.fd == None:
            self.error = "open source file fail."
            return False
        else:
            return True

    def hasSymbolTable(self):
        if not self.hasOpen:
            return False
        caddr = 0 #memory address for instruction
        com = self.getCommand()
        state = COMPLIE_UNKNOW
        while com != None:
            ctype = self.hasCommandType(com)
            if ctype == A_COMMAND or ctype == C_COMMAND:
                caddr += 1
            elif ctype == L_COMMAND:
                com = com.split("//")[0]
                com = "".join(com.split(" "))
                array = com.split("(")
                if len(array) != 2 or array[0] != "":
                    self.error = "symbol from error, " + com
                    state = COMPLIE_FAIL
                    break
                array = array[1].split(")")
                if len(array) != 2 or array[1] != "":
                    self.error = "symbol from error, " + com
                    state = COMPLIE_FAIL
                    break
                key = array[0]
                if key == None or key == "":
                    self.error = "symbol is empty, " + com
                    state = COMPLIE_FAIL
                    break
                if self.table.stContains(key):
                    self.error = "symbol already exist, " + key
                    state = COMPLIE_FAIL
                    break
                self.table.stAddEntry(key, caddr)
            else:
                pass
            com = self.getCommand()
        if com == None:
            state = COMPLIE_SUCESS
        if state != COMPLIE_SUCESS:
            return False
        self.line = 0
        self.fd.seek(0, 0)
        return True


    def getCurrentLine(self):
        return self.line

    def hasMoreCommands(self):
        pass

    def getCommand(self):
        while True:
            data = self.fd.readline()
            if len(data) <= 0:
                return None
            self.line += 1
            data = data.strip()
            tlen = len(data)
            if tlen <=0:
                continue
            if tlen >= 2 and data[0] == '/' and data[1] == '/':
                continue
            if tlen >= 1 and (data[0] == '\n' or data[0] == '\r'):
                continue
            dlen = tlen - 1
            if dlen > 0 and data[dlen] == '\n':
                data = data[0:dlen]
            return data

    def __hasCommandFromInput():
        pass

    def hasCommandType(self, com):
        self.ctype = U_COMMAND
        for c in com:
            if c == ' ' or c == '\t':
                continue
            if c == '@':
                self.ctype = A_COMMAND
                break
            elif c == '(':
                self.ctype = L_COMMAND
                break
            else:
                self.ctype = C_COMMAND
                break
        return self.ctype
    def hasParserA(self, com):
        symbol = ""
        code = ""
        com = com.split("//")[0]
        com = "".join(com.split(" "))
        dlen = len(com)
        if dlen < 2:
            self.error = "command form error, " + com
            return False, code 
        if com[0] != '@':
            self.error = com + " is't A_COMMAND'" 
            return False, code
        symbol = com[1:dlen]
        addr = None
        if not symbol[0].isdigit():
            if not self.table.stContains(symbol):
                addr = self.table.stAddValue(symbol)
            else:
                addr = self.table.stGetAddress(symbol)
        if addr == None:
            try:
                addr = string.atoi(symbol)
            except ValueError:
                self.error = "symbol form error, " + symbol
                return False, code
        if addr > 32767:
            self.error = symbol + "out of memory"
            return False, code
        b = bin(addr)
        dlen = len(b)
        b = b[2:dlen]
        code = "0" * (18 - dlen) + b
        #print code
        return True, code

    def hasParserC(self, com):
        dest = "" 
        comp = ""
        jump = ""
        ret = False

        com = com.split("//")[0]
        #print com
        darray = com.split("=")
        if len(darray) == 2:
            dest = darray[0]
            temp = darray[1]
        elif len(darray) == 1:
            temp = darray[0]
        else:
            self.error = "command from error, " + com
            return False, None, None, None

        carray = temp.split(";")
        if len(carray) == 2:
            comp = carray[0];
            jump = carray[1];
        elif len(carray) == 1:
            comp = carray[0]
        else:
            self.error = "command from error, " + com
            return False, None, None, None

        dest = "".join(dest.split(" "))
        jump = "".join(jump.split(" "))
        comp = "".join(comp.split(" "))
        if comp != "":
            ret = True
        else:
            self.error = "command from error, " + com
        return ret, dest, comp, jump
    def hasErrorStr(self):
        error = self.error
        self.error = None
        return error
    def hasClose(self):
        if self.fd != None:
            self.fd.close()
        self.fd = None

class hasCode:
    def __init__(self):
        self.ddict = {
                "":"000", "M":"001", "D":"010", "MD":"011", "DM":"011",
                "A":"100", "AM":"101", "MA":"101", "AD":"110", "DA":"110",
                "AMD":"111", "ADM":"111", "MAD":"111", "MDA":"111", 
                "DAM":"111", "DMA":"111"
                }
        self.jdict = {
                "":"000", "JGT":"001", "JEQ":"010", "JGE":"011", "JLT":"100", 
                "JLE":"110", "JMP":"111", "JNE":"101"
                }
        self.cdict = {
                "":"??????", "0":"0101010", "1":"0111111", "-1":"0111010", 
                "D":"0001100", "A":"0110000", "!D":"0001101", "!A":"0110001", 
                "D+1":"0011111", "1+D":"0011111", "A+1":"0110111", 
                "1+A":"0110111", "-D":"0001111", "-A":"0110011", 
                "D-1":"0001110", "A-1":"0110010", "D+A":"0000010",
                "A+D":"0000010", "D-A":"0010011", "A-D":"0000111",
                "D&A":"0000000", "D|A":"0010101", "A&D":"0000000",
                "A|D":"0010101", "D|M":"1010101", "M|D":"1010101",
                "D&M":"1000000", "M&D":"1000000", "M-D":"1000111",
                "D-M":"1010011", "D+M":"1000010", "M+D":"1000010",
                "M-1":"1110010", "M+1":"1110111", "1+M":"1110111",
                "-M":"1110011", "!M":"1110001", "M":"1110000"
                }
        self.error = None
    def hasCodeDest(self, dest):
        dcode = None
        try:
            dcode = self.ddict[dest]
        except KeyError:
            self.error = "dest unknow instruction: " + dest
            return None
        return dcode
    def hasCodeComp(self, comp):
        ccode = None
        try:
            ccode = self.cdict[comp]
        except KeyError:
            self.error = "comp unknow instruction: " + comp
            return None
        return ccode
    def hasCodeJump(self, jump):
        jcode = None
        try:
            jcode = self.jdict[jump]
        except KeyError:
            self.error = "jump unknow instruction: " + jump
            return None
        return jcode
    def hasCodeErrorStr(self):
        error = self.error
        self.error = None
        return error
    def hasCodeCreate(self, dest, comp, jump):
        dcode = self.hasCodeDest(dest)
        if dcode == None:
            return False, None
        ccode = self.hasCodeComp(comp)
        if ccode == None:
            return False, None
        jcode = self.hasCodeJump(jump)
        if jcode == None:
            return False, None
        code = "111" + ccode + dcode + jcode
        return True, code

class symbolTable:
    def __init__(self):
        self.mddr = 16 #next memory address for value.
        self.stable = {
                "SP":0, "LCL":1, "ARG":2, "THIS":3, "R0":0, "THAT":4, 
                "R1":1, "R2":2, "R3":3, "R4":4, "R5":5, "R6":6, 
                "R7":7, "R8":8, "R9":9, "R10":10, "R11":11, 
                "R12":12, "R13":13, "R14":14, "R15":15,
                "SCREEN":16384, "KBD":24576
                }
    def stAddEntry(self, key, addr):
        self.stable[key] = addr
    def stAddValue(self, key):
        self.stable[key] = self.mddr
        self.mddr += 1
        return self.stable[key]
    def stContains(self, key):
        return key in self.stable
    def stGetAddress(self, key):
        return self.stable[key]
    def stPrintTable(self):
        print "symbol\t\taddress"
        for key in self.stable:
            print "%s\t\t%d" %(key, self.stable[key])

def hasUsage(exe):
    print "usage : %s <asm file>" %(exe)

def hasParserFilePath(ppath):
    path = ""
    pername = ""
    sufname = ""
    if not os.path.isfile(ppath):
        return False, path, pername
    os.path.dirname(ppath)
    pername, sufname = os.path.splitext(ppath)
    if sufname != ".asm":
        return False, path, pername
    return True, path, pername

if __name__ == "__main__":
    if len(sys.argv) != 2:
        hasUsage(sys.argv[0])
        exit(-1)
    sourceFile = sys.argv[1]
    #sourceFile = "./test.asm"
    ret, path, pername = hasParserFilePath(sourceFile)
    if not ret or pername == None:
        hasUsage(sys.argv[0])
        exit(-1)

    if path != None and path != "":
        targetFile = path + "/" + pername + ".hack"
    else:
        targetFile = pername + ".hack"

    targetFd = open(targetFile, 'w')
    if targetFd == None:
        print "create target file \"%s\" fail." %(targetFile)

    hp = hasParser(sourceFile)
    hc = hasCode()
    if hp.hasOpen() == False:
        print hp.hasErrorStr()
        targetFd.close()
        os.remove(targetFile)
        exit(-1)

    if not hp.hasSymbolTable():
        print hp.hasErrorStr()
        targetFd.close()
        hp.hasClose()
        os.remove(targetFile)
        exit(-1)

    #hp.table.stPrintTable()
    state = COMPLIE_UNKNOW
    error = None
    data = hp.getCommand()
    while data != None:
        ret = False
        code = None
        ctype = hp.hasCommandType(data)
        if ctype == A_COMMAND:
            ret, code = hp.hasParserA(data)
            error = hp.hasErrorStr()
        elif ctype == C_COMMAND:
            ret, d, c, j = hp.hasParserC(data)
            if not ret:
                print "%s parser fail: <line:%d>, %s" %(COMMAND[ctype], \
                        hp.getCurrentLine(), hp.hasErrorStr())
                state = COMPLIE_FAIL
                break
            ret, code = hc.hasCodeCreate(d, c, j)
            error = hc.hasCodeErrorStr()
        elif ctype == L_COMMAND:
            #print "L"
            data = hp.getCommand()
            continue 
        else:
            state = COMPLIE_FAIL
        if not ret or state == COMPLIE_FAIL:
            state = COMPLIE_FAIL
            print "%s parser fail: <line:%d>, %s" %(COMMAND[ctype], \
                    hp.getCurrentLine(), error)
            break
        else:
            #print "code", code
            targetFd.write(code+"\n")
        data = hp.getCommand()

    hp.hasClose()
    targetFd.close()
    if data == None:
        state = COMPLIE_SUCESS

    if state == COMPLIE_FAIL:
        os.remove(targetFile)
    elif state == COMPLIE_UNKNOW:
        os.remove(targetFile)
    else:
        print "complie success."
    exit(0)
