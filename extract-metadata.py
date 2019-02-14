# Script to take the output of take-inventory.py (a .csv file), and go and open
# the specific files therein to extract author, date, H1, and other metadata,
# producing a second, more extensive .csv file (named with a "-with-metadata" suffix).
#
# usage: python extract-metadata.py <input_csv_file.csv>
#
# take-inventory.py invokes this script automatically at the end of its processing

import sys
input_file = sys.argv[1]  # File is first argument; [0] is the .py file

# Making the output filename assumes the input filename has only one .
elements = input_file.split('.')
output_file = elements[0] + '-with-metadata.' + elements[1]

def remove_metadata_tag(str):
    return 

print("Starting metadata extraction")

with open(input_file, encoding='utf-8') as f_in:
    import csv
    # Input file is assumed to have this order: docset, file, term, line, extract
    reader = csv.reader(f_in)    
    
    with open(output_file, 'w', encoding='utf-8', newline='') as f_out:
        # Output file order is docset, file, term, msauthor, author, msdate, mssservice, line,
        # extract, H1, and title
        
        writer = csv.writer(f_out)
        writer.writerow(['Docset', 'File', 'Term', 'MSAuthor', 'Author', 'Manager', 'MSDate', 'MSService', 'Line', 'Extract', 'H1', 'Title'])

        # As we iterate on the rows in the input file, if the filename is the same as the
        # previous iteration, we use the same metadata values from that iteration to avoid
        # the unneeded redundancy.
        prev_file = ''
        
        h1 = ''

        # The strings we look for to find metadata
        metadata_text = { 'title' : 'title:', 'msdate' : 'ms.date:', 'author' : 'author:', 'msauthor' : 'ms.author:', 'manager' : 'manager:', 'msservice' : 'ms.service:'}
        
        # The metadata values we find, which we carry from row to row
        metadata_values = { 'title' : '', 'msdate' : '', 'author' : '', 'msauthor' : '', 'manager' : '', 'msservice' : ''}
        
        next(reader)  # Skip the header line        

        for row in reader:
            # Most of these variables are just for clarity in the program here
            docset = row[0]
            filename = row[1]
            term = row[2]
            line_number = row[3]
            extract = row[4]

            if (filename == prev_file):
                # Don't do anything, because the values of the metadata variables are still valid
                pass
            else:
                with open(filename, encoding='utf-8') as docfile:
                    # To keep this simple, we read lines from the file and look for
                    # the metadata matches, and stopping when we reach the first line that starts
                    # with '#' which is assumed to be the H1.

                    for line in docfile:
                        # Check for H1 and exit the loop if we find it
                        if (line.startswith("#")):
                            # Remove all leading #'s and whitespace 
                            h1 = line.lstrip("# ")
                            break

                        for key in metadata_text:
                            if (line.startswith(metadata_text[key])):
                                metadata_values[key] = line.split(":", 1)[1].strip()  # Remove metadata tag

                # At this point, all the metadata_values are set

            writer.writerow([docset, filename, term, metadata_values['msauthor'], metadata_values['author'], metadata_values['manager'], metadata_values['msdate'], metadata_values['msservice'], line_number, extract, h1, metadata_values['title']])

            prev_file = filename

print("Completed metadata extraction")
