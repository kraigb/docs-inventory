# For each path in folders.txt, run regex terms defined in terms.txt

import csv
import os
import subprocess
import sys
import pathlib
import re

from slugify import slugify
from utilities import get_next_filename, parse_folders_terms_arguments

# Get input file arguments, defaulting to folders.txt and terms.txt
folders_file, terms_file, _ = parse_folders_terms_arguments(sys.argv[1:])

if folders_file == None:
    print("Usage: python take-inventory.py --folders <folders_file> --terms <terms_file>")
    sys.exit(2)

# Load the folders and terms from the files
folders = [line.rstrip('\n') for line in open(folders_file)]
terms = [line.rstrip('\n') for line in open(terms_file)]

result_rows = []

for folder_item in folders:
    # Each line in folders.txt has a label, a path, and a base URL separated by whitespace.
    # (The "None" arg to split() says "any amount of whitespace is the separator".)
    folder_info = folder_item.split(None, 2)
    docset = folder_info[0].strip()
    folder = folder_info[1].strip()
    base_url = folder_info[2].strip()

    # Use # as a comment in folder.txt; skip the line
    if docset.startswith('#'):
        continue

    print('take-inventory: Processing ' + docset + ' at ' + folder)

    # Now loop through the terms and run findstr to generate intermediate result files
    for term in terms:
        # Ignore commented-out terms
        if term.startswith('#'):
            print('take-inventory: Ignoring commented term "%s"' % (term))
            continue

        print('take-inventory: Searching %s for "%s"' %(docset, term))
        
        term = re.compile(term, re.IGNORECASE | re.MULTILINE)
        for root, dirs, files in os.walk(folder):
            for file in files:
                if pathlib.Path(file).suffix != '.md':
                    continue
                full_path = os.path.join(root, file)
                try:
                    content = pathlib.Path(full_path).read_text()
                except UnicodeDecodeError:
                    print("WARNING: File {} contains non-UTF-8 characters: Must be converted. Skipping.".format(full_path))
                    continue

                # Finding the first match is sufficient for inventory purposes - it will likely occur
                # multiple times in the file.
                match = term.search(content)
                if match is not None:
                    line_start = content.rfind("\n", match.span()[0])
                    line_end = content.find("\n", match.span()[1])
                    line = content[0:match.span()[0]].count("\n") + 1
                    url = full_path.replace(folder, base_url).replace('.md','').replace('\\','/')
                    result_rows.append([docset, full_path, url, term.pattern, line, content[line_start:line_end]])

# Sort the results (by filename, then line number), because a sorted list is needed for
# consolidate.py, and this removes the need to open the .csv file in Excel for a manual sort.
print("take-inventory: Sorting results by filename")
result_rows.sort(key=lambda row: (row[1], int(row[4])))  # Use int on [4] to sort the line numbers numerically

# Open CSV output file, which we do before running the searches because
# we consolidate everything into a single file

result_filename = get_next_filename()
print('take-inventory: Writing CSV results file %s.csv' % (result_filename))

with open(result_filename + '.csv', 'w', newline='', encoding='utf-8') as csv_file:    
    writer = csv.writer(csv_file)
    writer.writerow(['Docset', 'File', 'URL', 'Term', 'Line', 'Extract'])
    writer.writerows(result_rows)

print("take-inventory: Completed first CSV results file")
print("take-inventory: Invoking secondary processing to extract metadata")

# Run the other scripts, which can also be run independently 
subprocess.call('python extract-metadata.py %s.csv' % (result_filename))

# HACK: assumes knowledge of the extract-metadata.py file naming...
subprocess.call('python consolidate.py --terms=%s %s-metadata.csv' % (terms_file, result_filename))
