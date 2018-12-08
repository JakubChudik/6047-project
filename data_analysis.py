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
    X = data.drop(['case_uuid','tumor_stage'],axis= 1)
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
        print(result)
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



def unsupervised_learning(data, feature):
    """
    performs PCA on data and then clusters them
    """
    df = data.drop(['case_uuid', feature],axis= 1)
    n_components = 2


    pca = PCA(n_components)
    principal_components = pca.fit_transform(df)
    principal_df = pd.DataFrame(data = principal_components
                 , columns = ['principal component 1', 'principal component 2'])

    #cluster and joint PCA with labels
    clusters = KMeans(n_clusters=2).fit(principal_df)
    labels = pd.DataFrame({'target':clusters.labels_})
    finalDf = pd.concat([principal_df, labels[['target']]], axis = 1)

    #plot
    fig = plt.figure(figsize = (8,8))
    ax = fig.add_subplot(1,1,1)
    ax.set_xlabel('Principal Component 1', fontsize = 40)
    ax.set_ylabel('Principal Component 2', fontsize = 40)
    ax.set_title('2 component PCA', fontsize = 40)

    targets = [0, 1]
    colors = ['r', 'g']

    for target, color in zip(targets,colors):
        indicesToKeep = finalDf['target'] == target
        ax.scatter(finalDf.loc[indicesToKeep, 'principal component 1']
                   , finalDf.loc[indicesToKeep, 'principal component 2']
                   , c = color
                   , s = 50)
    ax.legend(targets)
    ax.grid()

def main():
    data = data_preprocessing('cleanDataStage.csv')
    supervised_learning_individual_feature(data)

main()
