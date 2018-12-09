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
                file.get("analysis", {}).get("workflow_type", "") == "HTSeq - Counts"
                ):
                    rna_seq_uuid = file["file_id"]
        if rna_seq_uuid:
            res.append([primary_site, case_uuid, rna_seq_uuid])
    return res

def get_all_cases_from_primary_site(primary_site = "Colon"):
    """
    Return a list of lists of primary_site, case_uuid and rna-seq_file_uuid for all cases
    which fall within primary site primary_site. RNA-Seq file is type "HTSeq - Counts" see
    https://docs.gdc.cancer.gov/Encyclopedia/pages/HTSeq-FPKM-UQ/ for details
    """
    res = []
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
        print("one done")
        if case_counts[primary_site] >= size:
            temp_file = get_all_cases_from_primary_site(primary_site)
            if len(temp_file) >= size:
                df = pd.DataFrame(temp_file, columns = ["primary_site","case_uuid", "rna_seq_uuid"])
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
        ('expand', 'diagnoses,demographic'),
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
        df = pd.read_csv("data/" + file, header = 1, names = ['0', "primary_site", "case_uuid", "rna_seq_uuid"])
        df = df.drop(columns=['0'])
        rows = random.sample(range(0, len(df) -1), size)
        temp_dfs.append(df.iloc[rows])

    res = pd.concat(temp_dfs)
    filename = "random_case_selection_size_"+str(size)+".csv"
    res.to_csv(filename)
    return filename

def data_transform(filename):
    """
    takes in a csv file with [primary_site, case_uuid, rna_seq_uuid], downloads the
    corresponding rna_seq file and combines all the data into a single file
    that can be used to perform subsequent analysis
    """
    gap = 1
    dirpath = tempfile.mkdtemp()
    pd_list = []
    file_df = pd.read_csv(filename, header = 0)
    for line in range(len(file_df)):
        if line % gap == 0:
            print(line,len(file_df))
            rna_uuid = file_df.iloc[line]["rna_seq_uuid"]
            case_uuid = file_df.iloc[line]["case_uuid"]
            try:
                df = pd.read_csv(download_rna_seq([rna_uuid], dirpath),sep="\t",names = ['rna_id','value'])
                df = df.transpose()
                df.columns = df.iloc[0]
                df = df.drop(df.index[0])
                df["case_uuid"] = str(case_uuid)
                pd_list.append(df.transpose())
            except:
                continue

    final_df = pd.concat(pd_list, axis=1, sort=False)
    final_df = final_df.transpose()

    return final_df

def convertTumorStage(tumor_stage):
    """
    convert tumor stage string to number. For example iiic becomes 3
    """
    stages= {0:0,1:1,2:3,3:5}
    sub_stages = {'a':0,'b':1,'c':2}
    if tumor_stage == "not reported":
        return None
    else:
        stage = tumor_stage.split(' ')[1]
        if stage.count('v') > 0:
            return 8
        else:
            count = stage.count('i')
            count = stages[count]
            if stage[-1] in ['a','b','c']:
                return count + sub_stages[stage[-1]]
            else:
                return count




def create_clinical_df(case_ids, feature):
    '''
    adds an additonal key of diagnoses age to our data
    dictionary which previously only contains a key for the
    case uuid and each measured gene
    '''
    data = {'case_uuid':[]}
    for i in range(len(case_ids)):
        data['case_uuid'].append(case_ids[i])
        clinical = get_demo_and_clin_data(case_ids[i])
        try:
            stage = convertTumorStage(clinical['clinical_data'][feature])
            try:
                data[feature].append(stage)
            except:
                data[feature] = [stage]
        except:
            try:
                data[feature].append(feature)
            except:
                data[feature] = [None]

    data = pd.DataFrame(data)
    return data


def add_days_to_death(filename):
    original_data = pd.DataFrame.from_csv("rna_data/" + filename)
    case_ids = list(original_data.case_uuid)
    data = {'case_uuid':[]}
    for i in range(len(case_ids)):
        data['case_uuid'].append(case_ids[i])
        clinical = get_demo_and_clin_data(case_ids[i])
        try:
            death = clinical['clinical_data']['days_to_death']
            try:
                data['days_to_death'].append(death)
            except:
                data['days_to_death'] = [death]
        except:
            try:
                data['days_to_death'].append(None)
            except:
                data['days_to_death'] = [None]

    file_name = "data_death/" + filename.split(".csv")[0] + "_add_death" + ".csv"

    data = pd.DataFrame(data)
    if not data.empty:
        final = pd.merge(original_data, data, left_on = 'case_uuid', right_on = 'case_uuid', how = 'outer')
        final = final[final['days_to_death'].notnull()]
        final.to_csv(file_name)
        return final

#add_days_to_death('cleanDataStage.csv')
#

def normalize_df(df):
    count = 1
    for col in df.columns:
        if count % 1000 == 0:
            print("normalized: " + str(count))
        if col != "case_uuid":
            df[col] = (df[col] - df[col].mean()) / df[col].std()
        count += 1
    return df

def make_full_rna_files():
    for file in os.listdir("data"):
        site = file.split("_")[0]
        f = 'data/' + site + '_case_rna_uuids.csv'
        if site == "Breast" or site == "Colon":
            genetic_data = data_transform(f)

            clinical_data = create_clinical_df(list(genetic_data.case_uuid), "tumor_stage")

            final = pd.merge(genetic_data, clinical_data, left_on = 'case_uuid', right_on = 'case_uuid', how = 'outer')
            final = final[final['tumor_stage'].notnull()]
#            final = final[final["tumor_stage"] != "tumor_stage"]
            final.to_csv(site + "_full_rna_stage_data"+".csv")
        print(site + " done")

def make_full_rna_files_from_existing(filename):
    site = "Breast"
    original_data = pd.DataFrame.from_csv(filename)
    genetic_data = original_data.drop(columns=['tumor_stage'])
    clinical_data = create_clinical_df(list(genetic_data.case_uuid), "tumor_stage")

    final = pd.merge(genetic_data, clinical_data, left_on = 'case_uuid', right_on = 'case_uuid', how = 'outer')
    final = final[final['tumor_stage'].notnull()]
#            final = final[final["tumor_stage"] != "tumor_stage"]
    final.to_csv('new_stages/' + site + "_full_rna_stage_data_new"+".csv")

make_full_rna_files_from_existing('rna_data/Breast_full_rna_stage_data.csv')

#def main():
#    site = "Colon"
#    genetic_data = data_transform('data/' + site + '_case_rna_uuids.csv')
##    genetic_data = normalize_df(genetic_data)
##    genetic_data.fillna(genetic_data.mean(), inplace=True)
#
#    clinical_data = create_clinical_df(list(genetic_data.case_uuid), "tumor_stage")
#
#    #merge genetic and clinical data here
#    final = pd.merge(genetic_data, clinical_data, left_on = 'case_uuid', right_on = 'case_uuid', how = 'outer')
#    final = final[final['tumor_stage'].notnull()]
#    final = final[final["tumor_stage"] != "tumor_stage"]
#    final.to_csv(site + "_full_rna_stage_data"+".csv")
#
#
#    make_full_rna_files()
#res = 0
#for file in os.listdir("rna_data"):
#    print("doing: " + file)
#    if "Adrenal" not in file and "Bladder" not in file:
#        res = add_days_to_death(file)
#
#main()
