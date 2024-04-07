import pandas as pd
import os
import json

def load_json(file_path):
    with open(file_path, 'r') as file:
        data = json.load(file)
        return data

def check_method_level(method_code, ground_method_truth):
    if len(ground_method_truth) == 0:
        return "no ground truth method"
    if len(ground_method_truth) > 0:
        function_name = ground_method_truth.split('.')[-1]
        function_name = function_name[:function_name.index('(')]
    if len(method_code) == 0:
        return "cannot locat method"
    if function_name in method_code:
        return "True"
    else:
        return "False"
    
def check_file_level(file_name, ground_method_truth, if_has_bug):
    if len(ground_method_truth) > 0:
        ground_file_name = ground_method_truth.split('.')[-2]
        if if_has_bug == "Yes":
            if ground_file_name in file_name:
                return "True"
            else:
                return "False"
        else:
            if ground_file_name in file_name:
                return "False"
            else:
                return "True"
    else:
        return "no ground truth method"

def check_block_level(block_code, bug_id):
    pass


ground_truth_lines = '../dataset/localization_groudtruth/buggy-lines'
ground_truth_methods = '../dataset/localization_groudtruth/buggy-methods/'
projects = ['Lang']
dicts = []
for project in projects:
    localizatin_file_path = "../analysis_result/GPT_response/fault_location/Lang/"
    for filename in os.listdir(localizatin_file_path):
        if filename.endswith(".json"):
            bug_id = filename.split(".")[0]
            ground_truth_line_path = os.path.join(ground_truth_lines, f"{bug_id}.buggy.lines".replace('_', "-"))
            ground_truth_method_path = os.path.join(ground_truth_methods, f"{bug_id}.buggy.methods".replace('_', "-"))
            method_ground_truth = pd.read_csv(ground_truth_method_path, delimiter=',', header=None, names=['method', 'value'])
            method_ground_truth = method_ground_truth[method_ground_truth['value'] == 1]
            falut_localization_info = load_json(localizatin_file_path + filename)
            falut_localization_info['Bug_ID'] = filename.split('.')[0]
            falut_localization_info['Ground_Method_Truth'] = ",".join(method_ground_truth['method'])
            dicts.append(falut_localization_info)

fault_df = pd.DataFrame(dicts)
fault_df['Locate Correct Method'] = fault_df.apply(lambda row: check_method_level(row['method_level'], row['Ground_Method_Truth']), axis=1)
fault_df['Locate Correct File'] = fault_df.apply(lambda row: check_file_level(row['file_name'], row['Ground_Method_Truth'], row['if_has_bug']), axis=1)
fault_df.to_csv("../analysis_result/evaluation/fault_location_eval.csv", index=False)
right_method_df = fault_df[fault_df['Locate Correct Method'] == 'True']
right_file_df = fault_df[fault_df['Locate Correct File'] == 'True']
print("File level accuracy:" + str(len(right_file_df)/ len(fault_df)))
print("Method Level accuracy: " + str(len(right_method_df) / len(fault_df)))