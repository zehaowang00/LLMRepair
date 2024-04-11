import getpass
import os
import json
from langchain_core.messages import (
    AIMessage,
    BaseMessage,
    ChatMessage,
    FunctionMessage,
    HumanMessage,
)
import pandas as pd
import random
from langchain.tools.render import format_tool_to_openai_function
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langgraph.graph import END, StateGraph
from langgraph.prebuilt.tool_executor import ToolExecutor, ToolInvocation
from langchain_core.tools import tool
from tool_agents import get_method_code, patch_generation, test_generation, save_patch_result
import operator
from typing import Annotated, List, Sequence, Tuple, TypedDict, Union
#from langchain.agents import create_openai_functions_agent
from langchain.tools.render import format_tool_to_openai_function
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_openai import ChatOpenAI
from typing_extensions import TypedDict
import functools
from unity_tool import get_report_map_dic, load_bug_report, load_json, load_api_key
from typing import Any
from openai import OpenAI

def _set_if_undefined(var: str):
    if not os.environ.get(var):
        os.environ[var] = getpass(f"Please provide your {var}")
def create_agent(llm, tools, system_message: str):
    """Create an agent."""
    functions = [format_tool_to_openai_function(t) for t in tools]

    prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                "You are a helpful AI assistant, collaborating with other assistants."
                " Use the provided tools to progress towards answering the question."
                " If you are unable to fully answer, that's OK, another assistant with different tools "
                " will help where you left off. Execute what you can to make progress."
                " If you or any of the other assistants have the final answer or deliverable,"
                #" prefix your response with FINAL ANSWER so the team knows to stop."
                " You don't need to thank you for each other once the work is done."
                " You have access to the following tools: {tool_names}.\n{system_message}",
            ),
            MessagesPlaceholder(variable_name="messages"),
        ]
    )
    prompt = prompt.partial(system_message=system_message)
    prompt = prompt.partial(tool_names=", ".join([tool.name for tool in tools]))
    return prompt | llm.bind_functions(functions)
class AgentState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], operator.add]
    bug_id: str
    sender: str
    bug_report_describe: str
    bug_report_title: str
    method_code_file_path: str
    client: Any
    json_result: Any

def agent_node(state, agent, name):
    result = agent.invoke(state)
    if isinstance(state["messages"][-1], FunctionMessage):
        state["method_code_body"] = "d"
    # We convert the agent output into a format that is suitable to append to the global state
    if isinstance(result, FunctionMessage):
        pass
    else:
        result = HumanMessage(**result.dict(exclude={"type", "name"}), name=name)
    return {
        "messages": [result],
        # Since we have a strict workflow, we can
        # track the sender so we know who to pass to next.
        "sender": name,
    }

def tool_node(state):
    """This runs tools in the graph

    It takes in an agent action and calls that tool and returns the result."""
    messages = state["messages"]
    # Based on the continue condition
    # we know the last message involves a function call
    last_message = messages[-1]
    # We construct an ToolInvocation from the function_call
    tool_input = json.loads(
        last_message.additional_kwargs["function_call"]["arguments"]
    )
    # We can pass single-arg inputs by value
    if len(tool_input) == 1 and "__arg1" in tool_input:
        tool_input = next(iter(tool_input.values()))
    tool_name = last_message.additional_kwargs["function_call"]["name"]
    action = ToolInvocation(
        tool=tool_name,
        tool_input={"state":state},
    )
    # We call the tool_executor and get back a response
    response = tool_executor.invoke(action)
    # We use the response to create a FunctionMessage
    function_message = FunctionMessage(
        content=f"{tool_name} response: {str(response)}", name=action.tool
    )
    # We return a list, because this will get added to the existing list
    return {"messages": [function_message]}

def router(state):
    # This is the router
    messages = state["messages"]
    last_message = messages[-1]
    if "function_call" in last_message.additional_kwargs:
        # The previus agent is invoking a tool
        return "call_tool"
    if "FINAL ANSWER" in last_message.content:
        # Any agent decided the work is done
        return "end"
    return "continue"

_set_if_undefined("OPENAI_API_KEY")
llm = ChatOpenAI(model="gpt-3.5-turbo")
system_message_developer = ("You are responsible for generating the patch for program repair. You need follow the steps: "
                            "1. Get the buggy method code"
                            "2. You need to talk to another agent to get the fault-triggering test cases. "
                            "3. You need to generate the patch for the bug."
                            "4. You need to share your generated patch to another agent for checking." 
                            "5. Once another agent agree that your patch can pass the test, you can save the patch result")

system_message_tester = ("You are responsible for generating the testing cases for the bug in the bug report based on the buggy method."                           "You need to follow the following steps: "
                         "1. get the buggy method code" 
                         "2. for the buggy method, generate the fault triggering test for triggering the bug describe in the bug report." "3. Another agent will give you the patch that is used to fix program. You need to check if the patch can pass" "the test and fix the bug in the bug report and tell the result to another agent.")  
developer_agent = create_agent(
    llm,
    [get_method_code, patch_generation, save_patch_result],
    system_message=system_message_developer,
)
developer_node = functools.partial(agent_node, agent=developer_agent, name="Developer")

# Performance agent
tester_agent = create_agent(
    llm,
    [get_method_code, test_generation],
    system_message=system_message_tester,
)
tester_node = functools.partial(
    agent_node, agent=tester_agent, name="Tester"
)

tools = [get_method_code, patch_generation, test_generation, save_patch_result]
tool_executor = ToolExecutor(tools)

workflow = StateGraph(AgentState)
workflow.add_node("Developer", developer_node)
workflow.add_node("Tester", tester_node)
workflow.add_node("call_tool", tool_node)
workflow.add_conditional_edges(
    "Developer",
    router,
    {"continue": "Tester", "call_tool": "call_tool", "end": END},
)
workflow.add_conditional_edges(
    "Tester",
    router,
    {"continue": "Developer", "call_tool": "call_tool", "end": END},
)

workflow.add_conditional_edges(
    "call_tool",
    # Each agent node updates the 'sender' field
    # the tool calling node does not, meaning
    # this edge will route back to the original agent
    # who invoked the tool
    lambda x: x["sender"],
    {
        "Developer": "Developer",
        "Tester": "Tester",
    },
)
workflow.set_entry_point("Developer")
graph = workflow.compile()

fault_path = '../analysis_result/GPT_response/fault_location/Lang_reflection'
report_map_path = '../dataset/bug_report/Lang/bug_report.csv'
bug_report = pd.read_csv(report_map_path)
bug_report_map = get_report_map_dic(bug_report)
api_key_path = "/Users/wang/Documents/project/api_key.json"  # use your key
api_key = load_api_key(api_key_path)
client = OpenAI(api_key=api_key)
for filename in os.listdir(fault_path):
    if filename.endswith(".json"):
        bug_id = filename.split('.')[0]
        bug_report_des_path = '../analysis_result/parsed_bug_reports/Lang/' + bug_report_map[bug_id] + '.json'
        #report_id = report_id.replace("_", "-")
        report = load_bug_report(bug_report_des_path)
        bug_description = report[0]['description']
        bug_title = report[0]['title']
        message = f"please generate the patch to fix the target bug"
        result = load_json(os.path.join(fault_path, filename))['result']
        short_code_path = load_json(os.path.join(fault_path, filename))['result'][0]['file_name']
        method_code_file_path = '/Users/wang/Documents/project/defects4j/Data/Lang/' + bug_id.lower() + '_b/' + short_code_path
        input = {"messages": [HumanMessage(content=message)], "bug_id": bug_id, "bug_report_title": bug_title,
                 "bug_report_describe": bug_description, "method_code_file_path": method_code_file_path,
                 'json_result':result, 'client': client}
        graph.invoke(input)
#index = 0
# for option_name in option_names:
#     message = f"Target configuration: {option_name} for {project} project"
#     input = {"messages": [HumanMessage(content=message)]}
#     try:
#         graph.invoke(input)
#     except Exception:
#         print("failed: " + str(option_name))
#     index += 1
#     print("processed: " + str(index))

# for s in graph.stream(
#     {
#         "messages": [
#             HumanMessage(
#                 content="Target configuration: max_concurrent_automatic_sstable_upgrades for cassandra project"
#             )
#         ],
#     },
#     # Maximum number of steps to take in the graph
#     {"recursion_limit": 10},
# ):
#     print(s)
#     print("----")






