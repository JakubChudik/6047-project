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
from sklearn.linear_model import LinearRegression
from sklearn.model_selection import train_test_split

def data_preprocessing(filename):
    '''
    loads json file containing rna expression data and age of
    diagnoses and converts this to a pandas DataFrame
    '''
    with open(filename, 'r') as f:
        data = json.load(f)
    print(len(data['case_uuid']))
    for key in data:
        print(key,len(data[key]))
    cases = pd.DataFrame(data)
    cases = cases.fillna(0)
    print('data preprocessing complete')
    return cases

def supervised_learning(data):
    """
    breaks our data into training and test, and uses the
    diagnoses age as y value. then create a linear regression
    model and test it against the test data
    """
    X = data.drop(['case_uuid','diagnoses_age','tumor_stage'],axis= 1)
    X_train, X_test, y_train, y_test = train_test_split(X, data.tumor_stage, test_size=0.25)
    model = LinearRegression()
    model.fit(X_train, y_train)
    pred_train = model.predict(X_train)
    print(sqrt(sklearn.metrics.mean_squared_error(y_train,pred_train)))
    pred_test = model.predict(X_test)
    print('pred',list(pred_test))
    print('actual',list(y_test))
    print(sqrt(sklearn.metrics.mean_squared_error(y_test,pred_test)))

def unsupervised_learning(data):
    pass

def main():
    data = data_preprocessing('cleanDataBreast.json')
    supervised_learning(data)

main()
