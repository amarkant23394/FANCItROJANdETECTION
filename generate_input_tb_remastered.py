"""
@author: M.Satya Amarkant
Project Name : Benchmark Generator using Attributed Graph Grammar
Description : 
"""

from numpy import equal
from ver_to_nx import Ver2Nx
import networkx as nx
import pathlib
import json
import itertools
import matplotlib.pyplot as plt
import sys
import os
from Networkx2Verilog import Networkx2Verilog 
import NX2Verilog
from pprint import pprint as pp
import random

class GenerateInputTb:
    def __init__(self,input_verilog_file,no_of_sub_inputs,output_top_directory):
        if no_of_sub_inputs <= 0:
            no_of_sub_inputs = 0
        #########INPUT FOR TB FILE########
        sub_circuit_tb_input_file_path = output_top_directory +"/input_tb.txt"

        if no_of_sub_inputs <= 15:   
            with open(sub_circuit_tb_input_file_path,'w')as fp_rule_file:
                n = no_of_sub_inputs
                for i in range(2**n):
                    fp_rule_file.write(str('{i:0>{n}b}'.format(i=i, n=n)))
                    fp_rule_file.write("\n")
        else:
            random_select_num_file_path = output_top_directory +"/random_input_tb.txt"
            n_of_input_bits = no_of_sub_inputs
            no_of_inputs_to_be_selected = 15
            list_of_random_num = set()

            while len(list_of_random_num) < (2**no_of_inputs_to_be_selected):
                generated_number = random.getrandbits(n_of_input_bits)
                list_of_random_num.add(generated_number)

            list_of_random_num = list(list_of_random_num)
            list_of_random_num.sort()
            dict_nums = {}
            select_index = 0
            for i in list_of_random_num:
                key_ele = '{i:0>{n}b}'.format(i=i, n=n_of_input_bits)
                dict_nums[key_ele] = 0

#            list_of_random_selects = dict_nums.copy().keys() 
#            for key_ele in list_of_random_selects:
#                for pin_index in range(n_of_input_bits-1, -1, -1):
#                    temp_key = key_ele
#                    if key_ele[pin_index] == '0':
#                        temp_key = temp_key[:pin_index] + '1' + temp_key[pin_index+1:]
#                    else:
#                        temp_key = temp_key[:pin_index] + '0' + temp_key[pin_index+1:]
#                    dict_nums[temp_key] = 0
#
#            with open(random_select_num_file_path,'w')as fp_rule_file:
#                for e in list_of_random_num:
#                    fp_rule_file.write(str(e))
#                    fp_rule_file.write("\n")
#
            with open(sub_circuit_tb_input_file_path,'w')as fp_rule_file:
                for key_ele in sorted(dict_nums.keys()):
                    fp_rule_file.write(key_ele)
                    fp_rule_file.write("\n")
            


        ##################################

        print("Finished")


