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
    return str.split(":", 1)[1].strip()

print("Starting metadata extraction")

with open(input_file, encoding='utf-8') as f_in:
    import csv
    # Input file is assumed to have this order: docset, file, term, line, extract
    reader = csv.reader(f_in)    

    with open(output_file, 'w', encoding='utf-8', newline='') as f_out:
        # Output file order is docset, file, term, msauthor, author, msdate, mssservice, line,
        # extract, H1, and title
        
        writer = csv.writer(f_out)
        writer.writerow(['Docset', 'File', 'Term', 'MSAuthor', 'Author', 'MSDate', 'MSService', 'Line', 'Extract', 'H1', 'Title'])

        # As we iterate on the rows in the input file, if the filename is the same as the
        # previous iteration, we use the same metadata values from that iteration to avoid
        # the unneeded redundancy.
        prev_file = ''
        
        title = ''
        msdate = ''
        author = ''
        msauthor = ''      
        msservice = ''
        h1 = ''
       
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
                        # Yeah, all this is hard-coded, just to be simple                    
                        if (line.startswith("#")):
                            h1 = line.lstrip("#").strip()
                            break  # We're done, exit loop
                        elif (line.startswith("title:")):
                            title = remove_metadata_tag(line)
                        elif (line.startswith("ms.date:")):
                            msdate = remove_metadata_tag(line)
                        elif (line.startswith("author:")):
                            author = remove_metadata_tag(line)
                        elif (line.startswith("ms.author:")):
                            msauthor = remove_metadata_tag(line)
                        elif (line.startswith("ms.service:")):
                            msservice = remove_metadata_tag(line)
                        else:
                            pass  # Ignore the line

                # At this point, all the metadata values are set

            writer.writerow([docset, filename, term, msauthor, author, msdate, msservice, line_number, extract, h1, title])

            prev_file = filename

print("Completed metadata extraction")
