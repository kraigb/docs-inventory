# For each path in folders.txt, invoke findstr (a Windows tool) for each term in terms.txt.
# This script works only on Windows.

import csv
import os
import subprocess
import sys
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
        # Separate the term type and the term itself
        terms_info = term.split(None, 1)
        term_type = terms_info[0]
        term = terms_info[1]

        # Ignore commented terms when term type
        if term_type.startswith('#'):
            print('take-inventory: Ignoring commented term "%s"' % (term))
            continue

        print('take-inventory: Searching %s for "%s"' %(docset, term))

        text_file = 'text_results\\%s-%s.txt' % (docset, slugify(term))
        command = 'findstr /S /%s /N /I /C:"%s" %s\*.md > %s' % (term_type, term, folder, text_file)

        print('take-inventory: Running ' + command)
        os.system(command)

        # Now process text results into CSV results
        with open(text_file, encoding="utf-8") as input_file:
            print('take-inventory: Processing %s into CSV' % (text_file))

            count = 1

            try:
                for line in input_file:
                    # Each line is <path>:<line>:<extract>. We split using the colon delimeter,
                    # but not after the third occurrence, which should be the : before <extract>.
                    # This avoids splitting the extract. We can then easily join the drive and
                    # path back together. (This is specific to Windows!)
                    elements = line.split(":", 3)

                    # Guard against bad lines in the findstr output
                    if len(elements) < 3:
                        print('take-inventory: Line %s contains an error' % (count))
                        continue;

                    # Attach drive letter back to filename
                    path = elements[0] + ':' + elements[1]
                    line = elements[2]

                    # Skip index.md and toc.md/TOC.md
                    if any(skip_file in path.lower() for skip_file in ["toc.md", "index.md", "index.experimental.md"]):
                        continue;

                    # Strip all leading and trailing whitespace from the extract, along with any
                    # leading - signs because when Excel imports the .csv file it otherwise treats
                    # those lines as formulas, inserts an =, and ends up showing "#NAME?" 
                    extract = elements[3].strip().lstrip("-")

                    # Generate the URL from the file path, which just means replacing the folder
                    # with the base_url, removing ".md", and replacing \\ with /
                    url = path.replace(folder, base_url).replace('.md', '').replace('\\', '/')

                    result_rows.append([docset, path, url, term, line, extract])
                    count += 1
            except:
                print("take-inventory: Encoding error in %s at line %d" % (text_file, count))

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
