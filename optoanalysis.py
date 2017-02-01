# -*- coding: utf-8 -*-
"""
Created on Tue Sep 27 10:25:21 2016

@author: lina
"""
import numpy as np
import os
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

def read_times_txt(txt):
    '''
    Input: a animal_name.txt file named for each animal, each row consists of
    a duration of freezing
    Output: numpy array of arrays containing the time intervals of freezing
    '''
    times = np.loadtxt(txt, delimiter='-')
    return times

def folder_times(directory):
    '''
    Input: Directory containing all the .txt files of freezing times for each
    animal
    Output:
    1. animals: list of the animal names from the .txt filenames
    2. tables: a list of all the numpy array of arrays containing the time
    intervals of freezing corresponding to the animals
    '''
    animals = []
    tables = []
    groupings = []
    for root, _, fn in os.walk(directory):
        for f in fn:
            fullpath = os.path.join(root, f)
            if f.strip('.txt').lower() == 'groups':
                with open(fullpath) as x:
                    firstline = x.readline()
                    group_names = firstline.strip().split(',')
                    group_names = [i.strip().lower() for i in group_names]
                    groupings.append(group_names)
                    secondline = x.readline()
                    groupings.append(secondline.strip())
            else:
                animals.append(f.strip('.txt').lower())
                times_all = read_times_txt(fullpath)
                tables.append(times_all)
    return animals, tables, groupings


def bin_freezing(tables, bin_size, total):
    '''
    input: tables output from folder_times(), size of bin in seconds, and the
    total length of time of the session in seconds
    Output:
    1. freezing_bins: the bins which the total time is split into
    2. the percent freezing occurring during the corresponding freezing_bins
    The function works by looking at every freezing episode and looping over all
    possible bins until it finds it's match. If bins fit into more than bin,
    the bin is split such that the earlier bin is binned first, and the later
    bin is appended to the end of the list to be binned once it comes up again.
    '''
    epochs = float(total)/bin_size
    idx = np.arange(1, epochs+1)*bin_size
    freezing_bins = []
    for i in idx:
        freezing_bins.append([])
    tables = list(tables)

    #time[0] is the start of freezing, time[1] is the end of freezing
    for time in tables:
        #where bn is the top end of the bin
        #splits the freezing events into bins
        for ix, bn in enumerate(idx):
            #for the case where an event spans more than two bins
            if (time[1] > bn) & (time[0] < (bn-bin_size)):
                freezing_bins[ix].append(bn - time[0])
                #send the later portion to be binned again
                tables.append(np.array([bn, time[1]]))
                #break to stop looping over all other bins once we've found the
                #correct bin(s)
                break
            #for the case where an event spans two bins
            elif (time[1] > bn) & ((bn-bin_size) <= time[0] < bn):
                freezing_bins[ix].append(bn - time[0])
                tables.append(np.array([bn, time[1]]))
                break
            #where an events spans only one bin
            elif (time[1] <= bn) & (time[0] >= (bn-bin_size)):
                freezing_bins[ix].append(time[1] - time[0])
                break
    sums = []
    for ix,i in enumerate(freezing_bins):
        if i == []:
            i.append(0)
        bin_sum = sum(i)
        sums.append(bin_sum)
    sums = np.array(sums)

    return freezing_bins, sums/float(bin_size)

def folder_freezing(directory, bin_size, total):
    '''
    Input: directory, size of bin in seconds, total length of recording session,
    and groupings as a list of groups based on your animal naming convention.
    - The first group will be labeled as 0, the second as 1 and so forth.
    Output: numpy array of binned freezing percentages, each line is one animal
    - grouping indicated in the first column determined by groupings parameter
    - numbered coding used only because we are using numpy arrays
    '''
    animals, tables, groupings = folder_times(directory)
    groups = np.zeros([len(tables),(total//bin_size + 1)])
    for idx, animal in enumerate(tables):
        for code, group in enumerate(groupings[0]):
            if group in animals[idx]:
                freezing = bin_freezing(tables[idx], bin_size, total)
                groups[idx][1:] = freezing[1]
                groups[idx][0] = code
    return groups, groupings[1]

def groups_to_df(groups, bin_size, total, key):
    '''
    Input: groups from folder_freezing(), bin_size in seconds, and total length
    of session, and dictionary containing groups corresponding to the
    coded group values
    Output: A Pandas DataFrame with records of each animal's freezing per bin
    '''
    groups = pd.DataFrame(groups,
        columns=['Group']+list(np.arange(bin_size,total+bin_size,bin_size)))
    #an ID must be made to associate a time point to an animal
    groups['ID'] = [i for i in groups.index]
    groups['Group'] = groups['Group'].map(key)
    groups_melt = pd.melt(groups, id_vars=['Group', 'ID'],
        var_name='Timepoints', value_name='Freezing')
    return groups, groups_melt

def plot_freezing(df, bin_size, total, style='ts'):
    '''
    Input: A Pandas Dataframe from groups_to_df(), bin_size and total time
    for x-axis generation, and style either 'ts' for time series, or 'bar' for
    bar plot.
    '''
    sns.set_style('ticks')
    assert style.lower() in ['ts', 'bar'], \
        "Please enter a style from 'ts' for time series, or 'bar' for bar plot"

    plt.figure(figsize=(15,10))
    plt.xlabel('Timepoints', fontsize=20)
    plt.ylabel('Freezing', fontsize=20)

    if style == 'ts':
        g = sns.tsplot(data=df, unit='ID', time='Timepoints', condition='Group', value='Freezing')
        plt.legend(prop={'size':20})
        sns.despine()
        g.set_xticks(range(0,total+60,60))
    elif style == 'bar':
        g = sns.barplot(x='Timepoints', y='Freezing', hue='Group', data=df, ci=68, capsize=0.05)
        sns.despine()
        g.set_ylabel('Freezing (%)', fontsize=20)
        g.set_xlabel('Timepoints', fontsize=20)
