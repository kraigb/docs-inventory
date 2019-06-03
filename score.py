# Script to take the output of consolidate.py and calculate a scoring value based on the criteria
# below. This is done as a separate script to allow for changes in the scoring algorithm without
# messing with consolidation.

import sys
import json
from utilities import parse_config_arguments, TAGS, COLUMNS

def score(input_file, output_file):
    print("score, INFO, Starting scoring, {}".format(input_file))

    with open(input_file, encoding='utf-8') as f_in:
        import csv    
        reader = csv.reader(f_in)    
        headers = next(reader)

        with open(output_file, 'w', encoding='utf-8', newline='') as f_out:        
            writer = csv.writer(f_out)

            # Insert a "score" column in the headers when we write, then remove it so we don't mess
            # with the indexes using header.index.                    
            headers.insert(0, COLUMNS["score"])
            writer.writerow(headers)
            headers.remove(COLUMNS["score"])

            current_row = next(reader)

            while current_row is not None:

                # Calculate and insert the score.
                #
                # Factors:
                #    text_score: link_text + text_intro + text
                #    non_text_score: Sum of meta_title, meta_description, meta_keywords, h1_heading, subheading, code_fence, and in_filename
                #

                text_cols = ["link_text", "text_intro", "text"]
                text_score = sum(int(current_row[headers.index(TAGS[column])]) for column in text_cols)
                
                non_text_cols = ["meta_title", "meta_description", "meta_keywords", "h1_heading", "subheading", "code_fence", "in_filename"]
                non_text_score = sum(int(current_row[headers.index(TAGS[column])]) for column in non_text_cols)

                # The first case here catches instances with a high text count but without the term showing up in the non_text_score areas.
                if non_text_score == 0 and text_score >= 6:
                    score = text_score
                else:
                    # Otherwise, score as non-zero anything with text_score >=3, multiplying by non_text_score to give a weigting of sorts.
                    score = text_score * non_text_score if text_score >= 3 else 0                

                # Write score only if non-zero
                if score != 0:
                    current_row.insert(0, score)
                    writer.writerow(current_row)

                current_row = next(reader, None)  # Assigns None if we're at the end

    print("score, INFO, Scoring complete, ,")

if __name__ == "__main__":    
    if len(sys.argv) == 1:
        print("Usage: python score.py <input_csv_file.csv>")
        print("<input_csv_file.csv> is the output from consolidate.py")
        sys.exit(2)

    # Making the output filename assumes the input filename has only one .
    input_file = sys.argv[1]
    elements = input_file.split('.')
    output_file = elements[0] + '-scored.' + elements[1]

    score(input_file, output_file)
