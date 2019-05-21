# Custom filtration--read a .CSV file line by line and do something else to it.

import sys
import requests
from bs4 import BeautifulSoup

USER_AGENT = {'User-Agent':'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/61.0.3163.100 Safari/537.36'}

def parse_time_to_read(soup):
    result = soup.find('li', attrs={'class': 'readingTime'})
    time_string = result.text.split()[0]
    return int(time_string)


def count_intro_links(soup):
    # The <nav class="center-doc-outline"> is the element that precedes the page content, so we start iterating there
    nav_element = soup.find('nav', attrs={'id': 'center-doc-outline'})
    next_element = nav_element.find_next_sibling()

    count = 0

    while next_element.name != "h2":        
        count += len(next_element.find_all('a'))
        next_element = next_element.find_next_sibling()

    return count


def count_code_blocks(soup, languages):    
    count = 0

    for language in languages:
        count += len(soup.find_all('code', attrs={'class': "lang-" + language}))

    return count

def extract_secondary(input_file, output_file):    
    print("extract-secondary: Starting extraction")

    with open(input_file, encoding='utf-8') as f_in:
        import csv

        reader = csv.reader(f_in)    
        headers = next(reader)

        index_url = headers.index("URL")

        with open(output_file, 'w', encoding='utf-8', newline='') as f_out:        
            writer = csv.writer(f_out)

            # Append the columns we'll be adding
            headers.append("MinutesToRead")
            headers.append("LinksInIntroduction")
            headers.append("CodeBlocksPython")
            headers.append("CodeBlocksCLI")

            writer.writerow(headers)

            for row in reader:
                url = row[index_url]
                print("extract-secondary: processing %s" % (url))

                # Go get the page content
                response = requests.get(url, headers=USER_AGENT)
                response.raise_for_status()
                page_text = response.text

                # We need the BeautifulSoup object for multiple parsings, so create it once
                soup = BeautifulSoup(page_text, 'html.parser')

                time = parse_time_to_read(soup)
                link_count = count_intro_links(soup)

                # Note: an inconsistency in article is use of "python" or "Python" for code block
                # languages, which comes through in the HTML as lang-python and lang-Python, both of
                # which we must count
                code_count = count_code_blocks(soup, ["javascript", "js", "JS", "JavaScript"])
                cli_count = count_code_blocks(soup, ["cli", "ps", "bash"])

                row.append(time)
                row.append(link_count)
                row.append(code_count)
                row.append(cli_count)

                writer.writerow(row)

    print("extract-secondary: Competed extraction")

if __name__ == "__main__":
    if len(sys.argv) == 1:
        print("Usage: python extract-secondary.py <input_file>")
        print("<input_csv_file.csv> is the output from consolidate.py")

    input_file = sys.argv[1]  # File is first argument; [0] is the .py file

    # Making the output filename assumes the input filename has only one .
    elements = input_file.split('.')
    output_file = elements[0] + '-secondary.' + elements[1]

    extract_secondary(input_file, output_file)
