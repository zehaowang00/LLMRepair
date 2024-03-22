import pandas as pd
import os 
import json
import re
from openai import OpenAI

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
    
def prompt_init(prompt, description, title, source_code, file_name):
     prompt['Bug report description'] = description
     prompt['Bug report title'] = title
     prompt['Checked code'] = source_code
     prompt['"File name of checked code"'] = file_name
     return prompt
     

prompt_localization = {
  "Role": "As a professional developers. You are responsible for locate and extract the buggy code snippet in the provided checked code carefully and accurately",
  "Instruction": "check the bug report description/title and try to answer the question. Output in JSON format.",
  "Bug report description": "",
  "Bug report title": "", 
  "Checked code": "",
  "File name of checked code": "",
  "Question": """ 
            Question1: What is the file name of checked code? 
            Question2: If checked code has the bug that is described in the bug report? (Only Answer Yes or No)
            Question3: In the checked code, Which method in the code contains the bug in the bug report? (please output the entire method that include buggy code from checked code, include the method name and body. The code you provide here is for further manual fix.)
            Question4: In the mthod, which code statements cause the bug?  (please answer the specific buggy code statements carefully. The answer should be the code in the method-level buggy code from the answer of Question3 for the bug in bug report.)
  """
}


#bug_report_des_path = '../analysis_result/parsed_bug_reports/Lang/LANG-747.json'
#source_code_path = '/Users/wang/Documents/project/defects4j/Data/Lang/lang_1_b/src/main/java/org/apache/commons/lang3/math/NumberUtils.java'
#save_file_path = '../analysis_result/GPT_response/fault_location/Lang/LANG-1.json'
# bug_report_des_path = '../analysis_result/parsed_bug_reports/Lang/LANG-857.json'
# source_code_path = '/Users/wang/Documents/project/defects4j/Data/Lang/lang_6_b/src/main/java/org/apache/commons/lang3/text/translate/CharSequenceTranslator.java'
# save_file_path = '../analysis_result/GPT_response/fault_location/Lang/LANG-6.json'
bug_report_des_path = '../analysis_result/parsed_bug_reports/Lang/LANG-304.json'
source_code_path = '/Users/wang/Documents/project/defects4j/Data/Lang/lang_57_b/src/java/org/apache/commons/lang/LocaleUtils.java'
save_file_path = '../analysis_result/GPT_response/fault_location/Lang/LANG-57.json'
report = load_bug_report(bug_report_des_path)
prompt_localization = prompt_init(prompt_localization, report[0]['description'], preprocessing_title(report[0]['title']), load_source_code(source_code_path), "src/main/java/org/apache/commons/lang3/text/translate/CharSequenceTranslator.java")
api_key_path = "/Users/wang/Documents/project/api_key.json" # use your key
api_key = load_api_key(api_key_path)
client = OpenAI(api_key=api_key)
fault_localization(client, prompt_localization, "", save_file_path)