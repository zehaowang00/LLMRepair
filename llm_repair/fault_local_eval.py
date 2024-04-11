import pandas as pd
import os
import json


def load_json(file_path):
    with open(file_path, 'r') as file:
        data = json.load(file)
        return data


def check_method_level(method_code, ground_method_truth, file_prediction):
    if "False" == file_prediction:
        return "False"
    if len(ground_method_truth) == 0:
        return "no ground truth method"
    if len(method_code) == 0:
        return "cannot locate method"
    method_signature = method_code.strip().split('(')
    method_signature = method_signature[0].split(' ')[-1]
    if len(ground_method_truth) > 0:
        if "," in ground_method_truth:
            truth_list = ground_method_truth.strip().split(',')
        else:
            truth_list = [ground_method_truth.strip()]
        for function_name in truth_list:
            function_name = function_name.split('.')[-1]
            function_name = function_name[:function_name.index('(')]
            if function_name == method_signature:
                return "True"
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


def is_code_part_of(main, part):
    return part.strip() in main.strip()


def check_block_level(line_code, ground_line_truth, bug_ID, file_prediction):
    if "FALSE" == file_prediction:
        return "False"
    if bug_ID in line_unprocessed_bugId or len(ground_line_truth) == 0:
        return "no ground truth block"
    if len(line_code) == 0:
        return "cannot locate code block"
    if len(ground_line_truth) > 0:
        ground_line_truth_list = ground_line_truth.split(',')
        if all(truth == 'FAULT_OF_OMISSION' for truth in ground_line_truth_list):
            return "ground truth are al FoOs"
        for truth in ground_line_truth_list:
            if truth == 'FAULT_OF_OMISSION':
                continue
            if is_code_part_of(truth, line_code) or is_code_part_of(line_code, truth):
                return "True"

    return "False"


ground_truth_lines = '../dataset/localization_groudtruth/buggy-lines'
ground_truth_methods = '../dataset/localization_groudtruth/buggy-methods/'
projects = ['Lang']
dicts = []
num_files = 0
method_unprocessed_bugId = []
line_unprocessed_bugId = []
for project in projects:
    localization_file_path = "../analysis_result/GPT_response/fault_location/Lang/"
    files = os.listdir(localization_file_path)
    num_files += len(files)
    for filename in files:
        bug_id = filename.split(".")[0]
        if filename.endswith(".json"):
            with open(localization_file_path + filename) as f:
                fault_localization_data = json.load(f)
            for fault_localization_info in fault_localization_data['result']:
                fault_localization_info['Bug_ID'] = bug_id
                try:
                    ground_truth_method_path = os.path.join(ground_truth_methods,
                                                            f"{bug_id}.buggy.methods".replace('_', "-"))
                    method_ground_truth = pd.read_csv(ground_truth_method_path, delimiter=',', header=None,
                                                      names=['method', 'value'])
                    method_ground_truth = method_ground_truth[method_ground_truth['value'] == 1]
                    fault_localization_info['Ground_Method_Truth'] = ",".join(method_ground_truth['method'])
                except Exception as e:
                    method_unprocessed_bugId.append(bug_id)
                # process block/line data
                try:
                    ground_truth_line_path = os.path.join(ground_truth_lines, f"{bug_id}.buggy.lines".replace('_', "-"))
                    line_ground_truth = pd.read_csv(ground_truth_line_path, delimiter='#', header=None,
                                                    names=['file', 'line', 'code'])
                    line_ground_truth['code'] = line_ground_truth['code'].str.lstrip()
                    fault_localization_info['Ground_Line_Truth'] = ",".join(line_ground_truth['code'])
                except Exception as e:
                    line_unprocessed_bugId.append(bug_id)
                dicts.append(fault_localization_info)


fault_df = pd.DataFrame(dicts)
fault_df['Locate Correct File'] = fault_df.apply(
    lambda row: check_file_level(row['file_name'], row['Ground_Method_Truth'], row['if_has_bug']), axis=1)
fault_df['Locate Correct Method'] = fault_df.apply(
    lambda row: check_method_level(row['method_level'], row['Ground_Method_Truth'], row['Locate Correct File']), axis=1)
fault_df['Locate Correct Block'] = fault_df.apply(
    lambda row: check_block_level(row['block_level'], row['Ground_Line_Truth'], row['Bug_ID'],
                                  row['Locate Correct File']), axis=1)

fault_df.to_csv("../analysis_result/evaluation/fault_location_eval.csv", index=False)

df_file_filtered = fault_df[fault_df['Locate Correct File'].isin(['True', 'False'])]
df_dedupe_file = df_file_filtered.drop_duplicates(subset='Bug_ID', keep='first')
checked_len_file = len(df_dedupe_file['Bug_ID'])
recall_success_count = df_file_filtered.groupby('Bug_ID')['Locate Correct File'].apply(lambda x: 'True' in x.values).sum()
accuracy_count = df_file_filtered[df_file_filtered["Locate Correct File"] == "True"].shape[0]

file_recall = recall_success_count / checked_len_file if checked_len_file > 0 else 0
file_accuracy = accuracy_count / len(df_file_filtered) if len(df_file_filtered) > 0 else 0
print("File level recall:" + str(file_recall) + ", accuracy:"
      + str(file_accuracy))

print(("Method Unprocessed bug id: {}".format(method_unprocessed_bugId)))
print(("Block Unprocessed bug id: {}".format(line_unprocessed_bugId)))
