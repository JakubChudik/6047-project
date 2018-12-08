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
from sklearn.cluster import KMeans
from sklearn.decomposition import PCA

def data_preprocessing(filename):
    '''
    loads json file containing rna expression data and age of
    diagnoses and converts this to a pandas DataFrame
    '''
    with open(filename, 'r') as f:
        data = json.load(f)
    cases = pd.DataFrame(data)
    cases = cases.fillna(0)
    return cases

def supervised_learning(data):
    """
    breaks our data into training and test, and uses the
    diagnoses age as y value. then create a linear regression
    model and test it against the test data
    """
    X = data.drop(['case_uuid','diagnoses_age'],axis= 1)
    X_train, X_test, y_train, y_test = train_test_split(X, data.diagnoses_age, test_size=0.25)
    model = LinearRegression()
    model.fit(X_train, y_train)
    pred_train = model.predict(X_train)
    print(sqrt(sklearn.metrics.mean_squared_error(y_train,pred_train)))
    pred_test = model.predict(X_test)
    print('pred',list(pred_test))
    print('actual',list(y_test))
    print(sqrt(sklearn.metrics.mean_squared_error(y_test,pred_test)))

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
    data = data_preprocessing('cleanDataBreast.json')
    supervised_learning(data)

main()
