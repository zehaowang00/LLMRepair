#!/bin/env python3
# -*- coding: utf-8 -*-
# version: Python3.X
""" Description
"""

__author__ = '__L1n__w@tch'

import re
import pandas as pd
import json


def get_report_map_dic(report_df):
    report_df['Lang ID'] = report_df['Bug ID'].apply(lambda x: 'LANG_' + str(x))
    report_df['Report ID'] = report_df['Report ID'].apply(lambda x: x.replace('-', '_'))
    return report_df.set_index('Lang ID')['Report ID'].to_dict()


def find_method_name_in_code(code, method_name):
    try:
        found_name = False
        if method_name in code:
            found_name = True
        if not found_name:
            small_method_name = re.findall(" ([^ ]+?\(.+)", method_name)[0]
            if small_method_name in code:
                method_name = small_method_name
                found_name = True
            else:
                small_small_method_name = re.findall("(.+?\([^,]+?),", small_method_name)[0]
                if small_small_method_name in code:
                    method_name = small_small_method_name
                    found_name = True
                else:
                    found_name = False
        if found_name:
            return method_name
        else:
            raise Exception(f"Can't find method: {method_name}")
    except Exception as e:
        raise Exception(f"Can't find method: {method_name}")


def get_method_code(class_code, method_name):
    method_code = list()
    stack = list()
    method_name = find_method_name_in_code(class_code, method_name)
    class_code = class_code.split("\n")
    while len(class_code) > 0:
        this_line = class_code.pop(0)
        if method_name not in this_line:
            continue
        # start get code
        method_code.append(this_line)
        while "{" not in this_line:
            this_line = class_code.pop(0)
            method_code.append(this_line)
        if "{" in this_line:
            stack.append("{")
        while len(stack) > 0:
            this_line = class_code.pop(0)
            method_code.append(this_line)
            if "{" in this_line:
                stack.append("{")
            if "}" in this_line:
                stack.pop()
    return "\n".join(method_code)


if __name__ == "__main__":
    report_map_path = '../dataset/bug_report/Lang/bug_report.csv'
    bug_report = pd.read_csv(report_map_path)
    bug_report_map = get_report_map_dic(bug_report)

    for bug_id, report_id in bug_report_map.items():
        json_path = '../analysis_result/GPT_response/fault_location/Lang/' + bug_id + '.json'
        report_id = report_id.replace("_", "-")
        if bug_id in ("LANG_30", "LANG_31", "LANG_59", "LANG_60", "LANG_61"):
            continue
        if bug_id == "LANG_3":
            print("debug")
        with open(json_path, "r", encoding="utf8") as f:
            json_data = json.load(f)
            for each_file in json_data["result"]:
                file_name = each_file["file_name"]
                source_code_path = '/Users/watch/Desktop/Code/defects4j/Data/Lang/' + bug_id.lower() + '_b/' + file_name
                if each_file["if_has_bug"].lower() == "no":
                    continue
                method_signature = each_file["method_level"].split(")")[0]
                with open(source_code_path, "r") as f:
                    try:
                        source_code = f.read()
                        result = get_method_code(source_code, method_signature)
                        # print(f"{bug_id} - {file_name} - {method_signature} - success")
                    except Exception as e:
                        print(f"{bug_id} - {file_name} - {method_signature} - fail: {e}")
