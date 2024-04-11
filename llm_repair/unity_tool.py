import json
import re


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


def get_report_map_dic(report_df):
    report_df['Lang ID'] = report_df['Bug ID'].apply(lambda x: 'LANG_' + str(x))
    report_df['Report ID'] = report_df['Report ID'].apply(lambda x: x.replace('-', '_'))
    return report_df.set_index('Lang ID')['Report ID'].to_dict()


def load_json(file_path):
    with open(file_path, 'r') as file:
        data = json.load(file)
        return data


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
