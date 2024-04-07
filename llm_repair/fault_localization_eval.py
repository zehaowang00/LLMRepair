import json
import os
import pandas as pd

response_dir = '/Users/linqiangguo/PycharmProjects/LLMRepair/analysis_result/GPT_response/fault_location/Lang'
ground_truth_lines = '/Users/linqiangguo/PycharmProjects/LLMRepair/dataset/localization_groudtruth/buggy-lines'
ground_truth_methods = '/Users/linqiangguo/PycharmProjects/LLMRepair/dataset/localization_groudtruth/buggy-methods'


def read_json_file(file_path):
    with open(file_path, 'r') as file:
        return json.load(file)


def read_methods_file(file_path):
    methods_data = pd.read_csv(file_path, delimiter=',', header=None, names=['method', 'value'])
    return methods_data[methods_data['value'] == 1]


def read_lines_file(file_path):
    lines_data = pd.read_csv(file_path, delimiter='#', header=None, names=['file_name', 'code'])
    return lines_data['code'].tolist()


# TODO
def evaluate_responses(responses, ground_truth_line_data, ground_truth_method_data):

    return evaluation


# Initialize counters for each question
correct_counts = {'Question1': 0, 'Question2': 0, 'Question3': 0, 'Question4': 0}
total_counts = {'Question1': 0, 'Question2': 0, 'Question3': 0, 'Question4': 0}

for filename in os.listdir(response_dir):
    bug_id = filename[:-5].replace('_', '-').capitalize()  # Assuming filename format is "<bug_id>.json"
    response_file_path = os.path.join(response_dir, filename)
    ground_truth_line_path = os.path.join(ground_truth_lines, f"{bug_id}.buggy.lines")
    ground_truth_method_path = os.path.join(ground_truth_methods, f"{bug_id}.buggy.methods")

    if not os.path.exists(ground_truth_method_path):
        continue  # Skip if no corresponding ground truth file exists

    # Load response and ground truth data
    response_data = read_json_file(response_file_path)
    ground_truth_line_data = read_lines_file(ground_truth_line_path)
    ground_truth_method_data = read_methods_file(ground_truth_method_path)

    # Evaluate the response
    evaluation = evaluate_responses(response_data, ground_truth_line_data, ground_truth_method_data)

    # Update counts based on evaluation
    for question, is_correct in evaluation.items():
        if is_correct:
            correct_counts[question] += 1
        total_counts[question] += 1

accuracy_results = {}
for question in correct_counts:
    if total_counts[question] > 0:
        accuracy_results[question] = (correct_counts[question] / total_counts[question]) * 100
    else:
        accuracy_results[question] = 0  # Default to 0% accuracy if no data
