import pandas as pd
import os 
import json
from openai import OpenAI
import re

def get_completion(client, prompt):
    messages = [{"role": "user", "content": prompt}]
    response = client.chat.completions.create(
        model="gpt-3.5-turbo-0125",
        #model="gpt-4",
        messages=messages,
        response_format={"type": "json_object"},
        temperature=0.3,
    )
    return response.choices[0].message.content

def patch_generation(client, prompt, few_shots, save_file_path ):
    response = get_completion(client, json.dumps(prompt))
    with open(save_file_path.replace('.json', '.txt'), 'w') as file:
         file.write(json.loads(response)['Fix Patch'])
    with open(save_file_path, 'w') as file:
       json.dump(json.loads(response), file, indent=4)

def test_generation(client, prompt, few_shots, save_file_path ):
    response = get_completion(client, json.dumps(prompt))
    with open(save_file_path, 'w') as file:
       json.dump(json.loads(response), file, indent=4)

def load_json(file_path):
    with open(file_path, 'r') as file:
            data = json.load(file)
            return data 
    
def load_api_key(key_path):
    with open(key_path, 'r') as file:
        data = json.load(file)
        return data['Key']
    
def load_source_code(file_path):
         with open(file_path, 'r') as file:
            source_code = file.read()
            return source_code
         
def preprocessing_title(report_title):
     processed_str = re.sub(r"\[LANG-\d+\]", "", report_title)
     return processed_str.strip()

def generate_patch():
     pass

def generate_test():
     pass

def prompt_init_patch(prompt, example, description, title, file_name, method_buggy_code, suspicious_code):
     prompt['Fix Patch format Example'] = "git diff format"
     prompt['Bug report description'] = description
     prompt['Bug report title'] = title
     prompt['Method include buggy code'] = method_buggy_code
     prompt['suspicious buggy code statements'] = suspicious_code
     prompt['File name of checked code'] = file_name
     return prompt


def prompt_init_test(prompt, description, title, method_buggy_code, suspicious_code):
     prompt['Bug report description'] = description
     prompt['Bug report title'] = title
     prompt['Method include buggy code'] = method_buggy_code
     prompt['suspicious buggy code statements'] = suspicious_code
     return prompt
 
prompt_patch = {
  "Role": "As a professional developers. You are responsible for fixing the bug in bug report and generating program repair patch.",
  "Instruction": """You should check the bug report information. The location of buggy code is provided. There are two type of information: method include bug, and suspicious buggy code statements. 
                    One is the method that includes a buggy code. Another is the suspicous buggy code that tirgger the bug in bug report. 
                    The suspicious buggy code statements may be very accurate. 
                    You need to fix the bug in the bug report and provide the fix patch. Please provide the fix patch refer the example format. Output in json format.""",
  "Bug report description": "",
  "Bug report title": "", 
  "Method include buggy code":"",
  "suspicious buggy code statements":"",
  "File name of checked code":"",
  "Fix Patch format Example":"", 
  "Question": "The patch for the bug in the bug report? (Only Output the fix patch for fix the bug in bug report refer the fix patch format example. No other words)"
}

prompt_test = {
  "Role": "As a professional testers. You are responsible for generating the fault triggering tests for bugs.",
  "Instruction": "Read the bug report information. Genearte the fault trigering test for the bug in the method. Output in JSON format",
  "Bug report description": "",
  "Bug report title": "", 
  "Method include buggy code":"",
  "suspicious buggy code statements":"",
  "Expected Output": """Can you provide one fault triggering test for the bug? (Please generate the Compilable test for trigger the bug in the bug report.) 
              """
}

bug_report_path = "../analysis_result/parsed_bug_reports/Lang/LANG-304.json"
fault_localization_path = "../analysis_result/GPT_response/fault_location/Lang/LANG-57.json"
save_file_path = "../analysis_result/GPT_response/patch_generation/Lang/patch/LANG-57.json"
test_file_path = "../analysis_result/GPT_response/patch_generation/Lang/test/LANG-57.json"
example_file_path = "../analysis_result/GPT_response/patch_generation/Patch_example_Lang_22.txt"
bug_report = load_json(bug_report_path)
fault_localization_info = load_json(fault_localization_path)
format_example = load_source_code(example_file_path)
api_key_path = "/Users/wang/Documents/project/api_key.json" # use your key
api_key = load_api_key(api_key_path)
client = OpenAI(api_key=api_key)
without_testing = True
if without_testing:
     prompt_patch = prompt_init_patch(prompt_patch, example=format_example, description=bug_report[0]['description'], title=preprocessing_title(bug_report[0]['title']), file_name=fault_localization_info['Question1'], method_buggy_code=fault_localization_info['Question3'], suspicious_code=fault_localization_info['Question4'])
     print(prompt_patch)
     patch_generation(client, prompt_patch, "", save_file_path)
else:
     prompt_test = prompt_init_test(prompt_test, description=bug_report[0]['description'], title=preprocessing_title(bug_report[0]['title']), method_buggy_code=fault_localization_info['Question3'], suspicious_code=fault_localization_info['Question4'])
     test_generation(client, prompt_test, "", test_file_path)
     test_case = load_json(test_file_path)['Fault triggering test']
     prompt_patch = prompt_init_patch(prompt_patch, example=format_example, description=bug_report[0]['description'], title=preprocessing_title(bug_report[0]['title']), file_name=fault_localization_info['Question1'], method_buggy_code=fault_localization_info['Question3'], suspicious_code=fault_localization_info['Question4'])
     prompt_patch['Test case'] = json.dumps(test_case)
     prompt_patch['Instruction'] = "..." #update intruction to tell there is test cases informaiton
     patch_generation(client, prompt_patch, "", save_file_path)
