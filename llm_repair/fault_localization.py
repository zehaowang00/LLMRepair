import openai
import pandas as pd
import os
import json
import re
from openai import OpenAI
from unity_tool import load_api_key, preprocessing_title, get_report_map_dic, load_json, load_bug_report, get_completion, load_source_code


class PredictionBugReport:
    def __init__(self, bugReport, fileName, prob):
        self.bugReport = bugReport
        self.fileName = fileName
        self.prob = float(prob) if isinstance(prob, str) else prob


def get_predict_file_map_dic(predict_df):
    predict_df['rank'] = predict_df['rank'].apply(lambda x: int(x))
    predict_df['bugReport'] = predict_df['bugReport'].apply(lambda x: x.replace('-', '_'))
    predict_df['fileName'] = predict_df['fileName'].apply(lambda x: str(x))
    predict_df['prob'] = predict_df['prob'].apply(lambda x: str(x))
    bug_reports_dict = {row['rank']: PredictionBugReport(row['bugReport'], row['fileName'], row['prob'])
                        for _, row in predict_df.iterrows()}

    return bug_reports_dict


def fault_localization(client, prompt, few_shots, save_file_path):
    response = get_completion(client, json.dumps(prompt))
    # with open(save_file_path, 'w') as file:
    #     json.dump(json.loads(response), file, indent=4)
    return response


def prompt_init(prompt, description, title, source_code, file_name):
    prompt['Bug report description'] = description
    prompt['Bug report title'] = title
    prompt['Checked code'] = source_code
    prompt['"File name of checked code"'] = file_name
    return prompt


def prompt_reason_fault(prompt):
    return prompt


def has_reason_analysis():
    return False


def main():
    prompt_localization = {
        "Role": "As a professional developers. You are responsible for locate if the provide code file has the bug described in the bug report carefully and accurately. If it is, you also should help to locate the speific location of bug.",
        "Instruction": "check the bug report description/title and try to answer the question. Output in JSON format. Please use following for key for the four questison: file_name, if_has_bug, method_level, block_level",
        "Bug report description": "",
        "Bug report title": "",
        "Checked code": "",
        "File name of checked code": "",
        "Question": """ 
                Question1: What is the file name of checked code? 
                Question2: If checked code has the bug that is described in the bug report? (Only Answer Yes or No.Only Answer Yes or No. The code file may have the bug described in the bug report or not, so you need to check carefully. If you answer yes, you must be very sure the bug in bug report happen in this code file no other source code file.)
                Question3: In the checked code file, Which method in the code contains the bug in the bug report? (If the answer to question 2 is yes. You must be sure that the bug in bug report happens in this method you find. Please output the entire and complete method header. Engineer will try to solve the bug by addresing this method. ) 
                Question4: In the method you find in answer3, which code statements cause the bug in the bug report?  (If the answer to question 2 is yes. The answer should be the block-level source code snippets that is inside the method you find in Question3 rather than natural language. Please provide the detailed block-level code snippets that include the bug triggering code for the bug in the bug report.)
      """
    }
    # load api key - use your own openai key
    api_key_path = "/Users/wang/Documents/project/api_key.json"  # use your key
    api_key = load_api_key(api_key_path)

    # load bug report
    report_map_path = '../dataset/bug_report/Lang/bug_report.csv'
    bug_report = pd.read_csv(report_map_path)
    bug_report_map = get_report_map_dic(bug_report)
    error_bug_id_list = []
    index = 0
    # for each bug report, find the predictions methods list from bug_file_prediction by IR
    for bug_id, report_id in bug_report_map.items():
        bug_report_des_path = '../analysis_result/parsed_bug_reports/Lang/' + bug_report_map[bug_id] + '.json'
        report_id = report_id.replace("_", "-")
        predict_file_name = f"finalmultic_{report_id}"
        predict_report_map_path = ('../dataset/bug_file_prediction'
                                   '/LANG_file_predict/') + predict_file_name + '.csv'
        try:
            predict_file = pd.read_csv(predict_report_map_path)
            predict_file_map = get_predict_file_map_dic(predict_file)
        except FileNotFoundError as e:
            error_bug_id_list.append(bug_id)
            continue
        response_results = []
        # for each bug, and top k(or by threshold) suspicious buggy method, build prompt to LLM
        for rank, predictionBugReport in predict_file_map.items():
            prob = predictionBugReport.prob
            # by threshold
            # if prob < 0.5:

            # by rank (eg: we only take the highest rank method)
            if rank > 3:
                break
            else:
                fileName = predictionBugReport.fileName
                source_code_path = '/Users/wang/Documents/project/defects4j/Data/Lang/' + bug_id.lower() + '_b/' + fileName
                save_file_path = f'../analysis_result/GPT_response/fault_location/Lang/{bug_id}.json'
                report = load_bug_report(bug_report_des_path)
                prompt_localization = prompt_init(prompt_localization, report[0]['description'],
                                                  preprocessing_title(report[0]['title']),
                                                  load_source_code(source_code_path),
                                                  fileName)
                client = OpenAI(api_key=api_key)
                try:
                    if not has_reason_analysis():
                        result = fault_localization(client, prompt_localization, "", save_file_path)
                        response_results.append(json.loads(result))
                    else:
                        result = prompt_localization = prompt_reason_fault(prompt_localization)
                        fault_localization(client, prompt_localization, "", save_file_path)
                        response_results.append(json.loads(result))
                    # index = index + 1
                    # print("processed: " + str(index))
                # except openai.BadRequestError as e:
                #     error_bug_id_list.append(bug_id)
                #     continue
                # except openai.RateLimitError as e2:
                #     error_bug_id_list.append(bug_id)
                #     continue
                except Exception as e:
                    error_bug_id_list.append(bug_id)
                    print(str(bug_id))
                    continue
        index = index + 1
        print("processed: " + str(index))
        with open(save_file_path, 'w') as file:
            saved_dict = {'result': response_results}
            json.dump(saved_dict, file, indent=4)

    print(error_bug_id_list)


if __name__ == "__main__":
    main()
