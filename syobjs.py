#-----------------------------------------------------------------------------
# Name:        syobjs.py
# Purpose:     Parser classes for syscompiler
#
# Author:      Miguel Angel Ajo Pelayo
#
# Created:     2005/29/07
# RCS-ID:      $Id: syobjs.py $
# Copyright:   (c) 2004
# Licence:     GNU Public License (GPL)
#----------------------------------------------------------------------------
import os

class Code:
    def __init__(self):
        self._code = ""

    def add(self,line):
        self._code = self._code + line + "\n"

    def add_code(self,code):
        self._code = self._code + code.string()

    def string(self):
        return self._code

# class defining the system ####################################################
class System:
    def __init__(self,name):
        self.name = name
        self.modules=[]
        self.file_prefix=""
        self.c_defs=[]


    def add_module(self,module):
    	self.modules.append(module)

    def find_module(self,name):
        for module in self.modules:
            if module.name==name:
                return module
        return None

    def add_c_def(self,c_def):
    	self.c_defs.append(c_def)

    def check_name(self,name):
        if self.name!=name:
            print "Error: " + name + " it's not the name for the system (" + \
                self.name + ")"
            return None
        else:
            return self


    def build_h_files(self):
            # for every module
            for module in self.modules:
                filename_h=module.get_filename()+".h"
                print " * generating "+filename_h
                # write the .h file to disk (overwriting)
                file_h = open(filename_h, 'w' )
                # write synthetized code
                file_h.write(module.synth_h())
                file_h.close()

    def build_gv_file(self):
        code = Code()

        code.add("digraph %s {"%self.name)

        code.add("rankdir=LR;")
        code.add("\tnode [shape = circle];")

        for module in self.modules:
            module.add_gv_transitions(code)


        code.add("}")
        print " * generating "+self.name+".gv"
        file_gv = open(self.name+".gv",'w')
        file_gv.write(code.string())
        file_gv.close()

        print " * generating %s" %(self.name+".svg")
        os.system("dot %s -Tsvg -o %s"%(self.name+".gv",self.name+".svg"))

    def process(self):
        self.build_h_files()
        self.build_gv_file()

    def set_file_prefix(self,prefix):
    	self.file_prefix = prefix

# class defining a module inside the system ####################################
class Module:
    def __init__(self,name,system):
        self.name = name
        self.used_module_names = []
        self.used_modules = []
        self.messages = []
        self.c_defs = []
        self.file_prefix=""
        self.system=system

    def set_file_prefix(self,prefix):
    	self.file_prefix = prefix

    def use_module(self,name):
    	self.used_module_names.append(name)

    def resolve_used_modules(self):
        self.used_modules = []
        # resolve used modules
        for name in self.used_module_names:
            module=self.system.find_module(name)
            if module!=None:
                self.used_modules.append(module)
            else:
                print "Error: unknown module "+name+" used from "+self.name
        # resolve src of messages
        for message in self.messages:
                message.resolve_src_modules()

    def add_c_def(self,c_def):
    	self.c_defs.append(c_def)

    def add_message(self,message):
    	self.messages.append(message)

    def get_filename(self):
        if self.file_prefix!="":
            return self.file_prefix+self.name
        else:
            return self.system.file_prefix+self.name

    def add_gv_transitions(self,code):
        for message in self.messages:
            message.add_gv_transition(code)

    def synth_h(self):
        # first resolve used module references
        self.resolve_used_modules()

        # get filename
        filename = self.get_filename()
        filename_H = "__"+filename.upper()+"_H"


        # generate synthetized code
        code = Code()
        code.add("//")
        code.add("// syscompiler: autogenerated file")
        code.add("// DON'T EDIT THIS FILE")
        code.add("//")
        code.add("#ifndef " + filename_H)
        code.add("#define " + filename_H)
        code.add("")
        code.add("")

        # insert system includes / defines
        if self.system.c_defs!=[]:
            for incl in self.system.c_defs:
                code.add(incl)
            code.add("")

        # insert includes for used modules
        if self.used_modules!=[]:
            for mod in self.used_modules:
                code.add("#include \""+mod.get_filename()+".h\"")
            code.add("")


        # insert module includes /defines
        if self.used_modules!=[]:
            for incl in self.c_defs:
                code.add(incl)
            code.add("")

        # generate every message variables
        for message in self.messages:
            code.add("//")
            froms="FROM "
            for module in message.src_names:
                    froms=froms + module +" "

            code.add("// MESSAGE " + message.get_msg_var()+" "+froms)
            code.add("//")
            code.add("")
            code.add_code(message.get_code(".h"))
            code.add("")

        code.add("void " + self.get_filename() + "_init();")
        code.add("void " + self.get_filename() + "();")
        code.add("")
        code.add("#endif")
        code.add("")

        # return synthetized code
        return code.string()


# class defining a message inside the module ###################################

class Message:
    def  __init__(self,name,module):
        self.name = name
        self.params = []
        self.src_names = []
        self.src_modules =[]
        self.module=module

    def add_src(self,name):
    	self.src_names.append(name)

    def resolve_src_modules(self):
        self.used_modules = []
        for name in self.src_names:
            module=self.module.system.find_module(name)
            if module!=None:
                self.src_modules.append(module)
            else:
                print "Error: unknown module "+name+" src of  "+self.get_msg_var()


    def get_msg_var(self):
        return self.module.name + "_" + self.name;

    def add_param(self,param):
    	self.params.append(param)

    def add_gv_transition(self,code):
        for src in self.src_names:
            code.add("\t"+src + " -> " + self.module.name + "\t[ label=\""+self.name+self.get_params_l()+"\" ];")


    def get_params_l(self):
        line = "("

        for param in self.params:
            line = line + param.name +", "

        if self.params!=[]:
            line = line [:len(line)-2]

        line = line + ")"
        return line

    def get_code(self,kind):        # kind = ".c" | ".h"
        code = Code()

        if kind==".h":
            code.add("extern bool " + self.get_msg_var() + "_flag;")

            for param in self.params:
                code.add_code(param.get_code("extern",self.get_msg_var()))

            code.add("")

            line = "#define CLEAR_MSG_" + self.get_msg_var().upper()
            line = line + "() "+ self.get_msg_var() +"_flag = false\n"
            code.add(line)

            code.add("")

            # generate macro for message passing

            #example of what we want to generate:
            ##define display_msg(T,DATA,DATA_LEN)	\\
            #   display_msg_T = T;			\\
            #   memcpy(display_msg_DATA,DATA,DATA_LEN); \\
            #   display_msg_DATA_LEN=DATA_LEN; 		\\
            #   display_msg_flag = true

            line = "#define "+self.get_msg_var()+"("
            for param in self.params:
                line = line + param.name +", "
                if param.type=="string":
                    line = line + param.name +"_LEN, "

            # remove last comma and space ", "
            if self.params!=[]:
                line = line [:len(line)-2]
            line = line + ")\t\\\\"

            code.add(line)

            # parameter filling for the macro
            n = 1
            last_n = len(self.params)
            code_param = ""
            for param in self.params:
                code_param = code_param + "\t"
                code_param = code_param + param.get_filling(self.get_msg_var())
                if n!=last_n:
                    code_param = code_param + ";\t\\\\\n"
                else:
                    code_param = code_param + ";\t\\\\"
                n = n + 1

            code.add(code_param)
            code.add("\t"+self.get_msg_var()+"_flag = true")



        else:
            code.add("bool " + self.get_msg_var() + ";")
            for param in self.params:
                code.add_code(param.get_code("",self.get_msg_var()))


        return code

# class defining a param inside the message ####################################

class Param:
    def __init__(self,name,type,is_pointer,message):
    	self.name = name
    	self.type = type
        self.vector_size = []
        self.message = message
        self.is_pointer=is_pointer

    def set_vector_size(self,vsize):
    	self.vector_size = vsize

    def get_vector_string(self):
        if self.vector_size!=[]:
            return "[" + self.vector_size +"]"
        else:
            return ""

    def get_string(self,varprefix):
    	return self.type + " " + varprefix  + self.name + self.get_vector_string()


    def get_code(self,prefix,varprefix):
        code = Code()
        if self.is_pointer:
            pointer = "*"
        else:
            pointer = ""

        varprefix = varprefix + "_"
        if self.type=="string":
            code.add(prefix+" byte " + pointer + varprefix + self.name+self.get_vector_string()+";")
            code.add(prefix+" byte " + varprefix + self.name + "_LEN;")
        else:
            code.add(prefix+" " + pointer + self.get_string(varprefix) +";")

        return code

    def get_filling(self,varprefix):
        varprefix = varprefix +"_"
        if self.type=="string":
            if self.is_pointer:
                # for a pointer copy it, and copy the LEN
                code = varprefix+self.name+" = "+self.name + "\t\\\\\n";
                code = code + varprefix+self.name+"_LEN = "+self.name+"_LEN"
            else:
                # for a normal string, do a memcpy, and copy the LEN
                code = "memcpy("+varprefix+self.name+","+self.name+","
                code = code + self.name +"_LEN);\t\\\\\n\t"
                code = code + varprefix+self.name+"_LEN = "+self.name+"_LEN"
        else:
                # for any other kind just do the assignment
                code = varprefix + self.name +" = "+self.name

        return code



