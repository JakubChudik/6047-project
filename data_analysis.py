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
    cases = pd.DataFrame(data)
    return cases

def linear_regression(data):
    X = data.drop(['case_uuid','diagnoses_age'],axis= 1)
    X_train, X_test, y_train, y_test = train_test_split(X, data.diagnoses_age, test_size=0.25)
    model = LinearRegression()
    model.fit(X_train, y_train)
    pred_train = model.predict(X_train)
    print(sqrt(sklearn.metrics.mean_squared_error(y_train,pred_train)))
    pred_test = model.predict(X_test)
    print(sqrt(sklearn.metrics.mean_squared_error(y_test,pred_test)))

def main():
    data = data_preprocessing('cleanData.json')
    linear_regression(data)

main()
