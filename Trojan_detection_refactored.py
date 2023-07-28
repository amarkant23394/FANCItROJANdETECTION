from FANCI_TROJAN_DETECTION_REFACTORED.per_node_subcircuit_maker import PerNodeSubCircuitMaker
from FANCI_TROJAN_DETECTION_REFACTORED.format_per_node_subcircuit_data import FormatPerNodeSubCircuit
from FANCI_TROJAN_DETECTION_REFACTORED.Comb_TestBench_Generator import Combinational_TestBench_Generator
from FANCI_TROJAN_DETECTION_REFACTORED.Seq_TestBench_Generator import Sequential_TestBench_Generator
from FANCI_TROJAN_DETECTION_REFACTORED.Verilog_Simulation import Verilog_Simulation
from FANCI_TROJAN_DETECTION_REFACTORED.generate_input_tb_remastered import GenerateInputTb
import os
import sys
import numpy as np
import statistics


class FanciTrojanDetection:

    clockPattern="CLK|clock|clk|CK"
    resetPattern="rst|reset|RST|Rst|RN|RSTB"

    def mean_vec(self,vec_cntrl_val):
        return np.mean(vec_cntrl_val)

    def median_vec(self,vec_cntrl_val):
        return statistics.median(vec_cntrl_val)

    def triviality_vec(self,vec_output_val):
        zero_encounter = 0
        for vec_ele in vec_output_val:
            if vec_ele == 0:
                zero_encounter += 1

        zero_prob = zero_encounter/len(vec_output_val)
        if zero_prob >= 0.5:
            return (1.0-zero_prob,zero_encounter,len(vec_output_val))
        
        return (zero_prob,zero_encounter,len(vec_output_val))

    def __init__(self,input_cone_depth,input_file_directory,output_top_directory,mean_median_threshold,trivial_threshold):
        PerNodeSubCircuitMaker(input_cone_depth,input_file_directory,output_top_directory);
        FormatPerNodeSubCircuit(output_top_directory)
        self.generate_simulated_file(output_top_directory,mean_median_threshold,trivial_threshold)

    def generate_simulated_file(self,input_path,mean_median_threshold,trivial_threshold):
        for subdir, dirs, files in os.walk(input_path):
                for file in files:
                    subdir_top_directory = "/".join(subdir.split("/")[:-1])
                    print(subdir_top_directory)
                    verilog_file_path = os.path.join(subdir, file)
                    node_name = file[:-2]

                    tb_random_input_file_path = subdir_top_directory + "/input_tb.txt"
                    print(tb_random_input_file_path)
                    tb_file_path = subdir_top_directory + "/testbench_common_file.sv"
                    print(tb_file_path)
                    simulated_output_file_path = subdir_top_directory + "/simulated_data_output.txt"
                    print(simulated_output_file_path)
                    logfile_path = subdir_top_directory+"/log_file.txt"
                    print(logfile_path)
                    print(node_name)

                    unformatted_lines = []
                    with open(verilog_file_path,'r')as fp_file:
                        unformatted_lines = fp_file.readlines()

                    module_name = ""
                    input_size = 0
                    is_sequential = False
                    for index,line in enumerate(unformatted_lines):
                        line = line.lstrip()
                        if line.startswith('module'):
                            module_term = line.split(" ")[0]
                            remaining = " ".join(line.split(" ")[1:])
                            module_name = remaining.split("(")[0]

                        if line.startswith('input'):
                            input_term = line.split(" ")[0]
                            remaining = " ".join(line.split(" ")[1:])
                            nodes_list = remaining.split(",")
                            for node_inst in nodes_list:
                                for clock_name in FormatPerNodeSubCircuit.clockPattern.split("|"):
                                    if node_inst.endswith(clock_name):
                                        is_sequential = True
                                        break

                                for rst_name in FormatPerNodeSubCircuit.resetPattern.split("|"):
                                    if node_inst.endswith(rst_name):
                                        is_sequential = True
                                        break

                            if is_sequential == True:
                                input_size = len(nodes_list) - 2
                            else:
                                input_size = len(nodes_list)

                        if module_name != "" and input_size != 0:
                            break
                    
                    if input_size <= 0:
                        continue

                    GenerateInputTb(verilog_file_path,input_size,subdir_top_directory)

                    if is_sequential == True:
                        Sequential_TestBench_Generator(tb_random_input_file_path,tb_file_path,simulated_output_file_path,input_size,1,module_name)
                    else:
                        Combinational_TestBench_Generator(tb_random_input_file_path,tb_file_path,simulated_output_file_path,input_size,1,module_name)

                    Verilog_Simulation(verilog_file_path,tb_file_path,logfile_path)
                    self.heuristics_calculation_from_simulated_output(node_name,subdir_top_directory,mean_median_threshold,trivial_threshold)
                    os.remove(simulated_output_file_path)

                    ##########HEURISTICS CALCULATION#####################

    def heuristics_calculation_from_simulated_output(self,node_name,output_top_directory,mm_threshold,tri_threshold):
        simulated_output_file_path = simulated_output_file_path = output_top_directory + "/simulated_data_output.txt"
        print(simulated_output_file_path)

#        if not os.path.exists(simulated_output_file_path):
#            return

        random_select_file_path = output_top_directory +"/random_input_tb.txt"
        simulated_output_lines = []
        with open(simulated_output_file_path,'r')as fp_file:
            simulated_output_lines = fp_file.readlines()

        #calculating no of inputs
        no_of_inputs = simulated_output_lines[0].split(" ")[0]
        no_of_inputs = len(no_of_inputs)

        control_vector = np.zeros((no_of_inputs,), dtype=float)
        output_dict = {}
        input_multi_vector = np.zeros((len(simulated_output_lines),no_of_inputs), dtype=int)

        for index,simulated_data in enumerate(simulated_output_lines):
            dict_value = int((simulated_data.split(" ")[1]).rstrip("\n"))
            dict_key = (simulated_data.split(" ")[0]).lstrip("")
            output_dict[dict_key] = dict_value 

#        if no_of_inputs > 15:
#            random_select_nums = []
#            with open(random_select_file_path,'r')as fp_file:
#                random_select_file_lines = fp_file.readlines()
#
#            for ran_ele in random_select_file_lines:
#                random_select_nums.append(int(ran_ele))
#
#            for pin_index in range(no_of_inputs-1, -1, -1):
#                control_value_sum = 0
#                control_div_value = 0
#                for i in random_select_nums:
#                    key_ele = '{i:0>{n}b}'.format(i=i, n=no_of_inputs)
#
#                    temp_key = key_ele
#                    if key_ele[pin_index] == '0':
#                        temp_key = temp_key[:pin_index] + '1' + temp_key[pin_index+1:]
#                    else:
#                        temp_key = temp_key[:pin_index] + '0' + temp_key[pin_index+1:]
#
#                    x_zero = output_dict[key_ele]
#                    x_one =  output_dict[temp_key]
#
#                    control_div_value += 1
#
#                    if x_zero != x_one:
#                        control_value_sum += 1
#
#                control_vector[pin_index] = float(control_value_sum)/float(control_div_value)
#
#        else:
#            for pin_index in range(no_of_inputs-1, -1, -1):
#                control_value_sum = 0
#                control_div_value = 0
#                for key_ele in output_dict.keys():
#                    if key_ele[pin_index] == '1':
#                        continue
#
#                    temp_key = key_ele[:pin_index] + '1' + key_ele[pin_index+1:]
#
#                    x_zero = output_dict[key_ele]
#                    x_one =  output_dict[temp_key]
#
#                    control_div_value += 1
#
#                    if x_zero != x_one:
#                        control_value_sum += 1
#
#                control_vector[pin_index] = float(control_value_sum)/float(control_div_value)
#        
#        mean_value = self.mean_vec(control_vector)
#        median_value = self.median_vec(control_vector)
        triviality_value,zero_prob_val,total_inputs_val = self.triviality_vec(list(output_dict.values()))

        final_output_path = output_top_directory + "/"

        final_output_file_path_mean = final_output_path+"mean.txt"
        final_output_file_path_median = final_output_path+"median.txt"
        final_output_file_path_triv = final_output_path+"triv.txt"
        final_output_file_path_prob = final_output_path+"_prob.txt"
        with open(final_output_file_path_prob,'a')as fp_file:
            fp_file.write(node_name)
            fp_file.write(" ")
            fp_file.write(str(triviality_value)) 
            fp_file.write(" ")
            fp_file.write(str(zero_prob_val)) 
            fp_file.write(" ")
            fp_file.write(str(total_inputs_val))            
            fp_file.write("\n")

#        if mean_value < mm_threshold:
#            with open(final_output_file_path_mean,'a')as fp_file:
#                fp_file.write(node_name)
#                fp_file.write("\n")
#
#        if median_value < mm_threshold:
#            with open(final_output_file_path_median,'a')as fp_file:
#                fp_file.write(node_name)
#                fp_file.write("\n")
#
        if triviality_value < tri_threshold:
            with open(final_output_file_path_triv,'a')as fp_file:
                fp_file.write(node_name)
                fp_file.write("\n")
                        

FanciTrojanDetection(5,sys.argv[1],sys.argv[2],0.1,0.09)
