import re
from langchain_core.tools import tool
import json
from unity_tool import get_completion

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
def get_method_code(state):
    """
    :param state: it is the state message in the lang graph for communication.
    """
    class_code_path = state['method_code_file_path']
    method_name = state['json_result'][0]["method_level"].split(")")[0]
    try:
        with open(class_code_path, "r") as f:
            class_code = f.read()
    except Exception as e:
        return "Cannot read source code"
    method_code = list()
    stack = list()
    method_name = find_method_name_in_code(class_code, method_name)
    class_code = class_code.split("\n")
    try:
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
    except:
        return "cannot find method_code"
    return "\n".join(method_code)

# @tool
# def save_patch_result(state):
#     """
#     :param state: it is the state message in the lang graph for communication.
#     The function is used for storing the generated patch result into a file. Then the teamwork can be closed.
#     """
#     bug_id = state['bug_id']
#     block_level_code = state['json_result'][0]["block_level"]
#     save_file_path = f"../analysis_result/GPT_response/patch_generation/Lang/patch/{bug_id}.json"
#     with open(save_file_path.replace('.json', '.txt'), 'w') as file:
#         file.write(json.loads(patch))
#     with open(save_file_path, 'w') as file:
#         json.dump(json.loads(patch), file, indent=4)


@tool
def patch_generation(state):
    """
    :param state: it is the state message in the lang graph for communication.
    """
    client = state['client']
    bug_id = state['bug_id']
    block_level_code = state['json_result'][0]["block_level"]
    save_file_path = f"../analysis_result/GPT_response/patch_generation/Lang/patch/{bug_id}.json"
    prompt = {
    "Role": "As a professional developers. You are responsible for fixing the bug in bug report and generating program repair patch.",
    "Instruction": """You should check the bug report information. The location of buggy code is provided. There are two type of information: method include bug, and suspicious buggy code statements. 
                    One is the method that includes a buggy code. Another is the suspicous buggy code that tirgger the bug in bug report. 
                    The suspicious buggy code statements may be not very accurate. 
                    You need to fix the bug in the bug report and provide the fix patch. Please provide the fix patch refer the example format. The fix patch should not cause compile error. Output in json format. Required Json Key: Fix Patch""",
    "Bug report description": state['bug_report_describe'],
    "Bug report title": state['bug_report_title'],
    "Method include buggy code": state['method_code_body'],
    "suspicious buggy code statements": block_level_code,
    "Fix Patch format Example": """diff --git a/src/main/java/org/apache/commons/lang3/math/Fraction.java b/src/main/java/org/apache/commons/lang3/math/Fraction.java
index b36a156..0fdfc36 100644
--- a/src/main/java/org/apache/commons/lang3/math/Fraction.java
+++ b/src/main/java/org/apache/commons/lang3/math/Fraction.java
@@ -581,7 +581,7 @@ public final class Fraction extends Number implements Comparable<Fraction> {
     private static int greatestCommonDivisor(int u, int v) {
         // From Commons Math:
         //if either operand is abs 1, return 1:
-        if (Math.abs(u) <= 1 || Math.abs(v) <= 1) {
+        if (Math.abs(u)==1 || Math.abs(v) <= 1) {
             return 1;
         }
         // keep u and v negative, as negative integers range down to""",
    "Question": """The patch for the bug in the bug report? (Only Output the fix patch for fix the bug in bug report refer the fix patch format example. No other words)."""
    }
    for i in range(-1, -len(state['messages']), -1):
        if state['messages'][i].name == 'Tester':
            feedback = state['messages'][i].content
            prompt['feedback from expert testers about generated patch'] = feedback
            break
    #feedback = state['messages'][-1].content
             # if len(feedback) > 0:
        # prompt['feedback from expert developers about generated patch'] = feedback
    response = get_completion(client, json.dumps(prompt))
    with open(save_file_path.replace('.json', '.txt'), 'w') as file:
        file.write(json.loads(response)['Fix Patch'])
    with open(save_file_path, 'w') as file:
        json.dump(json.loads(response), file, indent=4)
    return response

@tool
def test_generation(state):
    """
    :param client: client
    :param prompt: prompt
    :param few_shots: asdf
    :param save_file_path: asdf
    :return:
    """
    client = state['client']
    bug_id = state['bug_id']
    block_level_code = state['json_result'][0]["block_level"]
    save_file_path = f"../analysis_result/GPT_response/patch_generation/Lang/test/{bug_id}.json"
    prompt = prompt_test = {
    "Role": "As a professional testers. You are responsible for generating the fault triggering tests for bugs.",
    "Instruction": "Read the bug report information. Genearte the fault trigering test for the bug in the method. Output in JSON format. Please use the json key:Fault Triggering Test",
    "Bug report description": state['bug_report_describe'],
    "Bug report title": state['bug_report_title'],
    "Method include buggy code": state['method_code_body'],
    "suspicious buggy code statements": block_level_code,
    "Expected Output": """Fault Triggering Test: Can you provide one test case for testing the bug? (Please generate a complete and compilable test case code for trigger the bug in the bug report. No other words) 
              """
    }
    #feedback = state['messages'][-1].content
    #if len(feedback) > 0:
        #prompt['feedback from expert developers about generated patch'] = feedback
    response = get_completion(client, json.dumps(prompt))
    with open(save_file_path, 'w') as file:
        json.dump(json.loads(response), file, indent=4)
    return response