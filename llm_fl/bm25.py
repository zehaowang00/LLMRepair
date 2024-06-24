from langchain_community.retrievers import BM25Retriever

from langchain_core.documents import Document
import os
import pandas as pd
from llm_repair.unity_tool import get_report_map_dic, load_bug_report


def load_java_code():
    path = '/Users/wang/Documents/project/defects4j/Data/Lang/lang_60_b/'
    java_files = []

    for root, dirs, files in os.walk(path):
        for file in files:
            if file.endswith('.java'):
                file_path = os.path.join(root, file)
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    java_code = f.read()
                java_files.append(Document(page_content=java_code, metadata={"file_name": f"{file}"}))
    return java_files

report_map_path = '../dataset/bug_report/Lang/bug_report.csv'
bug_report = pd.read_csv(report_map_path)
bug_report_map = get_report_map_dic(bug_report)
for bug_id, report_id in bug_report_map.items():
    bug_report_des_path = '../analysis_result/parsed_bug_reports/Lang/' + bug_report_map[bug_id] + '.json'
    report_id = report_id.replace("_", "-")
    report = load_bug_report(bug_report_des_path)
    title = report[0]['title']
    description = report[0]['description']
    # java_code = load_java_code()
    # retriever = BM25Retriever.from_documents(java_code, k=5)
    query = title + description
    print(query)
    # result = retriever.invoke(query)
    # for doc in result:
    #     print(doc.metadata['file_name'])
