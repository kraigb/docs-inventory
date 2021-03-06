import csv
import os
import subprocess
import sys
import pathlib
import re
import json

from consolidate import consolidate
from extract_metadata import extract_metadata
from score import score

from slugify import slugify
from utilities import get_next_filename, parse_config_arguments, classify_occurrence, delineate_segments, COLUMNS

def take_inventory(config, results_folder):
    print("Script,Type,Message,Detail,Item")
    # Compile search terms
    terms = {}
    for search in config["inventory"]:
        terms[search["name"].lower()] = [re.compile(term, re.IGNORECASE | re.MULTILINE) for term in search["terms"]]

    results = {}

    for content_set in config["content"]:
        docset = content_set.get("repo")
        folder = os.path.expandvars(content_set.get("path"))  # Expands ${INVENTORY_REPO_ROOT}
        base_url = content_set.get("url")
        exclude_folders = content_set.get("exclude_folders")

        if folder is None:
            print("take_inventory, WARNING, No path for docset, Skipping, {}".format(docset))
            continue

        if docset is None or base_url is None:
            print("take_inventory, ERROR, Malformed config entry for docset, Check your config file, {}".format(docset))
            continue

        print('take_inventory, INFO, Processing docset, {}, {}'.format(docset, folder))

        for root, dirs, files in os.walk(folder):
            for exclusion in exclude_folders:
                if exclusion in dirs:
                    dirs.remove(exclusion)

            for file in files:
                if pathlib.Path(file).suffix != '.md':
                    continue

                full_path = os.path.join(root, file)

                try:
                    content = pathlib.Path(full_path).read_text(errors="replace")
                except UnicodeDecodeError:
                    print("take_inventory, WARNING, Skipping file that contains non-UTF-8 characters and should be converted, , {}".format(full_path))
                    continue

                code_lines, intro_lines, metadata_lines = delineate_segments(content, full_path)

                # Content check: if metadata_text is empty, then the article lacks metadata
                if len(metadata_lines) == 0:
                    print("take_inventory, WARNING, File contains no metadata, , {}".format(full_path))

                for search in config["inventory"]:
                    name = search["name"].lower()

                    if name not in results:
                        results[name] = []

                    for term in terms[name]:                        
                        for match in term.finditer(content):
                            line_start = content.rfind("\n", 0, match.span()[0])
                            line_start = 0 if line_start == -1 else line_start  # Handle BOF case

                            line_end = content.find("\n", match.span()[1])
                            line_end = len(content) if line_end == -1 else line_end # Handle EOF case

                            line_num = content[0:match.span()[0]].count("\n") + 1
                            line = content[line_start:line_end + 1]
                            line_content = line.lstrip() # Keep the trailing \n in this variant

                            # Determine the position in line_content of the term ending
                            chars_removed = len(line) - len(line_content)
                            term_end = match.span()[1] - line_start - chars_removed

                            # Second argument is the end of the term's occurrence, because we need to look at 
                            # that subset of text in some classifications.
                            tag = classify_occurrence(line_content, term_end, term.pattern, line_num, file,
                                code_lines, intro_lines, metadata_lines)

                            url = base_url + full_path[full_path.find('\\', len(folder) + 1) : -3].replace('\\','/')
                            results[name].append([docset, full_path, url, term.pattern, tag, line_num, line_content.strip()])

    # Sort the results (by filename, then line number), and save to a .csv file.
    # A sorted list is needed for consolidate.py and removes the need to open
    # the .csv file in Excel for a manual sort.
    print("take_inventory, INFO, Sorting results by filename, , ")
    
    for inventory, rows in results.items():
        rows.sort(key=lambda row: (row[1], int(row[5])))  # Use int on [4] to sort the line numbers numerically

        # Open CSV output file, which we do before running the searches because
        # we consolidate everything into a single file

        result_filename = get_next_filename(inventory)
        print('take_inventory, INFO, Writing CSV results file, , {}.csv'.format(result_filename))

        with open(result_filename + '.csv', 'w', newline='', encoding='utf-8') as csv_file:    
            writer = csv.writer(csv_file)
            writer.writerow([ COLUMNS["docset"], COLUMNS["file"], COLUMNS["url"], COLUMNS["term"],
                COLUMNS["tag"], COLUMNS["line"], COLUMNS["extract"] ])
            writer.writerows(rows)

        print("take_inventory, INFO, Completed first CSV results file, , {}.csv".format(result_filename))

        print("take_inventory, INFO, Invoking secondary processing to extract metadata, , ")
        meta_output = "{}-metadata.csv".format(result_filename)
        extract_metadata(result_filename+".csv", meta_output)

        print("take_inventory, INFO, Invoking secondary processing to consolidate output, , ")
        consolidate_output = "{}-consolidated.csv".format(result_filename)
        consolidate(config, meta_output, consolidate_output)

        print("take_inventory, INFO, Invoking secondary processing to apply scoring, , ")        
        score_output = "{}-scored.csv".format(result_filename)
        score(consolidate_output, score_output)

if __name__ == "__main__":
    # Get input file arguments, defaulting to folders.txt and terms.txt
    config_file, _ = parse_config_arguments(sys.argv[1:])

    if config_file is None:
        print("Usage: python take_inventory.py --config <config_file>")
        sys.exit(2)

    config = None
    with open(config_file, 'r') as config_load:
        config = json.load(config_load)

    if config is None:
        print("take_inventory: Could not deserialize config file")
        sys.exit(1)

    repo_folder = os.getenv("INVENTORY_REPO_ROOT")
    
    if repo_folder is None:
        print("take_inventory: Set environment variable INVENTORY_REPO_ROOT to your repo root before running the script.")
        sys.exit(1)

    # Run the script in the 'InventoryData' folder (using the environment variable if it exists)
    results_folder = os.getenv("INVENTORY_RESULTS_FOLDER", "InventoryData")
    os.chdir(results_folder)

    take_inventory(config, results_folder)
