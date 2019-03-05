# Script to take the output of take-inventory.py (a .csv file), and go and open
# the specific files therein to extract author, date, H1, and other metadata,
# producing a second, more extensive .csv file (named with a "-with-metadata" suffix).
#
# take-inventory.py invokes this script automatically at the end of its processing

import sys

def extract_metadata(input_file, output_file):
    print("extract-metadata: Starting metadata extraction")

    with open(input_file, encoding='utf-8') as f_in:
        import csv
        # Input file is assumed to have this order: docset, file, term, line, extract
        reader = csv.reader(f_in)    
        
        with open(output_file, 'w', encoding='utf-8', newline='') as f_out:
            # Output file order is docset, file, URL, term, msauthor, author, msdate, mssservice, line,
            # extract, H1, title, and description
            
            writer = csv.writer(f_out)
            writer.writerow(['Docset', 'File', 'URL', 'Term', 'MSAuthor', 'Author', 'Manager', 'MSDate', 'MSService', 'Line', 'Extract', 'H1', 'Title', 'Description'])

            # As we iterate on the rows in the input file, if the filename is the same as the
            # previous iteration, we use the same metadata values from that iteration to avoid
            # the unneeded redundancy.
            prev_file = ''
            
            h1 = ''

            # The strings we look for to find metadata
            metadata_text = { 'title' : 'title:', 'description' : 'description:', 'msdate' : 'ms.date:', 'author' : 'author:', 'msauthor' : 'ms.author:', 'manager' : 'manager:', 'msservice' : 'ms.service:'}
            
            # The metadata values we find, which we carry from row to row
            metadata_values = { 'title' : '', 'description': '', 'msdate' : '', 'author' : '', 'msauthor' : '', 'manager' : '', 'msservice' : ''}
            
            next(reader)  # Skip the header line

            count = 0

            for row in reader:
                # Most of these variables are just for clarity in the program here
                docset = row[0]
                filename = row[1]
                url = row[2]
                term = row[3]
                line_number = row[4]
                extract = row[5]

                if filename == prev_file:
                    # Don't do anything, because the values of the metadata variables are still valid
                    pass
                else:
                    # Reset metadata values in case one or more of them aren't present; we don't want previous
                    # values to accidentally carry over.
                    metadata_values = { 'title' : '', 'description': '', 'msdate' : '', 'author' : '', 'msauthor' : '', 'manager' : '', 'msservice' : ''}
                    h1 = ''

                    with open(filename, encoding='utf-8') as docfile:
                        # To keep this simple, we read lines from the file and look for
                        # the metadata matches, and stopping when we reach the first line that starts
                        # with '#' which is assumed to be the H1.

                        # Guard against encoding issues in files, and print filename to allow for correction.
                        try:
                            metadata_header_count = 0

                            for line in docfile:                        
                                # Check for H1 and exit the loop if we find it. A special case is that some files have # comments in 
                                # the metadata, so we make sure we've seen two '---' lines first. We use find instead of
                                # startswith because some files have non-utf-8 encoding at the beginning; -1 means "not found".
                                if line.find('---') != -1:
                                    metadata_header_count += 1
                                    continue
                                
                                if line.startswith("#") and metadata_header_count >= 2:
                                    h1 = line.lstrip("# ")  # Remove all leading #'s and whitespace 
                                    break

                                for key in metadata_text:
                                    if line.startswith(metadata_text[key]):
                                        metadata_values[key] = line.split(":", 1)[1].strip()  # Remove metadata tag
                        except:
                            print("extract-metadata: Encoding error in " + filename + "; skipping. Open the file directly and check for issues.")

                    # At this point, all the metadata_values are set

                writer.writerow([docset, filename, url, term, metadata_values['msauthor'],
                                metadata_values['author'], metadata_values['manager'],
                                metadata_values['msdate'], metadata_values['msservice'],
                                line_number, extract, h1, metadata_values['title'], metadata_values['description']])

                prev_file = filename

    print("extract-metadata: Completed metadata extraction")

if __name__ == "__main__":
    if len(sys.argv) == 1:
        print("Usage: python extract-metadata.py <input_csv_file.csv>")
        print("<input_csv_file.csv> is the output from take-inventory.py")

    input_file = sys.argv[1]  # File is first argument; [0] is the .py file

    # Making the output filename assumes the input filename has only one .
    elements = input_file.split('.')
    output_file = elements[0] + '-metadata.' + elements[1]

    extract_metadata(input_file, output_file)