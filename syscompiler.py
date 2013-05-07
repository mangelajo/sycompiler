#-----------------------------------------------------------------------------
# Name:        syscompiler.g
# Purpose:     yapps2 grammar for syscompiler
#
# Author:      Miguel Angel Ajo Pelayo
#
# Created:     2005/29/07
# RCS-ID:      $Id: syscompiler.g $
# Copyright:   (c) 2004
# Licence:     GNU Public License (GPL)
#----------------------------------------------------------------------------

from syobjs import *
def check_param_case(scanner,param_name):
    if param_name.upper()!=param_name:
        raise SyntaxError(scanner.pos, "parameter names should be UPCASE")

def check_sys_name(scanner,sys_name,ID):
    if ID!=sys_name:
        raise SyntaxError(scanner.pos, "SYS NAME: " + ID + " != " + sys_name)

def check_task_name(scanner,task_name,ID):
    if ID!=task_name:
        raise SyntaxError(scanner.pos, "TASK NAME: " + ID + " != " + task_name)

from string import *
import re
from yappsrt import *

class sycompScanner(Scanner):
    patterns = [
        ('"ns"', re.compile('ns')),
        ('"us"', re.compile('us')),
        ('"ms"', re.compile('ms')),
        ('"\\\\]"', re.compile('\\]')),
        ('"\\\\["', re.compile('\\[')),
        ('"\\\\*"', re.compile('\\*')),
        ('"END MESSAGE"', re.compile('END MESSAGE')),
        ('";"', re.compile(';')),
        ('"FROM"', re.compile('FROM')),
        ('"MESSAGE"', re.compile('MESSAGE')),
        ('","', re.compile(',')),
        ('"USES"', re.compile('USES')),
        ('"LOAD"', re.compile('LOAD')),
        ('"PERIOD"', re.compile('PERIOD')),
        ('"TASK"', re.compile('TASK')),
        ('"."', re.compile('.')),
        ('"END"', re.compile('END')),
        ("'END CODE'", re.compile('END CODE')),
        ("'CODE'", re.compile('CODE')),
        ("'END CREATE'", re.compile('END CREATE')),
        ("'CREATE'", re.compile('CREATE')),
        ('"FILEPREFIX"', re.compile('FILEPREFIX')),
        ('">"', re.compile('>')),
        ('"PRIORITY"', re.compile('PRIORITY')),
        ('"SYSTEM"', re.compile('SYSTEM')),
        ('[\t\n\r ]+', re.compile('[\t\n\r ]+')),
        ('//.*\n', re.compile('//.*\n')),
        ('ID', re.compile('[a-zA-Z_][a-zA-Z_0-9]*')),
        ('FILENAME', re.compile('[a-zA-Z_\\.][a-zA-Z_0-9\\.]*')),
        ('VAL', re.compile('.*')),
        ('NUM', re.compile('[0-9]+')),
    ]
    def __init__(self, str):
        Scanner.__init__(self,None,['[\t\n\r ]+', '//.*\n'],str)

class sycomp(Parser):
    def system(self):
        self._scan('"SYSTEM"')
        ID = self._scan('ID')
        system = System(ID)
        if self._peek('"PRIORITY"', '">"', '"FILEPREFIX"', "'CREATE'", "'CODE'", '"END"', '"TASK"') == '"PRIORITY"':
            self._scan('"PRIORITY"')
            ID = self._scan('ID')
            while self._peek('">"', '"FILEPREFIX"', "'CREATE'", "'CODE'", '"END"', '"TASK"') == '">"':
                self._scan('">"')
                ID = self._scan('ID')
        if self._peek('"FILEPREFIX"', "'CREATE'", "'CODE'", '"END"', '"TASK"') == '"FILEPREFIX"':
            self._scan('"FILEPREFIX"')
            ID = self._scan('ID')
            system.set_file_prefix(ID)
        if self._peek("'CREATE'", "'CODE'", '"END"', '"TASK"') == "'CREATE'":
            while 1:
                self._scan("'CREATE'")
                FILENAME = self._scan('FILENAME')
                f_create=open(FILENAME,'w')
                while self._peek('VAL', "'END CREATE'") == 'VAL':
                    VAL = self._scan('VAL')
                    f_create.write(VAL+"\n")
                self._scan("'END CREATE'")
                f_create.close()
                if self._peek("'CREATE'", "'CODE'", '"END"', '"TASK"') != "'CREATE'": break
        if self._peek("'CODE'", '"END"', '"TASK"') == "'CODE'":
            self._scan("'CODE'")
            while self._peek('VAL', "'END CODE'") == 'VAL':
                VAL = self._scan('VAL')
                system.add_c_def(VAL)
            self._scan("'END CODE'")
        while self._peek('"END"', '"TASK"') == '"TASK"':
            module = self.module(system)
        self._scan('"END"')
        ID = self._scan('ID')
        self._scan('"."')
        check_sys_name(self._scanner,system.name,ID)
        system.process()

    def module(self, SYS):
        self._scan('"TASK"')
        ID = self._scan('ID')
        module = Module(ID,SYS)
        if self._peek('"PERIOD"', '"LOAD"', '"FILEPREFIX"', '"USES"', '","', "'CODE'", '"END"', '"MESSAGE"') == '"PERIOD"':
            self._scan('"PERIOD"')
            NUM = self._scan('NUM')
            timeunit = self.timeunit(NUM)
        if self._peek('"LOAD"', '"FILEPREFIX"', '"USES"', '","', "'CODE'", '"END"', '"MESSAGE"') == '"LOAD"':
            self._scan('"LOAD"')
            NUM = self._scan('NUM')
            timeunit = self.timeunit(NUM)
        if self._peek('"FILEPREFIX"', '"USES"', '","', "'CODE'", '"END"', '"MESSAGE"') == '"FILEPREFIX"':
            self._scan('"FILEPREFIX"')
            ID = self._scan('ID')
            module.set_file_prefix(ID)
        if self._peek('"USES"', '","', "'CODE'", '"END"', '"MESSAGE"') == '"USES"':
            self._scan('"USES"')
            ID = self._scan('ID')
            module.use_module(ID)
            while self._peek('","', "'CODE'", '"END"', '"MESSAGE"') == '","':
                self._scan('","')
                ID = self._scan('ID')
                module.use_module(ID)
        if self._peek("'CODE'", '"END"', '"MESSAGE"') == "'CODE'":
            self._scan("'CODE'")
            while self._peek('VAL', "'END CODE'") == 'VAL':
                VAL = self._scan('VAL')
                module.add_c_def(VAL)
            self._scan("'END CODE'")
        while self._peek('"END"', '"MESSAGE"') == '"MESSAGE"':
            message = self.message(module)
        self._scan('"END"')
        ID = self._scan('ID')
        check_task_name(self._scanner, module.name, ID)
        SYS.add_module(module)

    def message(self, MOD):
        self._scan('"MESSAGE"')
        ID = self._scan('ID')
        message=Message(ID,MOD)
        if self._peek('"FROM"', '","', '"END MESSAGE"', 'ID') == '"FROM"':
            self._scan('"FROM"')
            ID = self._scan('ID')
            message.add_src(ID)
            while self._peek('","', '"END MESSAGE"', 'ID') == '","':
                self._scan('","')
                ID = self._scan('ID')
                message.add_src(ID)
        while self._peek('"END MESSAGE"', 'ID') == 'ID':
            param = self.param(message)
            self._scan('";"')
        self._scan('"END MESSAGE"')
        MOD.add_message(message)

    def param(self, MSG):
        ID = self._scan('ID')
        param_type=ID
        is_pointer=0
        if self._peek('"\\\\*"', 'ID') == '"\\\\*"':
            self._scan('"\\\\*"')
            is_pointer=1
        ID = self._scan('ID')
        check_param_case(self._scanner,ID)
        param = Param(ID,param_type,is_pointer,MSG)
        if self._peek('"\\\\["', '","', '";"') == '"\\\\["':
            self._scan('"\\\\["')
            _token_ = self._peek('ID', 'NUM')
            if _token_ == 'ID':
                ID = self._scan('ID')
                param.set_vector_size(ID)
            else:# == 'NUM'
                NUM = self._scan('NUM')
                param.set_vector_size(NUM)
            self._scan('"\\\\]"')
        MSG.add_param(param)
        while self._peek('","', '";"') == '","':
            self._scan('","')
            is_pointer=0
            if self._peek('"\\\\*"', 'ID') == '"\\\\*"':
                self._scan('"\\\\*"')
                is_pointer=1
            ID = self._scan('ID')
            check_param_case(self._scanner,ID)
            param = Param(ID,param_type,is_pointer,MSG)
            MSG.add_param(param)

    def timeunit(self, N):
        _token_ = self._peek('"ms"', '"us"', '"ns"')
        if _token_ == '"ms"':
            self._scan('"ms"')
        elif _token_ == '"us"':
            self._scan('"us"')
        else:# == '"ns"'
            self._scan('"ns"')


def parse(rule, text):
    P = sycomp(sycompScanner(text))
    return wrap_error_reporter(P, rule)





if __name__ == '__main__':
    from sys import argv, stdin
    print ""
    print "syscompiler v1.00 (c) 2013, NBEE Embedded Systems SL"
    print ""
    if len(argv) >= 2:
        f = open(argv[1],'r')
        parse("system", f.read())
    else:
        print 'Args:  [<filename>]'
    print ""


