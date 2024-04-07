import pandas as pd
import os
import xml.etree.ElementTree as ET
import json
import pickle

def extract_report_info(xml_file_path, json_file_path):
    tree = ET.parse(xml_file_path)
    root = tree.getroot()

    report_features = []

    for item in root.findall(".//item"):
        title = item.find("title").text
        description = item.find("description").text
        report_features.append({"title": title, "description": description})

    with open(json_file_path, "w") as json_file:
        json.dump(report_features, json_file, indent=4)


projects = ["Lang"]
for project in projects:
    report_xml_folder = f"../dataset/bug_report/{project}/"
    extract_save_folder = f"../analysis_result/parsed_bug_reports/{project}/"
for filename in os.listdir(report_xml_folder):
    if filename.endswith(".xml"):
        xml_file_path = os.path.join(report_xml_folder, filename)
        json_file_path = os.path.join(
            extract_save_folder, filename.replace(".xml", ".json")
        )

        extract_report_info(xml_file_path, json_file_path)

