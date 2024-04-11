import openai
import pandas as pd
import os
import json
import re
from openai import OpenAI

from fault_localization import load_api_key, preprocessing_title, get_report_map_dic, load_json, load_bug_report, get_completion

def fault_local_reflection(client, prompt, save_file_path):
    response = get_completion(client, json.dumps(prompt))
    #print(response)
    with open(save_file_path, 'w') as file:
        json.dump(json.loads(response), file, indent=4)
    #return response


def prompt_init(prompt, description, title, source_code):
    prompt['Bug report description'] = description
    prompt['Bug report title'] = title
    prompt['code from agents'] = source_code
    return prompt


prompt_reflection = {
    "Role": "As a professional developers. You are responsible check the fault localization result from other agent.",
    "Instruction": "Other agent provides three fault localization result on three different code files but there is only file that has the bug for the bug in the bug report. Check the bug report description/title and try to answer the question. Output in JSON format. Please use following for key: file_name, if_has_bug, method_level, block_level",
    "Bug report description": "",
    "Bug report title": "",
    "code from agents": "",
    "Question": """
        Which fault localization result is correct? (you need to choose the fault localization result from other agent and output in JSON format with the four keys.)
  """
}
projects = ['Lang']
dicts = []
report_map_path = '../dataset/bug_report/Lang/bug_report.csv'
bug_report = pd.read_csv(report_map_path)
bug_report_map = get_report_map_dic(bug_report)
agents_result = dict()
api_key_path = "/Users/wang/Documents/project/api_key.json"  # use your key
api_key = load_api_key(api_key_path)
client = OpenAI(api_key=api_key)
for project in projects:
    localization_file_path = "../analysis_result/GPT_response/fault_location/Lang/"
    count = 1
    for filename in os.listdir(localization_file_path):
        bug_id = filename.split(".")[0]
        if len(bug_id) == 0:
            continue
        bug_report_des_path = '../analysis_result/parsed_bug_reports/Lang/' + bug_report_map[bug_id] + '.json'
        save_file_path = f'../analysis_result/GPT_response/fault_location/Lang_reflection/{bug_id}.json'
        #report_id = report_id.replace("_", "-")
        report = load_bug_report(bug_report_des_path)
        if filename.endswith(".json"):
            fault_localization_info = load_json(localization_file_path + filename)
            index = 0
            for fault_localization in fault_localization_info['result']:
                agents_result['agent' + str(index)] = fault_localization
                index += 1
            index = 0
            #print(agents_result)
        # except Exception as e:
        #     print(bug_id)
        #     print(e)
        prompt_reflection = prompt_init(prompt_reflection, report[0]['description'],
                                        preprocessing_title(report[0]['title']),
                                        agents_result
                                        )
        fault_local_reflection(client, prompt_reflection, save_file_path)
        print("processed result: " + str(count))
        count += 1
