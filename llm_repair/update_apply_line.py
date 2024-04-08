#!/bin/env python3
# -*- coding: utf-8 -*-
# version: Python3.X

import os
import json
import re


def find_modify_code_line_in_project(source_code_path, patch_file_path):
    modify_lines = []
    modify_lines_index = {}
    with open(patch_file_path, 'r') as file:
        for line in file:
            if line.startswith('-') and not line.startswith('---'):
                processed_line = line.lstrip('-').strip()
                print(processed_line)
                modify_lines.append(processed_line)

    print(source_code_path)
    with open(source_code_path, 'r') as file:
        line_number = 1
        for source_line in file:
            for patch_line in modify_lines:
                if source_line == patch_line:
                    modify_lines_index['modify_lines'] = line_number
            line_number += 1
    return modify_lines_index


def index_patch_to_code_start(patch, source_code):
    patch = patch.split("\n")

    # index patch to code start
    while len(patch) > 0:
        this_line = patch.pop(0)
        if not this_line.startswith('@@'):
            continue
        this_line = this_line[this_line.rfind('@@') + 2:]
        if this_line.strip() != "":
            patch.insert(0, this_line)
        break
    # skip comment patch
    result = list()
    for line in patch:
        if line.strip().startswith("//"):
            if line.lstrip() + "\n" in source_code:
                result.append(line)
        else:
            result.append(line)
    return result


def generate_patch_file(source_code, patch):
    patch = index_patch_to_code_start(patch, source_code)
    source_code = source_code.split("\n")

    # insert patch
    patch_index, source_index = 0, 0
    result = list()
    while source_index < len(source_code) and patch_index < len(patch):
        if source_code[source_index].strip("- \n\t") != patch[patch_index].strip("- \n\t"):
            result.append(source_code[source_index])
            source_index += 1
        else:
            if not patch[patch_index].startswith('-'):
                result.append(source_code[source_index])
                source_index += 1
                patch_index += 1
            while patch_index < len(patch) and patch[patch_index].startswith('-') and \
                    source_code[source_index].strip("- \n\t") == patch[patch_index].strip("- \n\t"):
                source_index += 1
                patch_index += 1
            while patch_index < len(patch) and patch[patch_index].startswith('+'):
                result.append(patch[patch_index].lstrip('+'))
                patch_index += 1
            while patch_index < len(patch) and patch[patch_index].strip() == "":
                patch_index += 1
    while source_index < len(source_code):
        result.append(source_code[source_index])
        source_index += 1

    # check if patch end
    check_patch_end = True
    for i in range(patch_index, len(patch)):
        if patch[i].startswith("+") or patch[i].startswith("-"):
            check_patch_end = False
            break

    return "\n".join(result), check_patch_end


def load_json(file_path):
    with open(file_path, 'r') as file:
        data = json.load(file)
        return data


def load_file(file_path):
    with open(file_path, 'r') as file:
        return file.read()


def force_generate_patch_file(source_code, patch):
    delete_code = re.findall(r"-  (.+)", patch)
    # check if delete code exist
    for each_delete in delete_code:
        if each_delete.strip() not in source_code:
            return source_code, False
    # replace all delete code with add code
    add_code = re.findall(r"\+  (.+)", patch)
    if len(delete_code) == 1:
        pre_line = delete_code[0]
        after_patch = source_code.replace(pre_line, "\n".join(add_code))
        return after_patch, after_patch != source_code
    elif len(delete_code) == 0:
        pre_line = re.findall(r"(.+)\n\+  ", patch)[0]
        after_patch = source_code.replace(pre_line.strip(), pre_line + "\n" + "\n".join(add_code))
        return after_patch, after_patch != source_code
    else:
        return source_code, False


def main():
    projects = ['Lang']
    for project in projects:
        patch_file_path = "../analysis_result/GPT_response/patch_generation/Lang/patch/"
        total, normal_count, force_count = 0, 0, 0
        for filename in os.listdir(patch_file_path):
            if filename.endswith(".txt"):
                total += 1
                bug_id = filename.split(".")[0]
                patch_file = os.path.join(patch_file_path, filename)
                fault_localization_path = f"../analysis_result/GPT_response/fault_location/Lang/{bug_id}.json"
                fault_localization_info = load_json(fault_localization_path)
                modify_code_name = fault_localization_info['file_name']
                source_code_path = '/Users/watch/Desktop/Code/defects4j/Data/Lang/' + bug_id.lower() + '_b/' + modify_code_name
                try:
                    source_code, patch = load_file(source_code_path), load_file(patch_file)
                    generated_content, patch_end = generate_patch_file(source_code, patch)
                    if not patch_end:
                        print(f"[{bug_id}] normal patch fail, force patch")
                        generated_content, patch2_end = force_generate_patch_file(source_code, patch)
                        if not patch2_end:
                            raise Exception("Both normal patch and Force patch fail")
                        print(f"[{bug_id}] force patch successfully")
                        force_count += 1
                    else:
                        normal_count += 1
                    result = generated_content
                except Exception as e:
                    print(f"[{bug_id}]: {e}")
                    continue
        print(f"Total: {total}, Success: {force_count + normal_count}, Normal: {normal_count}, Force: {force_count}")


if __name__ == "__main__":
    main()
