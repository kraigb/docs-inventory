import datetime
import getopt
import os
import re
import sys

# Maps internal classification tags to labels in the CSV files
TERM_CLASSIFICATION = {
    "meta_title": "meta_title", 
    "link_text": "link_text",
    "link_url": "link_url",
    "media_url" : "media_url",
    "alt_text": "alt_text",
    "html_misc": "html_misc",
    "meta_title": "meta_title",
    "meta_description": "meta_description",
    "meta_keywords": "meta_keywords",
    "meta_ms": "meta_ms",
    "meta_redirect": "meta_redirect",
    "h1": "h1", 
    "subheading": "subheading",
    "code_fence": "code_fence",
    "code_inline": "code_inline",
    "code_block": "code_block",
    "text": "text"
}    

def get_next_filename(prefix=None):    
    """ Determine the next filename by incrementing 1 above the largest existing file number in the current folder for today's date."""

    today = datetime.date.today()

    date_pattern = prefix + '-results_' + str(today)
    files = [f for f in os.listdir('.') if re.match(date_pattern + '-[0-9]+.csv', f)]

    if (len(files) == 0):
        next_num = 1
    else:
        num_start_index = len(prefix) + 20  # position of "0001" and such
        file_nums = [item[num_start_index:num_start_index + 4] for item in files ]
        next_num = max(int(n) for n in file_nums) + 1

    return "%s-%04d" % (date_pattern, next_num) 


def parse_config_arguments(argv):
    """ Parses an arguments list for take-inventory.py, returning config file name. Any additional arguments after the options are included in the tuple."""
    config_file = "config.json"

    try:
        opts, args = getopt.getopt(argv, 'hH?', ["config="])
    except getopt.GetoptError:
        return (None, None, None)

    for opt, arg in opts:
        if opt in ('-h', '-H', '-?'):
            return (None, None, None)

        if opt in ('--config'):
            config_file = arg
    
    return (config_file, args)


def parse_endpoint_key_arguments(argv):
    """ Parses an arguments list for extract-key-phrases.py, returning an endpoint and API key (tuple), with no defaults. Any additional arguments after the options are included in the tuple."""

    endpoint = None
    key = None

    try:
        opts, args = getopt.getopt(argv, 'e:k:hH?', ["endpoint=", "key="])
    except getopt.GetoptError:
        return (None, None, None)

    for opt, arg in opts:
        if opt in ('-h', '-H', '-?'):
            return (None, None, None)

        if opt in ('--endpoint', '-e'):
            endpoint = arg

        if opt in ('--key', '-k'):
            key = arg
    
    return (endpoint, key, args)

def parse_filters_arguments(argv):
    """ Parses an arguments list for apply-filters.py, returning a filters file and additional args in a tuple."""
    filters_file = 'filters.txt'    

    try:
        opts, args = getopt.getopt(argv, 'fhH?', ["filters="])
    except getopt.GetoptError:
        return (None, None, None)

    for opt, arg in opts:
        if opt in ('-h', '-H', '-?'):
            return (None, None, None)

        if opt in ('--filters', '-f'):
            filters_file = arg
    
    return (filters_file, args)


def make_identifier(name):
    """Converts the given name to a valid Python identifier by replacing spaces with an underscore and removing any other characters that aren't letters, numbers, or underscores. Identifiers also cannot begin with a number."""
    
    # Replace spaces with underscores.
    name = name.replace(' ', '_')

    # Remove any other invalid characters
    name = re.sub('[^0-9a-zA-Z_]', '', name)

    # Remove leading characters until we find a letter or underscore
    name = re.sub('^[^a-zA-Z_]+', '', name)

    return name


def find_nth(string, substring, n):
   if (n == 1):
       return string.find(substring)
   else:
       return string.find(substring, find_nth(string, substring, n - 1) + 1)


def delineate_code_blocks(content):
    """Scans through content, building a list of pairs of line numbers that contain code blocks. The list also
    includes the language tag of that code block.

    BUG BUG This code looks for code blocks marked with ```<language_tag>. It doesn't find code blocks with only indentation.
    If we find cases of such code, we should really fix them in the docs by adding a code fence if possible.
    """

    code_blocks = []

    # Code blocks are delineated by pairs of ```'s at the beginning of a line or within a callout starting with >.
    # Any indentation is allowed. The pattern is <whitespace><optional ">"><whitespace>```<language><whitespace>\n,
    # which is the regex "\s*>?\s*`{3}([\S]+)?\s*\n". The trailing whitespace is needed because extra spaces
    # occur in some articles.

    line_num = 0    
    start_line = 0
    in_a_block = False
    language = ""

    for line in iter(content.splitlines(1)):  # 1 includes \n
        line_num += 1

        match = re.match("\s*>?\s*`{3}([\S]+)?\s*\n", line)
        
        if match:
            if not in_a_block:
                start_line = line_num
                in_a_block = True
                language = match.group(1)
            else:
                item = language, start_line, line_num
                code_blocks.append(item)
                in_a_block = False

    return code_blocks


def is_whitelist_language(term):
    # List of known language terms
    WHITELIST_LANGUAGE_TAGS = ["python", "node", "js", "node.js", "typescript", "java"]

    return True if term.lower() in WHITELIST_LANGUAGE_TAGS else False


def is_codefence(line, term):
    # A codefence means the term matches a list of known languages and is immediately preceded by ```; the line
    # also ends immediately after the term (stripping whitespace)
    
    line = line.lower().strip()  # Remove whitespace to account for instances where code fence has spaces after it
    term_lower = term.lower()    

    if is_whitelist_language(term_lower):
        pos = line.find(term_lower)

        if pos >= 3 and line[pos-3:pos] == "```" and (pos + len(term_lower)) == len(line):            
            return True

    return False


def classify_occurrence(line, pos_end, term, line_num, filename, code_blocks):
    """Classifies the occurrences of term within line, returning a classification tag. Return value is a list
    of keys in the TERM_CLASSIFICATION list. Here, line contains the full line of text; pos_end indicates the ending
    position of the term, which is needed when we have to look at the preceding text only.
    """

    # Some checks need the line text only up to the instance of the term.
    line_trunc = line[:pos_end]


    # Code-fence cases: term is a whitelisted language and is preceded directly by ```        
    if is_codefence(line, term):
        return TERM_CLASSIFICATION["code_fence"]


    # Inline code is contained within a pair of ` or a pair of ```. To detect this, we count the number of ticks
    # preceding the term in the line. If the count is odd, then the term is within the ticks and is inline code.
    if line_trunc.count("`") % 2 != 0:
        return TERM_CLASSIFICATION["code_inline"]


    # Code block cases: check if the occurrence line number falls within a known code block. The line text itself,
    # in this case, is indeterministic, which is why we go by line numbers.
    #
    # This check must be done before checking for other instance, because code in a block could include a
    # URL, a command that uses the term, etc.
    if any(lower < line_num < upper for (_, lower, upper) in code_blocks):
        return TERM_CLASSIFICATION["code_block"]

    
    # Preceding text cases: checked from innermost cases first, e.g. link_url before link_text.
    #    media_url: term is preceded by "src=", "<img", or "<video"
    #    alt_text: term is preceded by "![" or "alt="
    #    link_url: term is preceded by "](", "][", href=", or "]: "
    #    link_text: term is preceded by "[" or "<a"    
    #    h1: term is preceded by "<h1"
    #    subheading: term is is preceded by "<h" (check after looking for h1 specifically)

    mappings = { "alt_text": ["![", "alt="],
        "link_url": ["](", "][", "href=", "]: "], "link_text": ["[", "<a"],
        "media_url": ["src=", "<img", "<video"],
        "h1": ["<h1"], "subheading": ["<h2", "<h3", "<h4", "<h5"]
        }

    for key, values in mappings.items():
        if any(line_trunc.rfind(value) != -1 for value in values):
            return TERM_CLASSIFICATION[key]


    # Beginning of line cases, including VS Code alternate metadata tags. Check these after checking
    # the "preceding text" cases    
    #    meta_title: line begins with "title:"
    #    meta_description: line begins with "description:"
    #    meta_keywords: line begins with "keywords:"
    #    meta_ms: line begins with "ms.devlang:" or "ms.technology:", or term occurs under "ms.workload:"
    #    meta_redirect: line begins with "redirect_url:"
    #    h1: line begins with "# "
    #    subheading: line begins with "##"
    #    html_misc: line starts with "<!--" or "<div"

    mappings = {"meta_title": ["title:", "TOCTitle:", "PageTitle:"], "meta_description": ["description:", "MetaDescription:"],
        "meta_keywords": ["keywords:"], "meta_ms": ["ms.devlang:", "ms.technology:", "Area:", "documentationcenter:"],
        "meta_redirect": ["redirect_url:"], "h1": ["# "], "subheading": ["##"], "code_block": ["<pre"], "html_misc" : ["<!--", "<div"]
        }
    
    for key, values in mappings.items():
        if any(line_trunc.startswith(value) for value in values):
            return TERM_CLASSIFICATION[key]


    # SPECIAL HACK SECTION :) All of these are here to get the .csv to come out right without
    # added manual classification. In some of these cases, we can certainly go fix the files in question,
    # but to keep them consistent within their docset would require changing a number of other files.
    # Thus adding special cases to this inventory tool is simpler.

    # Special case #1:
    #    A line beginning with "- <term>" where term is a language, and the line number if < 20 (generally meaning a
    #    header then it's an ms.workload entry in the VS Docs, which we classify as meta_ms. There are no known
    #    false positives for these criteria. Other instances past line 20 are text in a bullet list.

    if line_num <= 20:
        if is_whitelist_language(term) and line_trunc.lower().startswith("- " + term.lower()):
            return TERM_CLASSIFICATION["meta_ms"]

    # Special case #2:
    #   azure-docs-pr\articles\service-fabric\service-fabric-service-model-schema.md contains a length Python script
    #   inside an HTML comment. A number of lines in this article show up for "Python" but are false positives, to
    #   we classify lines starting with "file.write" as html_misc
    if filename == "service-fabric-service-model-schema.md":
        if line_trunc.startswith("file.write"):
            return TERM_CLASSIFICATION["html_misc"]

    # Special case #3:
    #   azure-docs-pr\articles\key-vault\key-vault-hsm-protected-keys.md contains a bunch of Python CLI commands
    #   that have nothing to do with Python; those commands aren't in code fences at all, and should be classified
    #   as code_block.
    if filename == "key-vault-hsm-protected-keys.md":
        if line_trunc.startswith('"%nfast_home'):
            return TERM_CLASSIFICATION["html_misc"]

    # Special case #4:
    #   azure-docs-pr\articles\hdinsight\spark\apache-spark-deep-learning-caffe.md has a lot of indented code blocks
    #   without fences, containing a bunch of CLI stuff. 
    if filename == "apache-spark-deep-learning-caffe.md":
        if line_trunc.startswith('sudo apt-get install') or line_trunc.startswith("<value>"):
            return TERM_CLASSIFICATION["code_block"]


    # If we get here, term is contained within regular text or some other unhandled case
    return TERM_CLASSIFICATION["text"]
