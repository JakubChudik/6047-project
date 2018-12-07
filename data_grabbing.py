# -*- coding: utf-8 -*-
"""
Created on Fri Nov 23 14:10:31 2018

@author: jakub
"""

import json
import numpy as np
import os
import pandas as pd
import random
import requests
import shutil
import tempfile

random.seed(7)

def get_case_counts_for_primary_sites():
    """
    Return the number of cases for each primary site as a dictionary with keys being primary sites
    and values being number of cases
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

def make_files_for_cases(size):
    """
    Create csv file with [primary_site, case_uuid, rna_seq_uuid] for all primary sites that have
    at least size number of cases with rna_seq files and save them to data/
    """
    case_counts = get_case_counts_for_primary_sites()
    for primary_site in case_counts:
        if case_counts[primary_site] >= size:
            temp_file = get_all_cases_from_primary_site(primary_site)
            if len(temp_file) >= size:
                df = pd.DataFrame(temp_file)
                df.to_csv("data/" + primary_site + "_case_rna_uuids.csv", sep = ",")
    return

def download_rna_seq(rna_seq_uuid_list, dirpath):
    """
    Download a set of files RNA-Seq files using a post request with RNA-Seq UUIDS in json as per
    https://docs.gdc.cancer.gov/API/Users_Guide/Downloading_Files/ section
    POST REQUEST WITH FORM DATA PAYLOAD

    If only a single file - load using pandas.read_csv(filenam, sep="\t")
    If downloading multiple files, the structure is more nested and complicated
    """
    data_dict = {}
    data_dict["ids"] = rna_seq_uuid_list

    headers = {'Content-Type': 'application/json'}
    data = json.dumps(data_dict)

    try:
        response = requests.post('https://api.gdc.cancer.gov/data', headers=headers, data=data)
        filename = os.path.join(dirpath,response.headers["Content-Disposition"].split("filename=")[1])

        with open(filename, "wb") as file:
            file.write(response.content)
        file.close()
        print(filename)
        return filename
    except:
        return None

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
    try:
        diagnoses = response.json()['data']['diagnoses'][0]
        data = {'case_uuid':case_uuid,'clinical_data':diagnoses}
    except:
        return None
    return data


def get_random_cases(size = 20):
    """
    Get size number of random cases from each primary site and save them in
    random_case_selections.csv
    """
    temp_dfs = []
    for file in os.listdir("data"):
        df = pd.read_csv("data/" + file, header = 1)
        df = df.drop(columns = ['0'])
        rows = random.sample(range(0, len(df) -1), size)
        temp_dfs.append(df.iloc[rows])

    res = pd.concat(temp_dfs)
    res.to_csv("random_case_selection_size_"+str(size)+".csv")
    return res

def data_transform(filename):
    """
    takes in a csv file with [primary_site, case_uuid, rna_seq_uuid], downloads the
    corresponding rna_seq file and combines all the data into a single file
    that can be used to perform subsequent analysis
    """

    #{case_ids: [case_uuid1,case_uuid2,...], rna_id1:[case1_val,case2_val,...], rna_id2:[...],....}
    dirpath = tempfile.mkdtemp()
    data = {}
    with open(filename,'r') as file:
        lines = file.readlines()
        for i in range(2,len(lines)):
            if i % 20 == 0:
                case = lines[i].split(',')
                try:
                    case_rna = pd.read_csv(download_rna_seq([case[3].rstrip('\n')],dirpath),sep="\t",names = ['rna_id','level'])
                    try:
                        data['case_uuid'].append(case[2])
                    except:
                        data['case_uuid'] = [case[2]]
                    for index, row in case_rna.iterrows():
                        try:
                            data[row['rna_id']].append(row['level'])
                        except:
                            data[row['rna_id']] = [row['level']]
                except:
                    continue
    shutil.rmtree(dirpath)
    return data

def combine_clinical_genetic(genetic):
    '''
    adds an additonal key of diagnoses age to our data
    dictionary which previously only contains a key for the
    case uuid and each measured gene
    '''
    cases = genetic['case_uuid']
    for i in range(len(cases)):
        clinical = get_demo_and_clin_data(cases[i])
        if clinical == None:
                try:
                    genetic['diagnoses_age'].append(0)
                except:
                    genetic['diagnoses_age'] = [0]
        else:
            age = clinical['clinical_data']['age_at_diagnosis']
            try:
                genetic['diagnoses_age'].append(age)
            except:
                genetic['diagnoses_age'] = [age]
    return genetic


# make_files_for_cases(100)
# print(get_demo_and_clin_data('cee553c8-460d-436b-b55d-8f41624816cc'))
def main():
    genetic_data = data_transform('random_case_selection_size_15.csv')
    final = combine_clinical_genetic(genetic_data)
    print(final['diagnoses_age'])
    with open('cleanData.json', 'w') as outfile:
        json.dump(final, outfile)

main()
