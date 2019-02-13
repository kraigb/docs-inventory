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
result_file = 'results_' + str(today) + '.csv'

print('Opening CSV results file')

with open(result_file, 'w', newline='', encoding='utf-8') as csv_file:
    import csv
    writer = csv.writer(csv_file)
    writer.writerow(['Docset', 'File', 'Term', 'Line', 'Extract'])

    for folder_item in folders:
        # Each line in folders.txt has a label, then a space, so separate these
        folder_info = folder_item.split(" ", 1)
        docset = folder_info[0]
        folder = folder_info[1]

        print('Processing ' + docset + ' at ' + folder)

        # Now loop through the terms and run findstr to generate intermediate result files
        for term in terms:
            print('Searching ' + docset + ' for ' + term)

            text_file = 'text_results\\' + folder_info[0] + '-' + term.replace(' ', '-').lower() + '.txt'

            # folder_info [1] is the folder name
            command = 'findstr /S /L /N "' + term + '" ' + folder_info[1] + '\*.md > ' + text_file

            print('Running ' + command)
            os.system(command)

            # Now process text results into CSV results
            with open(text_file, encoding="utf8") as f:
                print('Processing ' + text_file + ' into CSV')

                for line in f:
                    # Each line is <path>:<line>:<extract>. We split using the colon delimeter,
                    # but not after the third occurrence, which should be the : before <extract>.
                    # This avoids splitting the extract. We can then easily join the drive and
                    # path back together. (This is specific to Windows!)

                    elements = line.split(":", 3)
                    path = elements[0] + ':' + elements[1]
                    line = elements[2]
                    extract = elements[3].strip()

                    writer.writerow([docset, path, term, line, extract])

print("Completed CSV results file")
