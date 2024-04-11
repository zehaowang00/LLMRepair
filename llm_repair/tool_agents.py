import re
from langchain_core.tools import tool

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

@tool
def get_method_code(class_code_path, method_name):
    """
    :param class_code_path:
    :param method_name:
    :return:
    """
    with open(class_code_path, "r") as f:
        try:
            class_code = f.read()
        except Exception as e:
            return "Cannot read source code"
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