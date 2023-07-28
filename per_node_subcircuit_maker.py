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
import shutil

class PerNodeSubCircuitMaker:

    clockPattern="CLK|clock|clk|CK"
    resetPattern="rst|reset|RST|Rst|RN|RSTB"
    single_input_gates = ["NOT","BUF","INV","CLKBUF","INPUT"]

    def topological_sort_sequential_circuit(self, graph):
        """
        Performs topological sorting on a sequential circuit represented as a NetworkX graph.

        Args:
            graph (networkx.DiGraph): The graph representing the sequential circuit.

        Returns:
            List: The topologically sorted list of nodes.
        """
        visited = set()
        sorted_nodes = []

        def dfs(node):
            if node in visited:
                return
            visited.add(node)

            for successor in graph.successors(node):
                dfs(successor)

            sorted_nodes.append(node)

        for node in graph.nodes:
            dfs(node)

        return list(reversed(sorted_nodes))

    def __init__(self,input_cone_depth,input_file_directory,output_top_directory):
        sub_circuit_top_directory = output_top_directory

        for filename in os.listdir(output_top_directory):
            file_path = os.path.join(output_top_directory, filename)
            if os.path.isfile(file_path):
                os.remove(file_path)

        # Remove all subdirectories and their contents within the folder
        for root, directories, files in os.walk(output_top_directory, topdown=False):
            for directory in directories:
                dir_path = os.path.join(root, directory)
                shutil.rmtree(dir_path)

        sys.setrecursionlimit(5000)
        for file_path in pathlib.Path(input_file_directory).iterdir():
            if file_path.is_file():
                input_f_path_str = str(file_path)
                print("Reading file = ",file_path)

                output_folder = str(pathlib.Path(file_path).name)
                output_folder = output_folder[:-2]

                #NT NODE SUBCIRCUITS
                sub_circuit_output_path_str = ""
                sub_circuit_output_path_str += sub_circuit_top_directory + "/"+ output_folder + "/Nt_Node_Subcircuits/"

                # Create target Directory if don't exist
                if not os.path.exists(sub_circuit_output_path_str):
                    os.makedirs(sub_circuit_output_path_str)

                for f in os.listdir(sub_circuit_output_path_str):
                    os.remove(os.path.join(sub_circuit_output_path_str, f))
                ######################################

#                i_graph_obj = verilog_parsing.ReadVerilog(input_f_path_str)     #parsing the verilog file of benchmark and convert it into graph object
                i_graph_obj = Ver2Nx(input_f_path_str)
                d_graph_obj = i_graph_obj.getGraph()
#                d_graph_obj = i_graph_obj.getGraph()
                graph_nodes = d_graph_obj.nodes()
                graph_node_attributes=nx.get_node_attributes(d_graph_obj,'type')
                
#                print("TOPOLOGICAL SORT BEFORE")
                for node_name in self.topological_sort_sequential_circuit(d_graph_obj):
                    print("Started Node = ",node_name," Gate type = ",graph_node_attributes[node_name])
                    if graph_node_attributes[node_name].lower() != "input":
                        if input_cone_depth == 0:
                            pair_node_list = list(nx.bfs_edges(d_graph_obj,node_name,reverse=True))
                        else:                        
                            pair_node_list = list(nx.bfs_edges(d_graph_obj,node_name,reverse=True,depth_limit=input_cone_depth))
#                        print("LEN OF NODES CONNECTED REVERSE = "+str(len(pair_node_list)))
                        if len(pair_node_list) <= 1:
                            continue
                        node_list = []                
                        node_list.append(node_name)
                        for m,n in pair_node_list:
                            node_list.append(n)

                        for dff_node_name in node_list:
                            if graph_node_attributes[dff_node_name].lower() == "dff":
                                for dff_fanin in d_graph_obj.predecessors(dff_node_name):
                                    node_list.append(dff_fanin)
                                    if graph_node_attributes[dff_fanin].lower() == "not":
                                        for reset_input_pred in d_graph_obj.predecessors(dff_fanin):
                                            node_list.append(reset_input_pred)

                        node_list = list(set(node_list))
                        print("Sub Graph list node made")
                        SG = d_graph_obj.subgraph(node_list)
                        sub_graph_node_attributes=nx.get_node_attributes(SG,'type')
                        SG = nx.DiGraph(SG)

                        clk_list_name = []
                        rst_list_name = []
                        no_of_sub_inputs = 0
                        rst_input_name = []

                        sub_cir_input_nodes_list = [u for u, deg in SG.in_degree() if not deg]

                        for node_inst_dict in sub_graph_node_attributes:
                            sub_node_name = str(node_inst_dict)
                            for clock_name in PerNodeSubCircuitMaker.clockPattern.split("|"):
                                if sub_node_name.endswith(clock_name):
                                    clk_list_name.append(sub_node_name)
                                    break

                            for rst_name in PerNodeSubCircuitMaker.resetPattern.split("|"):
                                if sub_node_name.endswith(rst_name):
                                    rst_list_name.append(sub_node_name)
                                    if node_inst_dict in sub_cir_input_nodes_list:
                                        rst_input_name.append(sub_node_name)

                                    for inst_rst in SG.predecessors(rst_list_name[-1]):
                                        if sub_graph_node_attributes[inst_rst] == "NOT":
                                            rst_list_name.append(inst_rst)

                        no_of_sub_inputs = len(sub_cir_input_nodes_list)
                        no_of_sub_inputs -= len(clk_list_name) 
                        no_of_sub_inputs -= len(rst_input_name)       
                        inst_dff_dict = {}
                        inst_dff_dict["CLOCK"] = clk_list_name
                        inst_dff_dict["RESET"] = rst_list_name

                        SG_graph_nodes = list(SG.nodes)
                        SG_str_input = "IN_"
                        SG_input_count = 1
                        SG_clk_rst_node_created = False
                        SG_clk_node_name = "clk_input_n"
                        SG_rst_node_name = "rst_input_n"
                        SG_rst_successor_node_name = "rst_connected_not_n"
                        for SG_node_ele in SG_graph_nodes:
                            SG_node_list = list(nx.bfs_edges(SG,SG_node_ele,reverse=True))[:2]
                            SG_len_node_list = 0
                            for SG_check_node_list in SG_node_list:
                                for SG_check_node in SG_check_node_list:
                                    if SG_check_node == SG_node_ele:
                                        SG_len_node_list+=1

        #                    input_check = 0
        #                    if node_attributes[node_ele] == "INPUT":
        #                        input_count+=1
        #                        continue
                            SG_ref_input_node_count = 0
                            if sub_graph_node_attributes[SG_node_ele] in PerNodeSubCircuitMaker.single_input_gates:
                                SG_ref_input_node_count = 1
                            else:
                                SG_ref_input_node_count = 2

                            if sub_graph_node_attributes[SG_node_ele].lower() == "input":
                                continue
                
                            if sub_graph_node_attributes[SG_node_ele].lower() == "dff":
                                if SG_len_node_list < 1:
                                    SG.add_node((SG_str_input+str(SG_input_count)), type = "IN")
                                    SG.add_edge((SG_str_input+str(SG_input_count)),SG_node_ele)
                                    SG_input_count+=1
#                                if clk_rst_node_created == False:
#                                    clk_rst_node_created = True 
#                                    graph_obj.add_node(clk_node_name, type = "IN")  
#                                    graph_obj.add_node(rst_node_name, type = "IN")
#                                    if reset_active_low == True:
#                                        graph_obj.add_node(rst_successor_node_name, type = "NOT")
#                                        graph_obj.add_edge(rst_node_name,rst_successor_node_name)
#                                graph_obj.add_edge(clk_node_name,node_ele)
#                                if reset_active_low == True:
#                                    graph_obj.add_edge(rst_successor_node_name,node_ele)
#                                else:
#                                    graph_obj.add_edge(rst_node_name,node_ele)
                            else:    
                                for loop_count in range(SG_ref_input_node_count-SG_len_node_list):
                                    SG.add_node((SG_str_input+str(SG_input_count)), type = "IN")
                                    SG.add_edge((SG_str_input+str(SG_input_count)),SG_node_ele)
                                    SG_input_count+=1  

#                        if no_of_sub_inputs > 55:
#                            continue
                            

                        #########VERILOG SUB FILE#######
                        sub_circuit_verilog_file_path = sub_circuit_output_path_str +"/"+str(node_name)+".v"
                        sub_circuit_module_name = "test_"+str(node_name)
                        Networkx2Verilog(SG,sub_circuit_module_name, sub_circuit_verilog_file_path, mode = "w")#,d_ff_dict = inst_dff_dict)
                        ################################                 


