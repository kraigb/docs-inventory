import os

# For each path in folders.txt, invoke findstr (a Windows tool) for each term in terms.txt.
# This script works only on Windows.

# Get folders list
folders = [line.rstrip('\n') for line in open('folders.txt')]
terms = [line.rstrip('\n') for line in open('terms.txt')]

# Open CSV output file, which we do before running the searches because
# we consolidate everything into a single file

import datetime
today = datetime.date.today()
from random import randint
suffix = '-' + str(randint(1000,9999))
result_file = 'results_' + str(today) + suffix + '.csv'

print('Opening CSV results file')

from slugify import slugify

with open(result_file, 'w', newline='', encoding='utf-8') as csv_file:
    import csv
    writer = csv.writer(csv_file)
    writer.writerow(['Docset', 'File', 'URL', 'Term', 'Line', 'Extract'])

    for folder_item in folders:
        # Each line in folders.txt has a label, a path, and a base URL separated by whitespace.
        # (The "None" arg to split() says "any amount of whitespace is the separator".)
        folder_info = folder_item.split(None, 2)
        docset = folder_info[0].strip()
        folder = folder_info[1].strip()
        base_url = folder_info[2].strip()

        # Use # as a comment in folder.txt; skip the line
        if (docset.startswith('#')):
            continue

        print('Processing ' + docset + ' at ' + folder)

        # Now loop through the terms and run findstr to generate intermediate result files
        for term in terms:
            print('Searching ' + docset + ' for ' + term)

            text_file = 'text_results\\' + docset + '-' + slugify(term) + '.txt'
                        
            command = 'findstr /S /R /N /I /C:"' + term + '" ' + folder + '\*.md > ' + text_file

            print('Running ' + command)
            os.system(command)

            # Now process text results into CSV results
            with open(text_file, encoding="utf-8") as f:
                print('Processing ' + text_file + ' into CSV')

                count = 0

                for line in f:
                    count = count + 1

                    # Each line is <path>:<line>:<extract>. We split using the colon delimeter,
                    # but not after the third occurrence, which should be the : before <extract>.
                    # This avoids splitting the extract. We can then easily join the drive and
                    # path back together. (This is specific to Windows!)
                    elements = line.split(":", 3)

                    # Guard against bad lines in the findstr output
                    if (len(elements) < 3):
                        print('Line %s contains an error' % (count))
                        continue;

                    path = elements[0] + ':' + elements[1]
                    line = elements[2]

                    # Strip all leading and trailing whitespace from the extract, along with any
                    # leading - signs because when Excel imports the .csv file it otherwise treats
                    # those lines as formulas, inserts an =, and ends up showing "#NAME?" 
                    extract = elements[3].strip().lstrip("-")

                    # Generate the URL from the file path, which just means replacing the folder
                    # with the base_url, removing ".md", and replacing \\ with /
                    url = path.replace(folder, base_url).replace('.md', '').replace('\\', '/')

                    writer.writerow([docset, path, url, term, line, extract])

print("Completed first CSV results file, invoking secondary processing to extract metadata")

import subprocess
subprocess.call('python extract-metadata.py ' + result_file)
