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


def get_completion(client, prompt):
    messages = [{"role": "user", "content": prompt}]
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        # model = 'gpt-4',
        messages=messages,
        response_format={"type": "json_object"},
        temperature=0.3,
    )
    return response.choices[0].message.content


def fault_localization(client, prompt, few_shots, save_file_path):
    response = get_completion(client, json.dumps(prompt))
    #with open(save_file_path, 'w') as file:
    #    json.dump(json.loads(response), file, indent=4)
    return response

def prompt_init(prompt, description, title, source_code):
    prompt['Bug report description'] = description
    prompt['Bug report title'] = title
    prompt['Checked code file'] = source_code
    #prompt['"File name of checked code"'] = file_name
    return prompt


def prompt_reason_fault(prompt):
    return prompt


def get_report_map_dic(report_df):
    report_df['Lang ID'] = report_df['Bug ID'].apply(lambda x: 'LANG_' + str(x))
    report_df['Report ID'] = report_df['Report ID'].apply(lambda x: x.replace('-', '_'))
    return report_df.set_index('Lang ID')['Report ID'].to_dict()


def get_predict_file_map_dic(predict_df):
    predict_df['rank'] = predict_df['rank'].apply(lambda x: int(x))
    predict_df['bugReport'] = predict_df['bugReport'].apply(lambda x: x.replace('-', '_'))
    predict_df['fileName'] = predict_df['fileName'].apply(lambda x: str(x))
    predict_df['prob'] = predict_df['prob'].apply(lambda x: str(x))
    bug_reports_dict = {row['rank']: PredictionBugReport(row['bugReport'], row['fileName'], row['prob'])
                        for _, row in predict_df.iterrows()}

    return bug_reports_dict


def has_reason_analysis():
    return False


prompt_localization = {
    "Role": "As a professional developer, you are responsible for locating the bug in the provided checked code carefully and accurately",
    "Instruction": "You are provided with three source code files, you need to check the bug report description/title and try to answer the question. Output in JSON format. Please use the following key for the four questions: file_name, if_has_bug, method_level, block_level",
    "Bug report description": "",
    "Bug report title": "",
    "Checked code file": "",
    "Question": """ 
            Question1: Which is the file has the bug described in the bug report? (Only one file has the bug please answer the file name that contain bug. The code file may have the bug described in the bug report or not, so you need to check carefully. If the bug report mentions the same class name, the code file is likely to contain the bug, Otherwise the code file is likely not to contain the bug )
            Question2: In the checked code, Which method in the code contains the bug in the bug report? ( For the file from the answer for question1, please output the entire method that include buggy code from checked code, include the method name and body. The code you provide here is for further manual fix.)
            Question3: In the method, which code statements cause the bug?  (For the file from the answer for question1,. please answer the specific buggy code statements carefully. The answer should be the code in the method-level buggy code from the answer of Question3 for the bug in bug report.)
  """
}

# bug_report_des_path = '../analysis_result/parsed_bug_reports/Lang/LANG-747.json'
# source_code_path = '/Users/wang/Documents/project/defects4j/Data/Lang/lang_1_b/src/main/java/org/apache/commons/lang3/math/NumberUtils.java'
# save_file_path = '../analysis_result/GPT_response/fault_location/Lang/LANG-1.json'
# bug_report_des_path = '../analysis_result/parsed_bug_reports/Lang/LANG-857.json'
# source_code_path = '/Users/wang/Documents/project/defects4j/Data/Lang/lang_6_b/src/main/java/org/apache/commons/lang3/text/translate/CharSequenceTranslator.java'
# save_file_path = '../analysis_result/GPT_response/fault_location/Lang/LANG-6.json'

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
    if bug_id != "LANG_18":
        continue
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
    #response_reuslt= []
    source_codes_list = dict()
    #with open(save_file_path, 'w') as file:
    # source_code_for_bug = 
    # for rank, predictionBugReport in predict_file_map.items():
    #     prob = predictionBugReport.prob

    for rank, predictionBugReport in predict_file_map.items():
        prob = predictionBugReport.prob
        # by threshold
        # if prob < 0.5:

        # by rank (eg: we only take the highest rank method)
        if rank > 2:
            break
        else:
            fileName = predictionBugReport.fileName
            source_code_path = '/Users/wang/Documents/project/defects4j/Data/Lang/' + bug_id.lower() + '_b/' + fileName
            source_codes_list[fileName] = load_source_code(source_code_path)

    save_file_path = f'../analysis_result/GPT_response/fault_location/Lang/{bug_id}.json'
    report = load_bug_report(bug_report_des_path)
    prompt_localization = prompt_init(prompt_localization, report[0]['description'],
                                        preprocessing_title(report[0]['title']),
                                        json.dumps(source_codes_list))
    client = OpenAI(api_key=api_key)
            
    try:
        if not has_reason_analysis():
            result = fault_localization(client, prompt_localization, "", save_file_path)
        else:
            prompt_localization = prompt_reason_fault(prompt_localization)
            result = fault_localization(client, prompt_localization, "", save_file_path)
        index = index + 1
        print("processed: " + str(index))
    except Exception as e:
        error_bug_id_list.append(bug_id)
        #print(result)
        print(str(e) + ": " +  str(bug_id))
        continue
    # except openai.BadRequestError as e:
    #     error_bug_id_list.append(bug_id)
    #     print(result)
    #     print(str(e) + ": " +  str(bug_id))
    #     continue
    # except openai.RateLimitError as e2:
    #     error_bug_id_list.append(bug_id)
    #     continue
    with open(save_file_path, 'w') as file:
        # save_result = {"result":reuslt}
        json.dump(json.loads(result), file, indent=4)
    
print(error_bug_id_list)