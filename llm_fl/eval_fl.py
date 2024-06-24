import pandas as pd
import os
from llm_repair.unity_tool import get_report_map_dic, load_bug_report

def get_class_name(full_string):
    parts = full_string.split('.')
    if len(parts) > 1:
        if '$' in parts[-2]:
            parts[-2] = parts[-2].split('$')[0]
        return parts[-2] + '.java'
    else:
        return full_string
def eval_recall(suspicious_files, ground_truth):
    merged_df = pd.merge(suspicious_files, ground_truth, on='Bug_ID')
    relevant_in_top_5 = 0
    for index, row in merged_df.iterrows():
        top_5_files = [row['rank1'], row['rank2'], row['rank3'], row['rank4'], row['rank5']]
        if row['class_name'] in top_5_files:
            relevant_in_top_5 += 1
        # else:
        #     print(f"Bug ID: {row['Bug_ID']}, Ground truth: {row['class_name']}, Top 5: {top_5_files}")
    # Calculate the recall
    recall = relevant_in_top_5 / len(ground_truth)

    print(f"Recall for the top 5 suspicious files: {recall:.2f}")

def eval_precision(suspicious_files, ground_truth):
    pass

report_map_path = '../dataset/bug_report/Lang/bug_report.csv'
bug_report = pd.read_csv(report_map_path)
bug_report_map = get_report_map_dic(bug_report)
fl_result = dict()
for bug_id, report_id in bug_report_map.items():
    ground_truth_methods = '../dataset/localization_groudtruth/buggy-methods/'
    ground_truth_method_path = os.path.join(ground_truth_methods,
                                            f"{bug_id}.buggy.methods".replace('_', "-"))
    method_ground_truth = pd.read_csv(ground_truth_method_path, delimiter=',', header=None,
                                      names=['method', 'value'])
    method_ground_truth = method_ground_truth[method_ground_truth['value'] == 1]
    method_ground_truth = ",".join(method_ground_truth['method'])
    fl_result[bug_id] = method_ground_truth

fl_result_df = pd.DataFrame.from_dict(fl_result, orient='index')
fl_result_df.columns = ['Ground_Method_Truth']
#fl_result_df.dropna(subset=['Ground_Method_Truth'], inplace=True)
fl_result_df = fl_result_df[fl_result_df['Ground_Method_Truth'] != '']
fl_result_df['class_name'] = fl_result_df['Ground_Method_Truth'].apply(get_class_name)
fl_result_df.to_csv('../analysis_result/bm25/fl/fl_benchmark.csv', index_label='Bug_ID')


suspicious_result = pd.read_csv('../analysis_result/bm25/fl/fl_result.csv')
ground_truth = pd.read_csv('../analysis_result/bm25/fl/fl_benchmark.csv')
ground_truth = ground_truth[ground_truth['Ground_Method_Truth'] != '']
eval_recall(suspicious_result, ground_truth)

