import pandas as pd
import os 
import requests

def download_file(url, folder_path):
    local_filename = url.split('/')[-1].replace('-','_')
    full_path = os.path.join(folder_path, local_filename)
    with requests.get(url, stream=True) as r:
        r.raise_for_status()
        with open(full_path, 'wb') as f:
            for chunk in r.iter_content(chunk_size=8192): 
                f.write(chunk)

#folder_path = '/Users/wang/Documents/project/LLMRepair/dataset/bug_report/Lang/'
folder_path = '/Users/linqiangguo/PycharmProjects/LLMRepair/dataset/bug_report/Lang'
data = pd.read_csv(folder_path +'bug_report.csv', usecols=['Report ID','Report URL'])
url_reports = data.set_index('Report ID')['Report URL'].to_dict()
for id, url in url_reports.items():
    xml_url = url.replace('/browse/', '/si/jira.issueviews:issue-xml/') + f'/{id}.xml'
    try:
        download_file(xml_url, folder_path)
    except Exception as e:
        print(f"Failed to download XML for {url}: {e}")

print('Done')
