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
%%
parser sycomp:
	ignore:	"[\t\n\r ]+"
    ignore: "//.*\n"
	token ID: "[a-zA-Z_][a-zA-Z_0-9]*"
    token FILENAME: "[a-zA-Z_\\.][a-zA-Z_0-9\\.]*"
	token VAL: ".*"
	token NUM: "[0-9]+"
	
	rule system: "SYSTEM" ID {{	system = System(ID)  }}
            ["PRIORITY" ID (">" ID)* ]
            ["FILEPREFIX" ID {{ system.set_file_prefix(ID) 	}}] 
            
            [ ('CREATE' FILENAME            {{ f_create=open(FILENAME,'w') }}
                ( VAL {{ f_create.write(VAL+"\n") }} ) *  
               'END CREATE' {{ f_create.close() }}
               )+
            ]
            [
              'CODE'
		      ( VAL 	{{system.add_c_def(VAL) }})*
		      'END CODE'
		    ]
	
		     (module<<system>>
		     	
		      )*
		   "END" ID "." {{ check_sys_name(self._scanner,system.name,ID) }}
		   		{{ system.process() }}
		   
	rule module<<SYS>>: 
            "TASK" ID  {{	module = Module(ID,SYS)  		}}
             ["PERIOD" NUM timeunit<<NUM>>]
             ["LOAD" NUM timeunit<<NUM>>]
		     ["FILEPREFIX" ID {{ module.set_file_prefix(ID) 	}} ]
		     
		     ["USES" ID        {{ module.use_module(ID) 	}}
		      ("," ID	       {{ module.use_module(ID)		}}
		      )*
		     ]
		     
		     [
              'CODE'
		      ( VAL 	{{ module.add_c_def(VAL) }})*
		      'END CODE'
		     ]
		     
		     
		     (message<<module>>)*
		     
		     "END" ID	  {{ check_task_name(self._scanner, module.name, ID) }}  
                          {{ SYS.add_module(module) }}      
                
	
	rule message<<MOD>>: "MESSAGE" ID {{ message=Message(ID,MOD) }}
                [ "FROM"  ID        {{ message.add_src(ID) 	}}
                ("," ID	       {{ message.add_src(ID)		}}
                    )*
                ]
		      	(
		      	 
		      	 param<<message>> ";"
		      	)*
                
		      "END MESSAGE" 
               {{ MOD.add_message(message) }}
		      
	rule param<<MSG>>:   ID {{ param_type=ID    }}
                              {{ is_pointer=0       }}
		      [ "\\*" {{ is_pointer=1 }} ]
              ID    {{ check_param_case(self._scanner,ID) }}
                    {{ param = Param(ID,param_type,is_pointer,MSG) }}
		      [
		       "\\["
		       (   ID {{ param.set_vector_size(ID) }}
		         | NUM {{ param.set_vector_size(NUM) }}
		        )
		       "\\]"
		       ] {{ MSG.add_param(param) }}
               (
                "," {{ is_pointer=0 }}
                [ "\\*" {{ is_pointer=1 }} ]
                ID  {{ check_param_case(self._scanner,ID)   }}
                    {{ param = Param(ID,param_type,is_pointer,MSG)     }}
                    {{ MSG.add_param(param)                 }}
                )*
rule timeunit<<N>>:         "ms"    
                        |   "us"
                        |   "ns"
                    
		      
%%


if __name__ == '__main__':
    from sys import argv, stdin
    if len(argv) >= 2:
        f = open(argv[1],'r')
        parse("system", f.read())
    else:
        print 'Args:  [<filename>]'		

      	