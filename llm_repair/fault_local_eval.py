import pandas as pd
import os
import json


def check_method_level(method_code, ground_method_truth, file_prediction):
    if "False" == file_prediction:
        return "In Wrong File"
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
    if len(ground_method_truth) == 0:
        return "no ground truth File"
    if "," in ground_method_truth:
        truth_list = ground_method_truth.strip().split(',')
    else:
        truth_list = [ground_method_truth.strip()]
    if if_has_bug == "Yes":
        for truth in truth_list:
            ground_file_name = truth.split('.')[-2]
            if ground_file_name in file_name:
                return "True"
        return "False"
    elif if_has_bug == "No":
        for truth in truth_list:
            ground_file_name = truth.split('.')[-2]
            if ground_file_name in file_name:
                return "False"
        return "True"


def load_defect4j(file_path, start_line, end_line):
    try:
        with open(file_path, 'r') as file:
            lines = file.readlines()
            code_segment = lines[start_line - 1:end_line]
            return ''.join(code_segment)
    except Exception as e:
        return f"Error: {e} on path: {file_path}"


def is_code_part_of(main, part):
    return part.strip() in main.strip()


def find_block_from_defect4j(bug_ID, line_info, file_name):
    # line info has sorted lines for bugs
    line_info = line_info.strip().split(',')
    start_line = int(line_info[0])
    end_line = int(line_info[-1])
    # change to your defect4J path
    defect4j_path = '/Users/linqiangguo/IdeaProjects/defects4j/Data/Lang'
    file_path = defect4j_path + '/' + bug_ID.lower() + '_b/'
    return load_defect4j(file_path + file_name, start_line, end_line).strip()


def check_block_level(line_code, ground_line_truth, bug_ID, file_prediction, line_info, file_name):
    if "False" == file_prediction:
        return "In Wrong File"
    if bug_ID in line_unprocessed_bugId or len(ground_line_truth) == 0:
        return "no ground truth block"
    if len(line_code) == 0:
        return "cannot locate code block"
    if len(ground_line_truth) > 0:
        ground_line_truth_list = ground_line_truth.split(',')
        if all(truth == 'FAULT_OF_OMISSION' for truth in ground_line_truth_list):
            missing_truth = find_block_from_defect4j(bug_ID, line_info, file_name)
            if is_code_part_of(missing_truth, line_code) or is_code_part_of(line_code, missing_truth):
                return "True"
            return "False"
        # TODO: Need to discuss: should we get a range or just single line code if one of it truth is FoO
        for truth in ground_line_truth_list:
            if truth == 'FAULT_OF_OMISSION':
                truth = find_block_from_defect4j(bug_ID, line_info, file_name)
            if is_code_part_of(truth, line_code) or is_code_part_of(line_code, truth):
                return "True"

        # for i in range(len(ground_line_truth_list)):
        #    if ground_line_truth_list[i] == 'FAULT_OF_OMISSION':
        #        ground_line_truth_list[i] = find_block_from_defect4j(bug_ID, line_info, file_name)
        #    if is_code_part_of(ground_line_truth_list[i], line_code) or is_code_part_of(line_code,
        #                                                                                ground_line_truth_list[i]):
        #        return "True"
    return "False"


ground_truth_lines = '../dataset/localization_groudtruth/buggy-lines'
ground_truth_methods = '../dataset/localization_groudtruth/buggy-methods/'
projects = ['Lang']
dicts = []
num_files = 0
method_unprocessed_bugId = set()
line_unprocessed_bugId = set()
for project in projects:
    localization_file_path = "../analysis_result/GPT_response/fault_location/Lang_reflection/"
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
                    method_unprocessed_bugId.add(bug_id)
                # process block/line data
                try:
                    ground_truth_line_path = os.path.join(ground_truth_lines, f"{bug_id}.buggy.lines".replace('_', "-"))
                    line_ground_truth = pd.read_csv(ground_truth_line_path, delimiter='#', header=None,
                                                    names=['file', 'line', 'code'])
                    line_ground_truth['code'] = line_ground_truth['code'].str.lstrip()
                    fault_localization_info['Ground_Line_Truth'] = ",".join(line_ground_truth['code'])
                    fault_localization_info['Ground_Line_Location'] = ",".join(str(int(line))
                                                                               for line in line_ground_truth['line'])
                except Exception as e:
                    line_unprocessed_bugId.add(bug_id)
                dicts.append(fault_localization_info)

fault_df = pd.DataFrame(dicts)
fault_df['Locate Correct File'] = fault_df.apply(
    lambda row: check_file_level(row['file_name'], row['Ground_Method_Truth'], row['if_has_bug']), axis=1)
fault_df['Locate Correct Method'] = fault_df.apply(
    lambda row: check_method_level(row['method_level'], row['Ground_Method_Truth'], row['Locate Correct File']), axis=1)
fault_df['Locate Correct Block'] = fault_df.apply(
    lambda row: check_block_level(row['block_level'], row['Ground_Line_Truth'], row['Bug_ID'],
                                  row['Locate Correct File'], row['Ground_Line_Location'], row['file_name']), axis=1)


def eval_with_reflection(fault_df):
    fault_df.to_csv("../analysis_result/evaluation/fault_location_eval.csv", index=False)
    # file level evaluation
    df_file_filtered = fault_df[fault_df['Locate Correct File'].isin(['True', 'False'])]
    # Calculate True Positives (TP)
    tp_file = df_file_filtered[(df_file_filtered['if_has_bug'] == 'Yes')
                               & (df_file_filtered['Locate Correct File'] == 'True')].shape[0]
    # Calculate False Positives (FP)
    fp_file = df_file_filtered[(df_file_filtered['if_has_bug'] == 'Yes')
                               & (df_file_filtered['Locate Correct File'] == 'False')].shape[0]
    # Calculate False Negative (FN)
    fn_file = df_file_filtered[(df_file_filtered['if_has_bug'] == 'No')
                               & (df_file_filtered['Locate Correct File'] == 'False')].shape[0]
    file_recall = tp_file / (tp_file + fn_file)
    file_precision = tp_file / (tp_file + fp_file) if (tp_file + fp_file) > 0 else 0
    file_f1_score = 2 * (file_precision * file_recall) / (file_precision + file_recall) if (
                                                                                                   file_precision + file_recall) != 0 else 0
    df_file_true = df_file_filtered[(df_file_filtered['Locate Correct File'] == 'True')].shape[0]
    file_acc = df_file_true / len(df_file_filtered) if df_file_true > 0 else 0
    print("File level: accuracy: " + str(file_acc) + ", recall: " + str(file_recall) + ", precision: "
          + str(file_precision) + ", f1: " + str(file_f1_score))

    # method level evaluation
    df_method_filtered = fault_df[fault_df['Locate Correct Method'].isin(['True', 'False'])]
    df_method_true = df_method_filtered[(df_method_filtered['Locate Correct Method'] == 'True')].shape[0]
    method_accuracy = df_method_true / len(df_method_filtered) if len(df_method_filtered) > 0 else 0
    print("Method level accuracy:" + str(method_accuracy))

    # block level evaluation
    df_block_filtered = fault_df[fault_df['Locate Correct Block'].isin(['True', 'False'])]
    df_block_true = df_block_filtered[(df_block_filtered['Locate Correct Block'] == 'True')].shape[0]
    block_accuracy = df_block_true / len(df_block_filtered) if len(df_block_filtered) > 0 else 0
    print("Block level accuracy:" + str(block_accuracy))


eval_with_reflection(fault_df)

if len(method_unprocessed_bugId) > 0:
    print(("Method Unprocessed bug id: {}".format(method_unprocessed_bugId)))
if len(line_unprocessed_bugId) > 0:
    print(("Block Unprocessed bug id: {}".format(line_unprocessed_bugId)))
