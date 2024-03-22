import pandas as pd
import os 
import json
from openai import OpenAI
import re

def get_completion(client, prompt):
    messages = [{"role": "user", "content": prompt}]
    response = client.chat.completions.create(
        model="gpt-3.5-turbo-0125",
        # model="gpt-4",
        messages=messages,
        response_format={"type": "json_object"},
        temperature=0.3,
    )
    return response.choices[0].message.content

def patch_generation(client, prompt, few_shots, save_file_path ):
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
    
def preprocessing_title(report_title):
     processed_str = re.sub(r"\[LANG-\d+\]", "", report_title)
     return processed_str.strip()

def generate_patch():
     pass

def generate_test():
     pass

prompt_patch = {
  "Role": "As a professional developers. You are responsible for generating program repair patch.",
  "Instruction": "Read ",
  "Example:":"", 
  "Question": """ Question1: 
              """
}

prompt_testing = {
  "Role": "As a professional developers. You are responsible for generating program repair patch.",
  "Instruction": "Read ",
  "Question": """ Question1: 
              """
}

bug_report_path = ""
fault_localization_path = ""
bug_report = load_json(bug_report_path)
fault_localization_info = load_json(fault_localization_path)
api_key_path = "/Users/wang/Documents/project/api_key.json" # use your key
api_key = load_api_key(api_key_path)
client = OpenAI(api_key=api_key)
