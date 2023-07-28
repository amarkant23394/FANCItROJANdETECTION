# -*- coding: utf-8 -*-
"""
Created on Mon Nov  8 10:01:00 2021

@author: saxen
"""

import os 
import logging
import sys

#For reading the files
def filereading(filename):
    try:
        fp = open(filename,"r")
        lines = fp.readlines()
        fp.close()
    except: 
        logging.error("{} doesnot exsits".format(filename))
        sys.exit()
    return lines 

class Sequential_TestBench_Generator:
    def __init__(self,input_file,testbench_file,output_file,input_size,output_size,topcellname):
        logging.info("Started")
        lines = filereading(input_file)
        fp = open(testbench_file,"w")
        fp.write("module tb_{};\n".format(topcellname))
        fp.write("reg [0:{}] N;\n".format(input_size-1))
        fp.write("reg CK, reset;\n")
        fp.write("bit [0:{}] output_single;\n".format(output_size-1))
        fp.write("integer i,f;\n")
        string = []
        for i in range(0,input_size):string.append("N[{}]".format(i))
        string.append("CK, reset")
        for j in range(0,output_size):string.append("output_single[{}]".format(j))
        string = ",".join(string)
        fp.write( "{} U1 ({});\n".format(topcellname,string))
        fp.write("initial \n")
        fp.write("begin\n")
        fp.write("    CK = 0;\n")
        fp.write("end\n")
        fp.write("always #5 CK = ~CK;\n")
        fp.write("initial\n")
        fp.write("begin\n")
        fp.write("  reset = 1;\n")
        fp.write("  #5;\n")
        fp.write("  reset = 0;\n")
        fp.write("end\n")
        fp.write("always @(posedge CK)\n")
        #fp.write("initial\n")
        fp.write("begin\n")
        fp.write('f = $fopen("{}","w");\n'.format(output_file))
        fp.write("#2\n")
        for i in range(len(lines)):
            fp.write("N = {}'b{};\n#10\n".format(input_size,lines[i].strip()))
            fp.write('$fwrite(f,"%b %b\\n",N,output_single);\n')
        fp.write("$fclose(f);\n")
        fp.write("$finish;\n")
        fp.write("end\n")
        fp.write("endmodule")
        fp.close()
        logging.info("Ended")
