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


def parse_endpoint_key_arguments(argv):
    """ Parses an arguments list for extract-key-phrases.py, returning an endpoint and API key (tuple), with no defaults. Any additional arguments after the options are included in the tuple."""

    endpoint = None
    key = None

    try:
        opts, args = getopt.getopt(argv, 'e:k:hH?', ["endpoint=", "key="])
    except getopt.GetoptError:
        return (None, None, None)

    for opt, arg in opts:
        if opt in ('-h', '-H', '-?'):
            return (None, None, None)

        if opt in ('--endpoint', '-e'):
            endpoint = arg

        if opt in ('--key', '-k'):
            key = arg
    
    return (endpoint, key, args)

def parse_filters_arguments(argv):
    """ Parses an arguments list for apply-filters.py, returning a filters file and additional args in a tuple."""
    filters_file = 'filters.txt'    

    try:
        opts, args = getopt.getopt(argv, 'fhH?', ["filters="])
    except getopt.GetoptError:
        return (None, None, None)

    for opt, arg in opts:
        if opt in ('-h', '-H', '-?'):
            return (None, None, None)

        if opt in ('--filters', '-f'):
            filters_file = arg
    
    return (filters_file, args)


def make_identifier(name):
    """Converts the given name to a valid Python identifier by replacing spaces with an underscore and removing any other characters that aren't letters, numbers, or underscores. Identifiers also cannot begin with a number."""
    
    # Replace spaces with underscores.
    name = name.replace(' ', '_')

    # Remove any other invalid characters
    name = re.sub('[^0-9a-zA-Z_]', '', name)

    # Remove leading characters until we find a letter or underscore
    name = re.sub('^[^a-zA-Z_]+', '', name)

    return name
