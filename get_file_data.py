import csv
import os
import subprocess
import sys
import pathlib
import re
import json

from consolidate import consolidate
from extract_metadata import extract_metadata
from extract_scrapings import extract_scrapings

from slugify import slugify
from utilities import get_next_filename, parse_config_arguments, classify_occurrence, delineate_segments, COLUMNS

def get_file_data(config, results_folder):
    print("Script,Type,Message,Item")

    results = {}

    for content_set in config["content"]:
        docset = content_set.get("repo")
        folder = os.path.expandvars(content_set.get("path"))  # Expands ${INVENTORY_REPO_ROOT}
        base_url = content_set.get("url")
        exclude_folders = content_set.get("exclude_folders")

        if folder is None:
            print("get-file-data, WARNING, No path for docset - skipping, {}".format(docset))
            continue

        if docset is None or base_url is None:
            print("get-file-data: Malformed config entry for docset {}; check your config file".format(docset))
            continue

        print('get-file-data, INFO, Processing docset {}, {}'.format(docset, folder))

        for root, dirs, files in os.walk(folder):
            for exclusion in exclude_folders:
                if exclusion in dirs:
                    dirs.remove(exclusion)

            for file in files:
                if pathlib.Path(file).suffix != '.md':
                    continue

                full_path = os.path.join(root, file)

                """
                try:
                    content = pathlib.Path(full_path).read_text(errors="ignore")
                except UnicodeDecodeError:
                    print("get-file-data, WARNING, Skipping file that contains non-UTF-8 characters and should be converted, {}".format(full_path))
                    continue

                code_lines, intro_lines, metadata_lines = delineate_segments(content, full_path)

                # Content check: if metadata_text is empty, then the article lacks metadata
                if len(metadata_lines) == 0:
                    print("get-file-data, WARNING, File contains no metadata, {}".format(full_path))
                """

                for search in config["inventory"]:
                    name = search["name"].lower()

                    if name not in results:
                        results[name] = []

                    url = base_url + full_path[full_path.find('\\', len(folder) + 1) : -3].replace('\\','/')
                    results[name].append([docset, full_path, url, "", "", "", "" ])                    

    # Sort the results (by filename, then line number), and save to a .csv file.
    # A sorted list is needed for consolidate.py and removes the need to open
    # the .csv file in Excel for a manual sort.
    print("get-file-data, INFO, Sorting results by filename,")
    
    for inventory, rows in results.items():
        rows.sort(key=lambda row: (row[1]))

        # Open CSV output file, which we do before running the searches because
        # we consolidate everything into a single file

        result_filename = get_next_filename(inventory)
        print('get-file-data, INFO, Writing CSV results file, {}.csv'.format(result_filename))

        with open(result_filename + '.csv', 'w', newline='', encoding='utf-8') as csv_file:    
            writer = csv.writer(csv_file)
            writer.writerow([ COLUMNS["docset"], COLUMNS["file"], COLUMNS["url"], COLUMNS["term"],
                COLUMNS["tag"], COLUMNS["line"], COLUMNS["extract"] ])
            writer.writerows(rows)

        print("get-file-data, INFO, Completed first CSV results file, ")
        print("get-file-data, INFO, Invoking secondary processing to extract metadata, ")

        meta_output = "{}-metadata.csv".format(result_filename)        
        extract_metadata(result_filename+".csv", meta_output)

        scrapings_output = "{}-scrapings.csv".format(result_filename)
        extract_scrapings(meta_output, scrapings_output)

if __name__ == "__main__":
    # Get input file arguments, defaulting to folders.txt and terms.txt
    config_file, _ = parse_config_arguments(sys.argv[1:])

    if config_file is None:
        print("Usage: python get_file_data.py --config <config_file>")
        sys.exit(2)

    config = None
    with open(config_file, 'r') as config_load:
        config = json.load(config_load)

    if config is None:
        print("get_file_data: Could not deserialize config file")
        sys.exit(1)

    repo_folder = os.getenv("INVENTORY_REPO_FOLDER")
    
    if repo_folder is None:
        print("get_file_data: Set environment variable INVENTORY_REPO_FOLDER to your repo root before running the script.")
        sys.exit(1)

    # Run the script in the 'InventoryData' folder (using the environment variable if it exists)
    results_folder = os.getenv("INVENTORY_ISSUES_FOLDER", "IssueData")
    os.chdir(results_folder)

    get_file_data(config, results_folder)
