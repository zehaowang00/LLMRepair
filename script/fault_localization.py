import pandas as pd
import os 
import json
import re
from openai import OpenAI

def get_completion(client, prompt):
    messages = [{"role": "user", "content": prompt}]
    response = client.chat.completions.create(
        model="gpt-3.5-turbo-0125",
        messages=messages,
        response_format={"type": "json_object"},
        temperature=0,
    )
    return response.choices[0].message.content

def fault_localization(client, prompt, few_shots, save_file_path):
    response = get_completion(client, json.dumps(prompt))
    with open(save_file_path, 'w') as file:
       json.dump(json.loads(response), file, indent=4)

def load_bug_report(file_path):
    with open(file_path, 'r') as file:
            data = json.load(file)
            return data
    
def preprocessing_title(report_title):
     processed_str = re.sub(r"\[LANG-\d+\]", "", report_title)
     return processed_str.strip()

def load_source_code(file_path):
         with open(file_path, 'r') as file:
            source_code = file.read()
            return source_code
         
def load_api_key(key_path):
    with open(key_path, 'r') as file:
        data = json.load(file)
        return data['Key']

prompt_localization = {
  "Role": "As a professional developers. You are responsible for locate the location of buggy code snippet in the provided input file",
  "Instruction": "check the bug report description/title and try to find the answer for the question. Output in json format.",
  "Bug report description": "",
  "Bug report title": "", 
  "Input file": "",
  "Question": """ 
            Question1: What is the code that contains the bug in the provided input file? (Please just reply the block level of code statements that has bug. Do not explain the bug, just reply the source code that may contain bug)
            Question2: Provide the code line number about the buggy code snippet in the source code. (Answer the location of start line number and the location of end line number)
  """
}

bug_report_des_path = '../analysis_result/parsed_bug_reports/Lang/LANG-747.json'
source_code_file = '/Users/wang/Documents/project/defects4j/Data/Lang/lang_1_b/src/main/java/org/apache/commons/lang3/math/NumberUtils.java'
save_file_path = '../analysis_result/GPT_response/fault_location/Lang/LANG-1.json'
report = load_bug_report(bug_report_des_path)
prompt_localization['Bug report description'] = report[0]['description']
prompt_localization['Bug report title'] = preprocessing_title(report[0]['title'])
api_key_path = "/Users/wang/Documents/project/api_key.json" # use your key
api_key = load_api_key(api_key_path)
client = OpenAI(api_key=api_key)
fault_localization(client, prompt_localization, "", save_file_path)