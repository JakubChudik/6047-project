# -*- coding: utf-8 -*-
"""
Created on Fri Nov 23 14:10:31 2018

@author: jakub
"""

from selenium import webdriver
import pandas as pd
import json
import requests

def get_project_ids(size = 1):
    """
    Return ids of all projects
    """
    driver = webdriver.Chrome(executable_path = "utils/chromedriver.exe")
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
    driver = webdriver.Chrome(executable_path = "utils/chromedriver.exe")
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

def get_all_cases_from_project(project = "TCGA-LUSC"):
    """
    Return a dictionary of all cases in the project project.
    Keys are case-ids, values are case-url for each case-id
    """
    driver = webdriver.Chrome(executable_path = "utils/chromedriver.exe")
    experiment_strategy = "RNA-Seq"
    offset = "0"
    cases_size = 40
    url =   ("https://portal.gdc.cancer.gov/repository?cases_size=" + str(cases_size) + 
             "&cases_offset=" + offset + "&facetTab=cases&filters=" +
             "%7B%22op%22%3A%22and%22%2C%22content%22%3A%5B%7B%22op%22%3A%22in%22%2C%22content" + 
             "%22%3A%7B%22field%22%3A%22cases.project.project_id%22%2C%22value%22%3A%5B%22" +
             project + "%22%5D%7D%7D%2C%7B%22op%22%3A%22in%22%2C%22content%22%3A%7B%22field" +
             "%22%3A%22files.experimental_strategy%22%2C%22value%22%3A%5B%22" + 
             experiment_strategy + 
             "%22%5D%7D%7D%5D%7D&searchTableTab=cases")
    driver.get(url)
    
    #wait for page to load
    driver.implicitly_wait(3)
    driver.switch_to_active_element().find_element_by_css_selector(".undefined.button.css-oe4so").click()
 
    #wait for page to load
    driver.implicitly_wait(3)
    
    #number of cases in this project
    n_cases = int(driver.find_element_by_class_name("test-showing").text.split("\n")[-2])
    case_dict = {}
    
    for i in range(0, (n_cases // cases_size) +1):
        offset = i * cases_size
        url =   ("https://portal.gdc.cancer.gov/repository?cases_size=" + str(cases_size) + 
             "&cases_offset=" + str(offset) + "&facetTab=cases&filters=" +
             "%7B%22op%22%3A%22and%22%2C%22content%22%3A%5B%7B%22op%22%3A%22in%22%2C%22content" + 
             "%22%3A%7B%22field%22%3A%22cases.project.project_id%22%2C%22value%22%3A%5B%22" +
             project + "%22%5D%7D%7D%2C%7B%22op%22%3A%22in%22%2C%22content%22%3A%7B%22field" +
             "%22%3A%22files.experimental_strategy%22%2C%22value%22%3A%5B%22" + 
             experiment_strategy + 
             "%22%5D%7D%7D%5D%7D&searchTableTab=cases")
        driver.get(url)
        for case_row_id in range(0, cases_size):
            try:
                temp = driver.find_element_by_id("row-" + str(case_row_id) + "-case-link")
            except:
                break
            case_id = temp.text
            case_url = temp.get_attribute("href").split("?")[0].split("cases/")[1]
            case_dict[case_id] = case_url
    
    return case_dict

def get_rna_seq_file_url(case_uuid):
    """
    Return url to RNA-Seq data related to a case_uuid
    """
    driver = webdriver.Chrome(executable_path = "utils/chromedriver.exe")
    url =   ("https://portal.gdc.cancer.gov/repository?filters=%7B%22op%22%3A%22and%22%2C%22content" +
            "%22%3A%5B%7B%22op%22%3A%22in%22%2C%22content%22%3A%7B%22field%22%3A%22cases.case_id" +
            "%22%2C%22value%22%3A%5B%22" +
            case_uuid + 
            "%22%5D%7D%7D%2C%7B%22op%22%3A%22in%22%2C%22content%22%3A%7B%22field%22%3A%22" +
            "files.experimental_strategy%22%2C%22value%22%3A%5B%22RNA-Seq" + 
            "%22%5D%7D%7D%5D%7D&searchTableTab=files")
    driver.get(url)
    #wait for page to load
    driver.implicitly_wait(3)
    driver.switch_to_active_element().find_element_by_css_selector(".undefined.button.css-oe4so").click()
     
    #wait for page to load
    driver.implicitly_wait(3)
    file_name = (driver.find_elements_by_class_name("css-3a0tuc")[0].
                 find_elements_by_tag_name("td")[2].text)
    return file_name

def make_case_plus_url_table(size = 100):
    """
    Make table with 3 columns: Project, Case-UUID, RNA-Seq UUID
    Include all projects with number of casese >= size
    """
    projects = get_project_ids()
    cases_per_project = get_case_count_per_project(projects)
    all_cases_dic = {}
    
    for project in cases_per_project:
        if cases_per_project[project] >= size:
            all_cases_dic[project] = get_all_cases_from_project(project)
        
    res = [["Project", "Case-UUID", "RNA-Seq Url"]]    
    
    for project in all_cases_dic:
        for case in all_cases_dic[project]:
            uuid = all_cases_dic[project][case]
            temp = [project, uuid , get_rna_seq_file_url(uuid)]
            res.append(temp)

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
 







