import os
import sys
import pathlib
import re
import json
import datetime
import re
import statistics

from consolidate import consolidate
from extract_metadata import extract_metadata
from score import score

from slugify import slugify
from utilities import get_next_filename, parse_config_arguments, classify_occurrence, delineate_segments, COLUMNS

def file_age(file, today, age_list):
    if pathlib.Path(file).suffix != '.md':
        return

    try:
        content = pathlib.Path(file).read_text(errors="replace")
    except UnicodeDecodeError:
        print("tally_age, WARNING, Skipping file that contains non-UTF-8 characters and should be converted, , {}".format(file))
        return

    # Find ms.date line in the content. Regex accomodates odd variations found in repos, such
    # as excess whitespace, quotes around dates.
    msdate = re.findall("ms.date:\s*\"?(\d{1,2}\/\d{1,2}\/\d{2,4})\"?", content)

    # Content check: if metadata_text is empty, then the article lacks metadata
    if len(msdate) == 0:
        print("tally_age, File contains no metadata--skipping, , {}".format(file))
        return

    try:
        article_date = datetime.datetime.strptime(msdate[0], "%m/%d/%Y")
        age = (today.date() - article_date.date()).days
        age_list.append(age)
    except ValueError:
        print(f"Skipping: malformed date in {file}")

def collect_stats(dict, data):
    dict["values"] = data

    if len(data) > 0:
        dict["mean"] = statistics.mean(data)
    else:
        dict["mean"] = 0

    if len(data) > 1:
        dict["stddev"] = statistics.stdev(data)
    else:
        dict["stddev"] = 0

def tally_age(root_path, save_file):
    results = {}
    today = datetime.datetime.now()
    exclude_folders = ["media", "breadcrumb", ]

    # For output, we want a dictionary with top-level folder names and an array 
    # of days-old values for all articles contained in that folder and any child
    # folders. So each dictionary entry is itself a dictionary: "folder": { "mean": xxx, "stddev": yyy, "values"" array"}

    results = {}        
    root_ages = []

    # Iterate the top-level folders
    for item in os.listdir(root_path):        
        full_path = os.path.join(root_path, item)

        if not os.path.isdir(full_path):
            # Process a file at the root
            file_age(full_path, today, root_ages)
        else:
            # Process a folder
            if item in exclude_folders:
                continue

            folder_result = {}
            ages = []

            # Iterate the entire subfolder, adding all article
            # ages to the ages list.
            for root, dirs, files in os.walk(full_path):
                for exclusion in exclude_folders:
                    if exclusion in dirs:
                        dirs.remove(exclusion)

                for file in files:
                    file_age(os.path.join(root, file), today, ages)

            collect_stats(folder_result, ages)
            results[item] = folder_result
    
    collect_stats(results, root_ages)

    with open(save_file, 'w') as fp:        
        json.dump(results, fp)

if __name__ == "__main__":
    root_path = sys.argv[1]
    json_path = sys.argv[2]

    if root_path is None or json_path is None:
        print("Usage: python tally_age.py <root-path> <json-file-path>")
        sys.exit(2)

    tally_age(root_path, json_path)
