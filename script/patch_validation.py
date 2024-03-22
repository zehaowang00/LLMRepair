import pandas as pd
import os 
import json

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

def patch_validate(client, prompt, few_shots, save_file_path ):
    response = get_completion(client, json.dumps(prompt))
    with open(save_file_path, 'w') as file:
       json.dump(json.loads(response), file, indent=4)

prompt_validation = {
  "Role": "As a professional developers. You are responsible for generating program repair patch.",
  "Instruction": "Read ",
  "Question": """ Question1: 
              """
}