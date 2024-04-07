import os
import json

def find_modify_code_line_in_project(source_code_path, patch_file_path):
    modify_lines = []
    modify_lines_index = {}
    with open(patch_file_path, 'r') as file:
        for line in file:
            if line.startswith('-') and not line.startswith('---'):
                processed_line = line.lstrip('-').strip()
                print(processed_line)
                modify_lines.append(processed_line)
    
    with open(source_code_path, 'r') as file:
        line_number = 1
        for source_line in file:
            for patch_line in modify_lines:
                if source_line == patch_line:
                    modify_lines_index['modify_lines'] = line_number
            line_number += 1
    return modify_lines_index

def load_json(file_path):
    with open(file_path, 'r') as file:
        data = json.load(file)
        return data
    
projects = ['Lang']
for project in projects:
    patch_file_path = "../analysis_result/GPT_response/patch_generation/Lang/patch/"
    for filename in os.listdir(patch_file_path):
        if filename.endswith(".txt"):
            bug_id = filename.split(".")[0]
            patch_file = os.path.join(patch_file_path, filename)
            fault_localization_path = f"../analysis_result/GPT_response/fault_location/Lang/{bug_id}.json"
            fault_localization_info = load_json(fault_localization_path)
            modify_code_name = fault_localization_info['file_name']
            source_code_path = '/Users/wang/Documents/project/defects4j/Data/Lang/' + bug_id.lower() + '_b/' + modify_code_name
            print(bug_id)
            modify_lines = find_modify_code_line_in_project(source_code_path, patch_file)
            # print(f"{bug_id}: {modify_lines}")
            





