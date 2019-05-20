import csv
import os
import subprocess
import sys
import pathlib
import re
import json

from consolidate import consolidate
from extract_metadata import extract_metadata

from slugify import slugify
from utilities import get_next_filename, parse_config_arguments

def take_inventory(config, results_folder):
    # Compile search terms
    terms = {}
    for search in config["inventory"]:
        terms[search["name"].lower()] = [re.compile(term, re.IGNORECASE | re.MULTILINE) for term in search["terms"]]

    results = {}

    for content_set in config["content"]:
        docset = content_set.get("repo")
        folder = content_set.get("path")
        base_url = content_set.get("url")
        exclude_folders = content_set.get("exclude_folders")

        if folder is None:
            print("take-inventory: No path for docset {} - skipping".format(docset))
            continue

        if docset is None or base_url is None:
            print("take-inventory: Malformed config entry for docset {}; check your config file".format(docset))
            continue

        print('take-inventory: Processing ' + docset + ' at ' + folder)

        for root, dirs, files in os.walk(folder):
            for exclusion in exclude_folders:
                if exclusion in dirs:
                    dirs.remove(exclusion)

            for file in files:
                if pathlib.Path(file).suffix != '.md':
                    continue

                full_path = os.path.join(root, file)

                try:
                    content = pathlib.Path(full_path).read_text(errors="ignore")
                except UnicodeDecodeError:
                    print("take-inventory: WARNING: File {} contains non-UTF-8 characters: Must be converted. Skipping.".format(full_path))
                    continue

                for search in config["inventory"]:
                    name = search["name"].lower()

                    if name not in results:
                        results[name] = []

                    for term in terms[name]:
                        for match in term.finditer(content):
                            line_start = content.rfind("\n", 0, match.span()[0])
                            line_end = content.find("\n", match.span()[1])
                            line = content[0:match.span()[0]].count("\n") + 1
                            url = base_url + full_path[full_path.find('\\', len(folder) + 1) : -3].replace('\\','/')
                            results[name].append([docset, full_path, url, term.pattern, line, content[line_start:line_end].strip()])

    # Sort the results (by filename, then line number), and save to a .csv file.
    # A sorted list is needed for consolidate.py and removes the need to open
    # the .csv file in Excel for a manual sort.
    print("take-inventory: Sorting results by filename")
    
    for inventory, rows in results.items():
        rows.sort(key=lambda row: (row[1], int(row[4])))  # Use int on [4] to sort the line numbers numerically

        # Open CSV output file, which we do before running the searches because
        # we consolidate everything into a single file

        result_filename = get_next_filename(inventory)
        print('take-inventory: Writing CSV results file %s.csv' % (result_filename))

        with open(result_filename + '.csv', 'w', newline='', encoding='utf-8') as csv_file:    
            writer = csv.writer(csv_file)
            writer.writerow(['Docset', 'File', 'URL', 'Term', 'Line', 'Extract'])
            writer.writerows(rows)

        print("take-inventory: Completed first CSV results file")
        print("take-inventory: Invoking secondary processing to extract metadata")

        meta_output = "{}-metadata.csv".format(result_filename)
        consolidate_output = "{}-consolidated.csv".format(result_filename)

        extract_metadata(result_filename+".csv", meta_output)
        consolidate(config, meta_output, consolidate_output)

if __name__ == "__main__":
    # Get input file arguments, defaulting to folders.txt and terms.txt
    config_file, _ = parse_config_arguments(sys.argv[1:])

    if config_file is None:
        print("Usage: python take-inventory.py --config <config_file>")
        sys.exit(2)

    config = None
    with open(config_file, 'r') as config_load:
        config = json.load(config_load)

    if config is None:
        print("Could not deserialize config file")
        sys.exit(1)

    # Run the script in the 'InventoryData' folder (using the environment variable if it exists)
    results_folder = os.getenv("INVENTORY_RESULTS_FOLDER", "InventoryData")
    os.chdir(results_folder)

    take_inventory(config, results_folder)
