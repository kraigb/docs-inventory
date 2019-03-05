# Script to use the Cognitive Services key phrase extraction API to process the contents
# of source files listed in a CSV file. The input file should be relatively small to minimize
# service usage (and not exceed free tier limits).
#
# Yo provide the endpoint and API key for your specific subscription through command line args.

import http.client, urllib.request, urllib.parse, urllib.error, base64
import json
import numpy as np
import sys
from utilities import parse_endpoint_key_arguments

# Constants -- this limit is imposed by the API
max_doc_length = 5000

def get_key_phrases(endpoint, headers, params, body_text):
    try:
        conn = http.client.HTTPSConnection(endpoint)
        conn.request("POST", "/text/analytics/v2.0/keyPhrases?%s" % params, body_text, headers)
        response = conn.getresponse()
        data = response.read()        
        conn.close()
        return data
    except Exception as e:
        print("[Errno {0}] {1}".format(e.errno, e.strerror))
        return None


def split_at_last_paragraph(text, max_length):
    if (len(text) < max_length):
        return (text, None)
    else:
        # Find the last \n up to max_length
        pos1 = text.rfind('\n', 0, max_length)
        
        # If for some reason there's no new line, just chop at 
        # the length boundary; we might occasionally lose an important
        # word here, so we could be more sophisticated if we want, but
        # this is good enough to start.
        if (pos1 == -1):
            pos1 = max_length

        return (text[:pos1], text[(pos1 + 1):])

def extract_key_phrases(endpoint, key, input_file, output_file):
    print("extract-key-phrases: Starting key phrase extraction")

    headers = {
        # Request headers
        'Content-Type': 'application/json',
        'Ocp-Apim-Subscription-Key': key,
    }

    params = urllib.parse.urlencode({})

    with open(input_file, encoding='utf-8') as f_in:
        import csv
        # Output CSV has the same structure with added KeyPhrases column
        reader = csv.reader(f_in) 
    
        csv_headers = next(reader)
        csv_headers.append("KeyPhrases")
        index_file = csv_headers.index("File")

        with open(output_file, 'w', encoding='utf-8', newline='') as f_out:
            writer = csv.writer(f_out)
            writer.writerow(csv_headers)

            # Now go through each source file listed in the .csv, and run key phrase extraction.
            # Cognitive Services has a 5K per "document" limit, which means an item in the JSON
            # documents collection. There can be 1000 items in the collection.
            # 
            # For us, this means reading the file contents, then splitting the text at appropriate
            # boundaries. For starters, we just do this at the nearest \n to the 5K limit. 
            
            for row in reader:
                filename = row[index_file]

                if filename == '':
                    continue

                with open(filename, 'r', encoding="utf-8") as f_source:
                    print("extract-key-phrases: Processing %s" % (filename))
                    
                    text = f_source.read()

                    # Strip off header by finding position of second "---" 
                    blocks = text.split("---", 2)

                    if len(blocks) < 3:
                        print("extract-key-phrases: Skipping file that appears to have a malformed metadata header, %s" % (filename))
                        continue;

                    # Use just the text past the header
                    text = blocks[2]

                    documents = []
                    id = 1                

                    while (len(text) > 0):
                        if len(text) > max_doc_length:
                            # Find the last \n up to the max length
                            last_para_pos = text.rfind('\n', 0, max_doc_length)
                            text_doc = text[:last_para_pos]
                            text = text[(last_para_pos + 1):]
                        else:
                            text_doc = text
                            text = ''
                                            
                        documents.append({ "language": "en", "id": id, "text": text_doc })
                        id += 1                    
                    
                    body_json = {"documents": documents}
                    data = get_key_phrases(endpoint, headers, params, json.dumps(body_json))
                    data_json = json.loads(data)
                    key_phrases = []

                    # Combine the list of key phrases for the documents, which is then the 
                    # key phrases for the source file as a whole.
                    for doc in data_json["documents"]:
                        key_phrases = sorted(np.unique(key_phrases + doc["keyPhrases"]))

                    # Append the phrases list (; separated) to the CSV row and write it.
                    row.append(';'.join(key_phrases))
                    writer.writerow(row)

    print("extract-key-phrases: Competed extraction")

if __name__ == "__main__":
    # Get input file arguments, defaulting to folders.txt and terms.txt
    endpoint, key, args = parse_endpoint_key_arguments(sys.argv[1:])

    if endpoint == None or key == None or args == None:
        print("Usage: python extract-key-phrases.py --endpoint <endpoint_url> --key <api_key> <input_file>")
        sys.exit(2)

    # Making the output filename assumes the input filename has only one .
    input_file = args[0]
    elements = input_file.split('.')
    output_file = elements[0] + '-key-phrases.' + elements[1]

    extract_key_phrases(endpoint, key, input_file, output_file)