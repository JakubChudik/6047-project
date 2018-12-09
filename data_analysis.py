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
from sklearn.linear_model import LinearRegression
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

def supervised_learning(data):
    """
    breaks our data into training and test, and uses the
    diagnoses age as y value. then create a linear regression
    model and test it against the test data
    """
    X = data.drop(['case_uuid','tumor_stage'],axis= 1)
    X_train, X_test, y_train, y_test = train_test_split(X, data.tumor_stage, test_size=0.25)
    model = LinearRegression()
    model.fit(X_train, y_train)
    pred_train = model.predict(X_train)
    print(sqrt(sklearn.metrics.mean_squared_error(y_train,pred_train)))
    pred_test = model.predict(X_test)
    pred_test = np.rint(pred_test)
    print('pred',list(pred_test))
    print('actual',list(y_test))
    print(sqrt(sklearn.metrics.mean_squared_error(y_test,pred_test)))

def supervised_learning_individual_feature(data):
    """
    breaks our data into training and test, and uses the
    diagnoses age as y value. then create a linear regression
    model and test it against the test data
    """
    data = data.drop(data[data["tumor_stage"] == 0].index)
    data = data[pd.notnull(data['tumor_stage'])]
    data.fillna(data.mean(), inplace=True)

    X = data.drop(['case_uuid','tumor_stage'],axis= 1)
    # X = data.drop(['case_uuid','tumor_stage','days_to_death'],axis= 1)
    cols = len(X.columns)
    print(cols)
    mins = []
    indeces = []
    for i in range(1,cols):
        column = i
        X_single = X.iloc[:,column].values.reshape(-1,1)
        # print(X_single.head())
        X_train, X_test, y_train, y_test = train_test_split(X_single, data.tumor_stage, test_size=0.25)
        model = LinearRegression()
        model.fit(X_train, y_train)
        pred_train = model.predict(X_train)
        # print(sqrt(sklearn.metrics.mean_squared_error(y_train,pred_train)))
        pred_test = model.predict(X_test)
        # pred_test = np.rint(pred_test)
        # print('pred',list(pred_test))
        # print('actual',list(y_test))
        result = sqrt(sklearn.metrics.mean_squared_error(y_test,pred_test))
        if i % 1000 == 0:
            print("Currently on gene: " + str(i))
        if len(mins) >= 5:
            if result < max(mins):
                index = mins.index(max(mins))
                del mins[index]
                del indeces[index]
                mins.append(result)
                indeces.append(column)
        else:
            mins.append(result)
            indeces.append(column)
    print (mins,indeces)
    return (mins,indeces)

def main():
    data = data_preprocessing('Breast_test_data.csv')
    supervised_learning_individual_feature(data)

main()
