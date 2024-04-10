import openai
import pandas as pd
import os 
import json
import re
from openai import OpenAI


class PredictionBugReport:
    def __init__(self, bugReport, fileName, prob):
        self.bugReport = bugReport
        self.fileName = fileName
        self.prob = float(prob) if isinstance(prob, str) else prob


def get_completion(client, prompt):
    messages = [{"role": "user", "content": prompt}]
    response = client.chat.completions.create(
        model="gpt-3.5-turbo-0125",
        # model = 'gpt-4',
        messages=messages,
        response_format={"type": "json_object"},
        temperature=0.3,
    )
    return response.choices[0].message.content


def fault_localization(client, prompt, few_shots, save_file_path):
    response = get_completion(client, json.dumps(prompt))
    # with open(save_file_path, 'w') as file:
    #     json.dump(json.loads(response), file, indent=4)
    return response


def load_bug_report(file_path):
    with open(file_path, 'r') as file:
        data = json.load(file)
        return data


def preprocessing_title(report_title):
    processed_str = re.sub(r"\[LANG-\d+\]", "", report_title)
    return processed_str.strip()


def load_source_code(file_path):
    try:
        with open(file_path, 'r') as file:
            source_code = file.read()
            return source_code
    except Exception as e:
        return f"Error: {e}" + f"on path: {file_path}"


def load_api_key(key_path):
    with open(key_path, 'r') as file:
        data = json.load(file)
        return data['Key']


def prompt_init(prompt, description, title, source_code, file_name):
    prompt['Bug report description'] = description
    prompt['Bug report title'] = title
    prompt['Checked code'] = source_code
    prompt['"File name of checked code"'] = file_name
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
    "Role": "As a professional developers. You are responsible for locate and extract the buggy code snippet in the provided checked code carefully and accurately",
    "Instruction": "check the bug report description/title and try to answer the question. Output in JSON format. Please use following for key for the four questison: file_name, if_has_bug, method_level, block_level",
    "Bug report description": "",
    "Bug report title": "",
    "Checked code": "",
    "File name of checked code": "",
    "Question": """ 
            Question1: What is the file name of checked code? 
            Question2: If checked code has the bug that is described in the bug report? (Only Answer Yes or No.Only Answer Yes or No. The code file may have the bug described in the bug report or not, so you need to check carefully. If you answer yes, you must be very sure the bug in bug report happen in this code file no other source code file.)
            Question3: In the checked code, Which method in the code contains the bug in the bug report? (If the answer to question 2 is yes. please output the entire method that include buggy code from checked code, include the method name and body. The code you provide here is for further manual fix.)
            Question4: In the method, which code statements cause the bug?  (If the answer to question 2 is yes. The answer should be the code in the method-level buggy code from the answer of Question3 for the bug in bug report.)
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
            except openai.BadRequestError as e:
                error_bug_id_list.append(bug_id)
                continue
            except openai.RateLimitError as e2:
                error_bug_id_list.append(bug_id)
                continue
    index = index + 1
    print("processed: " + str(index))
    with open(save_file_path, 'w') as file:
        saved_dict = {'result': response_results}
        json.dump(saved_dict, file, indent=4)

print(error_bug_id_list)