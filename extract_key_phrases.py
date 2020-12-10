# Script to use the Cognitive Services key phrase extraction API to process the contents
# of source files listed in a CSV file. The input file should be relatively small to minimize
# service usage (and not exceed free tier limits).
#
# Yo provide the endpoint and API key for your specific subscription through command line args.

import http.client, urllib.request, urllib.parse, urllib.error, base64
import requests
import json
import numpy as np
import sys
from utilities import parse_endpoint_key_arguments, delineate_segments
import time

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

    # Constants -- this limit is imposed by the API
    max_doc_length = 5000

    headers = {
        # Request headers
        'Content-Type': 'application/json',
        'Ocp-Apim-Subscription-Key': key,
    }

    params = urllib.parse.urlencode({})
    all_phrases = []

    with open(input_file, encoding='utf-8') as f_in:
        import csv
        # Output CSV has the same structure with added KeyPhrases column
        reader = csv.reader(f_in) 
     
        csv_headers = next(reader)
        csv_headers.append("key_phrases")
        index_file = csv_headers.index("file")

        with open(output_file, 'w', encoding='utf-8', newline='') as f_out:
            writer = csv.writer(f_out)
            writer.writerow(csv_headers)

            # Now go through each source file listed in the .csv, and run key phrase extraction on 
            # the introductory text.                       

            for row in reader:
                filename = row[index_file]

                if filename == '':
                    continue

                with open(filename, 'r', encoding="utf-8") as f_source:
                    print("extract_key_phrases: Processing %s" % (filename))
                    
                    text = f_source.read()
                    #_, intro_lines, metadata_lines = delineate_segments(content, filename)

                    # Strip off header by finding position of second "---" 
                    blocks = text.split("---", 2)

                    if len(blocks) < 3:
                        print("extract_key_phrases: Skipping file that appears to have a malformed metadata header, %s" % (filename))
                        continue;

                    # Use just the text past the header
                    text = blocks[2]

                    # Separate to the next ## (any other subheading)
                    blocks = text.split("##", 1)
                    text = blocks[0][0:max_doc_length]                    

                    documents = []
                    documents.append({ "language": "en", "id": 1, "text": text })                    
                    body_json = {"documents": documents}
#                    data = get_key_phrases(endpoint, headers, params, json.dumps(body_json))
#                    data_json = json.loads(data)
                    keyphrase_uri = endpoint + "/keyphrases"
                    response = requests.post(keyphrase_uri, headers=headers, json=body_json)                    

                    # Combine the list of key phrases for the documents, which is then the 
                    # key phrases for the source file as a whole.
                    key_phrases = []

                    if response.status_code == 200:
                        for doc in response.json()["documents"]:
                            key_phrases = sorted(key_phrases + doc["keyPhrases"])
                            all_phrases[-1:-1] = key_phrases
                    else:
                        print("Response code %d, %s" % (response.status_code, response.text))

                    # Append the phrases list (; separated) to the CSV row and write it.
                    row.append(';'.join(key_phrases))
                    writer.writerow(row)

                    # Throttle ourselves to avoid Cognitive Services rate limits
                    time.sleep(1)

    all_phrases = sorted(np.unique(all_phrases))
    
    with open('phraselist.txt', 'w') as phrase_file:
        phrase_file.writelines([str(phrase) + "\n" for phrase in all_phrases])
 
    print("extract_key_phrases: Completed extraction")

if __name__ == "__main__":    
    endpoint, key, args = parse_endpoint_key_arguments(sys.argv[1:])

    if endpoint == None or key == None or args == None:
        print("Usage: python extract_key_phrases.py --endpoint <endpoint_url> --key <api_key> <input_file>")
        sys.exit(2)

    # Making the output filename assumes the input filename has only one .
    input_file = args[0]
    elements = input_file.split('.')
    output_file = elements[0] + '-keyphrases.' + elements[1]

    extract_key_phrases(endpoint, key, input_file, output_file)
