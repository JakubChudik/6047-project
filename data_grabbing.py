# -*- coding: utf-8 -*-
"""
Created on Fri Nov 23 14:10:31 2018

@author: jakub
"""

import pandas as pd
import json
import requests

def get_case_counts_for_primary_site():
    """
    Return the number of cases for each primary site
    """
    cases_endpt = 'https://api.gdc.cancer.gov/cases'
    headers = {'Content-Type': 'application/json'}
    data2 = {
            "size":"0",
            "facets":"primary_site",
            }
    
    response = requests.post(cases_endpt, headers=headers, data = json.dumps(data2))
    response_dic = response.json()
    count_dic = {}
    
    for bucket in response_dic["data"]["aggregations"]["primary_site"]["buckets"]:
        count_dic[bucket["key"]] = count_dic.get(bucket["key"], 0) + bucket["doc_count"]
    
    return count_dic

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
        if rna_seq_uuid:
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
    url = "https://api.gdc.cancer.gov/cases/" + case_uuid
    params = (
        ('pretty', 'true'),
        ('expand', 'diagnoses'),
    )
    response = requests.get(url, params=params)
    diagnoses = response.json()['data']['diagnoses'][0]
    return (case_uuid, diagnoses)
