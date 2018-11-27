# -*- coding: utf-8 -*-
"""
Created on Fri Nov 23 14:10:31 2018

@author: jakub
"""

from selenium import webdriver
import pandas as pd
import json
import requests

options = webdriver.ChromeOptions()
options.add_argument("headless")

def get_project_ids(size = 1):
    """
    Return ids of all projects
    """
    driver = webdriver.Chrome(executable_path = "utils/chromedriver.exe", chrome_options=options)
    url = ("https://api.gdc.cancer.gov/projects?from=0&size=" + str(size) + 
           "&sort=project.project_id:asc&pretty=true")
    driver.get(url)
    a = driver.page_source.split('"project_id"')
    ids = []
    for i in a[1:]:
        temp = i.split('"')
        ids.append(temp[1])
    return ids

def get_case_count_per_project(projects):
    """
    Return a dicrionary of number of cases with RNA-Seq data for each project from projects
    """
    driver = webdriver.Chrome(executable_path = "utils/chromedriver.exe", chrome_options=options)
    dic = {}
    for project in projects:
        url = ("https://api.gdc.cancer.gov/projects/" + project +
               "?expand=summary,summary.experimental_strategies,&pretty=true")
        driver.get(url)
        a = driver.page_source
        if "RNA-Seq" in a:
            a = a.split('"experimental_strategy": "RNA-Seq"')[0].split('"case_count": ')
            dic[project] = int(a[-1].split(",")[0])    
        else:
             dic[project] = 0
    return dic

def get_cases_response(primary_site, offset):
    """
    Get 10 cases from primary_site including experimental strategy, and analysis type for each 
    case using GDC API, see guide here https://docs.gdc.cancer.gov/API/PDF/API_UG.pdf
    Returns a python request response
    """
    files_endpt = 'https://api.gdc.cancer.gov/cases'
    filters = {
            "op":"and",
            "content":[
                    {
                    "op":"=",
                    "content":
                        {
                        "field":"cases.primary_site",
                        "value":[primary_site]
                        },
                    },
                    {
                    "op":"in",
                    "content":
                        {
                        "field":"files.experimental_strategy",
                        "value":["RNA-Seq"]
                        },
                    }
                ]
            }
    params = {
                "filters": json.dumps(filters),
                'fields': 'case_id,files.file_id,files.experimental_strategy,files.access,files.analysis.workflow_type', 
                'size':"10", 
                'from':str(offset * 10), 
                'pretty':"true"
                }
    return requests.get(files_endpt, params = params)

def get_all_cases_from_response(response, primary_site):
    """
    Return a list of lists of primary_site, case_uuid and rna-seq_file_uuid for all cases in a 
    requests response response.
    """
    res = []
    for case in response.json()["data"]["hits"]:
        case_uuid = case["case_id"]
        
        #find RNA-Seq UUID
        rna_seq_uuid = None
        for file in case["files"]:
            if (
                file.get("access", "") == "open" and 
                file.get("experimental_strategy", "") == "RNA-Seq" and
                file.get("analysis", {}).get("workflow_type", "") == "HTSeq - FPKM"
                ):
                    rna_seq_uuid = file["file_id"]
                    
        res.append([primary_site, case_uuid, rna_seq_uuid])
    return res

def get_all_cases_from_primary_site(primary_site = "Colon"):
    """
    Return a list of lists of primary_site, case_uuid and rna-seq_file_uuid for all cases
    which fall within primary site primary_site. RNA-Seq file is type "HTSeq - FPKM-UQ" see
    https://docs.gdc.cancer.gov/Encyclopedia/pages/HTSeq-FPKM-UQ/ for details
    """
    res = [["primary_site","case_uuid", "rna_seq_uuid"]]
    offset = -1
    response = get_cases_response(primary_site, 0)
    while offset < response.json()["data"]["pagination"]["pages"]:
        offset += 1
        response = get_cases_response(primary_site, offset)
        res += get_all_cases_from_response(response, primary_site)
    return res
        
def download_rna_seqs(rna_seq_urls, filename = "data.tar"):
    """
    Download a set of files RNA-Seq files using a post request with RNA-Seq UUIDS in json as per 
    https://docs.gdc.cancer.gov/API/Users_Guide/Downloading_Files/ section 
    POST REQUEST WITH FORM DATA PAYLOAD 
    """
    data_dict = {}
    data_dict["ids"] = rna_seq_urls
    
    headers = {'Content-Type': 'application/json'}
    data = json.dumps(data_dict)
        
    response = requests.post('https://api.gdc.cancer.gov/data', headers=headers, data=data)
    with open(filename, "wb") as file:
        file.write(response.content)
    file.close()

def get_demo_and_clin_data(case_uuid):
    """
    Return demographic and clinical data associated with a case_uuid
    """
    url = "https://portal.gdc.cancer.gov/cases/" + case_uuid
    raise NotImplementedError 












