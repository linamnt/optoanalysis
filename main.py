"""
Script to run optoanalysis through shell.

Usage:
python main.py /directory/of/files/ bin_size total_time output --style
@author: lina
"""
from optoanalysis import *
import sys
import ast

def main():
    directory = sys.argv[1]
    bin_size = int(sys.argv[2])
    total = int(sys.argv[3])
    output_fn = sys.argv[4]
    if len(sys.argv) > 5:
        style = sys.argv[5].strip('--')
    else:
        style = 'ts'

    groups, key = folder_freezing(directory, bin_size, total)
    key = ast.literal_eval(key)
    groups, groups_melt = groups_to_df(groups, bin_size, total, key)
    groups.to_csv(output_fn)
    plot_freezing(groups_melt, bin_size, total, style)
    plt.show()

if __name__ == '__main__':
    main()
