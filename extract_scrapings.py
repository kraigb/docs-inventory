# Custom filtration--read a .CSV file line by line and do something else to it.

import sys
import requests
from bs4 import BeautifulSoup
from utilities import COLUMNS

USER_AGENT = {'User-Agent':'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/61.0.3163.100 Safari/537.36'}

def parse_time_to_read(soup):
    result = soup.find('li', attrs={'class': 'readingTime'})

    if result == None:
        return -1

    time_string = result.text.split()[0]
    return int(time_string)


def count_intro_links(soup):
    # The <nav class="center-doc-outline"> is the element that precedes the page content, so we start iterating there
    nav_element = soup.find('nav', attrs={'id': 'center-doc-outline'})

    if nav_element == None:
        return -1

    next_element = nav_element.find_next_sibling()

    count = 0

    while next_element and next_element.name != "h2": 
        link_elements = next_element.find_all('a')

        for link in link_elements:
            # Check if we're in a selector div, whose third parent is a div with "op_single_selector".
            # If so, don't count this link.

            add_count = 1

            try:
                if link.parent.parent.parent.attrs["class"][0] == "op_single_selector":
                    add_count = 0
            except:
                pass
        
            count += add_count
            
        next_element = next_element.find_next_sibling()

    return count


def count_code_blocks(soup, languages):
    # Code blocks are <pre><code class="lang-language"> where "language" is a specific language name (case insensitive).
    # If the code block is unfenced, the class is BUG BUG

    count = 0
    blocks = soup.find_all('pre')

    # Looks for unfenced code blocks
    if languages == None:
        for block in blocks:
            code_block = block.findNext("code")

            if code_block != None and not code_block.has_key("class"):
                count += 1

        return count
        #return sum(block.text == "" for block in blocks)       

    # Look for code blocks for a list of specific languages
    for block in blocks:
        code_block = block.findNext("code")

        for language in languages:
            if code_block != None and code_block.has_key("class"):
                if code_block["class"][0].lower() == "lang-" + language.lower():
                    count += 1

    return count

def extract_scrapings(input_file, output_file):    
    print("extract_scrapings, INFO, Starting extraction, {}".format(input_file))

    with open(input_file, encoding='utf-8') as f_in:
        import csv

        reader = csv.reader(f_in)    
        headers = next(reader)

        index_url = headers.index(COLUMNS["url"])

        with open(output_file, 'w', encoding='utf-8', newline='') as f_out:        
            writer = csv.writer(f_out)

            # Append the columns we'll be adding
            headers.append("minutes_to_read")
            headers.append("links_in_intro")
            headers.append("code_blocks_python")
            headers.append("code_blocks_js")
            headers.append("code_blocks_java")
            headers.append("code_blocks_cli")
            headers.append("code_blocks_unfenced")

            writer.writerow(headers)

            file_count = 0

            for row in reader:
                url = row[index_url]
                file_count += 1

                if file_count % 100 == 0:
                    print("extract_scrapings, INFO, Files processed, {}".format(file_count))

                # Go get the page content
                try:
                    response = requests.get(url, headers=USER_AGENT)
                    response.raise_for_status()
                except:
                    print("extract_scrapings, WARNING, Request failed, {}".format(url))

                    # Write the row with -1's so we can a failed request in the output                    
                    for i in range(0,7):
                        row.append(-1)
                        
                    writer.writerow(row)
                    continue

                page_text = response.text

                # We need the BeautifulSoup object for multiple parsings, so create it once
                soup = BeautifulSoup(page_text, 'html.parser')

                time = parse_time_to_read(soup)
                link_count = count_intro_links(soup)

                # Note: an inconsistency in article is use of "python" or "Python" for code block
                # languages, which comes through in the HTML as lang-python and lang-Python, both of
                # which we must count
                code_count_python = count_code_blocks(soup, ["python"])
                code_count_js = count_code_blocks(soup, ["javascript", "js", "typescript", "node", "node.js"])
                code_count_java = count_code_blocks(soup, ["java"])
                code_count_cli = count_code_blocks(soup, ["cli", "ps", "bash", "shell"])
                code_count_unfenced = count_code_blocks(soup, None)

                row.append(time)
                row.append(link_count)
                row.append(code_count_python)
                row.append(code_count_js)
                row.append(code_count_java)
                row.append(code_count_cli)
                row.append(code_count_unfenced)

                writer.writerow(row)

    print("extract_scrapings, INFO, INFO, Competed extraction,, {}".format(output_file))

if __name__ == "__main__":
    if len(sys.argv) == 1:
        print("Usage: python extract_scrapings.py <input_file>, {}".format(input_file))
        print("<input_csv_file.csv> is the output from extract_metadata.py or consolidate.py")

    input_file = sys.argv[1]  # File is first argument; [0] is the .py file

    # Making the output filename assumes the input filename has only one .
    elements = input_file.split('.')
    output_file = elements[0] + '-scrapings.' + elements[1]

    extract_scrapings(input_file, output_file)
