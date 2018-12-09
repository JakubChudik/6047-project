# -*- coding: utf-8 -*-
"""
Created on Fri Nov 23 14:10:31 2018

@author: jakub
"""
import json
import numpy as np
import os
import pandas as pd
import sklearn
from math import sqrt
import random
from sklearn.linear_model import LinearRegression, LogisticRegression
from sklearn.model_selection import train_test_split
from sklearn.cluster import KMeans
from sklearn.decomposition import PCA

def data_preprocessing(filename):
    '''
    loads json file containing rna expression data and age of
    diagnoses and converts this to a pandas DataFrame
    '''
    data = pd.DataFrame.from_csv(filename)
    print('data preprocessing complete')
    print(data.head())
    return data

#def supervised_learning(data):
#    """
#    breaks our data into training and test, and uses the
#    diagnoses age as y value. then create a linear regression
#    model and test it against the test data
#    """
#    X = data.drop(['case_uuid','tumor_stage'],axis= 1)
#    X_train, X_test, y_train, y_test = train_test_split(X, data.tumor_stage, test_size=0.25)
#    model = LinearRegression()
#    model.fit(X_train, y_train)
#    pred_train = model.predict(X_train)
#    print(sqrt(sklearn.metrics.mean_squared_error(y_train,pred_train)))
#    pred_test = model.predict(X_test)
#    pred_test = np.rint(pred_test)
#    print('pred',list(pred_test))
#    print('actual',list(y_test))
#    print(sqrt(sklearn.metrics.mean_squared_error(y_test,pred_test)))

def supervised_learning_individual_feature(data, features, split, linear = True):
    """
    breaks our data into training and test, and uses the
    diagnoses age as y value. then create a linear regression
    model and test it against the test data
    """
    features += ['case_uuid']
    X = data.drop(features, axis= 1)
    mins = []
    for i in range(len(X.columns)):
        X_single = X.iloc[:,i].values.reshape(-1,1)
        X_train, X_test, y_train, y_test = 0,0,0,0
        if split == "tumor_stage":
            X_train, X_test, y_train, y_test = train_test_split(X_single, data.tumor_stage, test_size=0.25)
        else:
            X_train, X_test, y_train, y_test = train_test_split(X_single, data.days_to_death, test_size=0.25)
       
        model = LinearRegression()
        if not linear:
            model = LogisticRegression()
        
        model.fit(X_train, y_train)
        pred_test = model.predict(X_test)
        result = sqrt(sklearn.metrics.mean_squared_error(y_test,pred_test))
        
        if i % 1000 == 0:
            print("Currently on gene: " + str(i))
        mins.append((result, X.columns[i]))
    
    mins.sort(key = lambda x: x[0])
    print(mins[0:5])
    return mins

def get_top_10_stage_for_all():
    res =  dict()
    log = dict()
    features = ["tumor_stage"]
    split = "tumor_stage"
    for file in os.listdir("rna_data"):
        site = file.split("_")[0]
        f = 'rna_data/' + file
        data = data_preprocessing(f)
        mins = []
        try:
            mins = supervised_learning_individual_feature(data, features, split, linear = False)
            res[site] = mins[0:10]
            log[site] = "success"
        except:
            log[site] = "fail"
            continue
        print(site + " done")
    temp = pd.DataFrame(res)
    temp.to_csv("top_10_log_reg_stage.csv")
    return res, log

def get_top_10_death_for_all():
    res =  dict()
    log = dict()
    features = ["tumor_stage", "days_to_death"]
    split = "days_to_death"
    for file in os.listdir("data_death"):
        site = file.split("_")[0]
        f = 'data_death/' + file
        data = data_preprocessing(f)
        mins = []
        try:
            mins = supervised_learning_individual_feature(data, features, split)
            res[site] = mins[0:10]
            log[site] = "success"
        except:
            log[site] = "fail"
            continue
        print(site + " done")
    temp = pd.DataFrame(res)
    temp.to_csv("top_10_logreg_death.csv")
    return res, log

#def main():

#main()
