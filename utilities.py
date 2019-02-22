import datetime
import getopt
import os
import re
import sys


def get_next_filename():    
    """ Determine the next filename by incrementing 1 above the largest existing file number in the current folder for today's date."""

    today = datetime.date.today()

    date_pattern = 'results_' + str(today)
    files = [f for f in os.listdir('.') if re.match(date_pattern + '-[0-9]+.csv', f)]

    if (len(files) == 0):
        next_num = 1
    else:
        file_nums = [item[19:23] for item in files ]
        next_num = max(int(n) for n in file_nums) + 1

    return "%s-%04d" % (date_pattern, next_num)


def parse_folders_terms_arguments(argv):
    """ Parses an arguments list for take-inventory.py, returning folders and terms filenames (tuple), defaulting to folders.txt and terms.txt. Any additional arguments after the options are included in the tuple."""
    folders_file = 'folders.txt'
    terms_file = 'terms.txt'

    try:
        opts, args = getopt.getopt(argv, 'hH?', ["folders=", "terms="])
    except getopt.GetoptError:
        return (None, None, None)

    for opt, arg in opts:
        if opt in ('-h', '-H', '-?'):
            return (None, None, None)

        if opt in ('--folders'):
            folders_file = arg

        if opt in ('--terms'):
            terms_file = arg
    
    return (folders_file, terms_file, args)
