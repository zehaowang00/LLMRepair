from langchain_community.retrievers import BM25Retriever

from langchain_core.documents import Document
import os
import pandas as pd
from llm_repair.unity_tool import get_report_map_dic, load_bug_report


def load_java_code(path):
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
fl_result = dict()
for bug_id, report_id in bug_report_map.items():
    bug_report_des_path = '../analysis_result/parsed_bug_reports/Lang/' + bug_report_map[bug_id] + '.json'
    report_id = report_id.replace("_", "-")
    report = load_bug_report(bug_report_des_path)
    title = report[0]['title']
    description = report[0]['description']
    project_path = '/Users/wang/Documents/project/defects4j/Data/Lang/' + bug_id.lower() + '_b/'
    java_code = load_java_code(project_path)
    retriever = BM25Retriever.from_documents(java_code, k=8)
    query = title + description
    result = retriever.invoke(query)
    fl_result[bug_id] = [doc.metadata['file_name'] for doc in result]

fl_result_df = pd.DataFrame.from_dict(fl_result, orient='index')
fl_result_df.columns = ['rank1', 'rank2', 'rank3', 'rank4', 'rank5']
fl_result_df.to_csv('../analysis_result/bm25/fl/fl_result.csv', index_label='Bug_ID')