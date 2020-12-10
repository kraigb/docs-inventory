import datetime
import getopt
import os
import re
import sys

# List of known language terms
ALLOWLIST_LANGUAGE_TAGS = ["python", "node", "js", "javascript", "node.js", "typescript", "java"]


# Maps internal classification tags to labels in the CSV files
TAGS = {
    "meta_title": "meta_title", 
    "meta_description": "meta_description",
    "meta_keywords": "meta_keywords",
    "meta_other": "meta_other",
    "meta_redirect": "meta_redirect",
    "link_text": "link_text",
    "link_url": "link_url",
    "media_url" : "media_url",
    "alt_text": "alt_text",
    "html_misc": "html_misc",
    "h1_heading": "h1_heading", 
    "subheading": "subheading",
    "code_fence": "code_fence",
    "code_inline": "code_inline",
    "code_block": "code_block",
    "text_intro": "text_intro",
    "text": "text",
    "in_filename" : "in_filename"
}    

COLUMNS = {
    "score": "score",
    "docset": "docset",
    "file": "file",
    "url": "url",
    "msauthor": "msauthor", 
    "author": "author", 
    "manager": "manager", 
    "msdate": "msdate", 
    "msservice": "msservice",
    "mstopic": "mstopic",
    "term": "term",
    "tag": "tag",
    "line": "line",
    "extract": "extract",
    "term_total": "term_total",
    "in_filename": "in_filename",
    "h1": "h1",
    "title": "title",
    "description": "description"
}


def get_next_filename(prefix=None):    
    """ Determine the next filename by incrementing 1 above the largest existing file number in the current folder for today's date."""

    today = datetime.date.today()

    date_pattern = prefix + '_' + str(today)
    files = [f for f in os.listdir('.') if re.match(date_pattern + '-[0-9]+.csv', f)]

    if (len(files) == 0):
        next_num = 1
    else:        
        num_start_index = len(prefix) + 12  # position of "0001" and such
        file_nums = [item[num_start_index:num_start_index + 4] for item in files ]
        next_num = max(int(n) for n in file_nums) + 1

    return "%s-%04d" % (date_pattern, next_num) 


def parse_config_arguments(argv):
    """ Parses an arguments list for take_inventory.py, returning config file name. Any additional arguments after the options are included in the tuple."""
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
    """ Parses an arguments list for extract_key_phrases.py, returning an endpoint and API key (tuple), with no defaults. Any additional arguments after the options are included in the tuple."""

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
    """ Parses an arguments list for apply_filters.py, returning a filters file and additional args in a tuple."""
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

def line_starts_with_metadata(line, path):
    # Output warnings for these (needs to be fixed in the source)
    if line.startswith("ï»¿---"):
        print("take_inventory, WARNING, File is not utf-8 encoded, , {}".format(path))

    return line.startswith("---") or line.startswith("ï»¿---")

def delineate_segments(content, path):
    """Scans through content, building a list of pairs of line numbers that contain (a) code blocks, (b) introductory text (between H1 and the first subheading), and (c) the metadata header (one pair, lines delineated by ---).

    Returns a tuple of lists, code_blocks, intro_text, and metadata, where each list contains tuples with start and end line numbers. The code_blocks items include the language tag. The delineators of the segments are not included in the ranges.

    BUG BUG For code blocks, this code looks for code blocks marked with ```<language_tag>. It doesn't find code blocks with only indentation. That should be a content bug that's best to fix in the sources.
    """
    
    metadata = []    
    start_line = 0 
    metadata_only = True   # Checking only metadata at beginning
    in_metadata = False

    intro = []
    in_intro = False
    ignore_subsequent_headings = False

    code_blocks = []
    in_code_block = False
    start_code = 0
    language = ""
    
    line_num = 0

    for line in iter(content.splitlines(1)):  # The 1 arg means include \n
        line_num += 1

        # If the first line is NOT a metadata delineator, assume there is no metadata        
        if line_num == 1 and not line_starts_with_metadata(line, path):
            metadata_only = False

        # If we're scanning only metadata, ignore everything else until the ending ---
        if metadata_only:
            if line_starts_with_metadata(line, path):
                if not in_metadata:
                    start_line = line_num
                    in_metadata = True
                else:
                    item = start_line + 1, line_num - 1
                    metadata.append(item)
                    in_metadata = False
                    metadata_only = False    

            continue

        # Check for code blocks next, because various comments in a code block otherwise appear
        # as headings. Thus we look for headings only if we're not in a code block. A code block can,
        # however, legitimately occur within the intro text.

        # Code blocks are delineated by pairs of ```'s at the beginning of a line or within a callout starting with >.
        # Any indentation is allowed. The pattern is <whitespace><optional ">"><whitespace>```<language><whitespace>\n,
        # which is the regex "\s*>?\s*`{3}([\S]+)?\s*\n". The trailing whitespace is needed because extra spaces
        # occur in some articles.
        match_code_fence = re.match("\s*>?\s*`{3}([\S]+)?\s*\n", line)

        if match_code_fence:
            if not in_code_block:
                start_code = line_num
                in_code_block = True
                continue
            else:
                in_code_block = False                
                item = start_code + 1, line_num - 1, match_code_fence.group(1)  # Last item is the language tag
                code_blocks.append(item)                
                continue
        
        if in_code_block:
            continue

        # We care only about the first H1 segment
        if ignore_subsequent_headings:
            continue

        # H1, line begins with "# "; other heading begins with ##        
        line_is_h1 = line.startswith("# ")
        line_is_subheading = any(line.startswith(tag) for tag in ["## ", "<h2", "### ", "<h3", "#### ", "<h4"])        
       
        if line_is_h1 or line_is_subheading:
            # Warn on missing h1, but treat this first subheading as the h1 anyway
            if not in_intro and line_is_subheading:
                print("take_inventory, WARNING, Found subheading before finding an h1, '{}', {}".format(line.strip(), path))
                line_is_h1 = True

            if in_intro and line_is_h1:
                print("take_inventory, WARNING, Found second h1, '{}', {}".format(line.strip(), path))

            if not in_intro:
                # Start tracking the intro text
                start_line = line_num
                in_intro = True
            else:
                if line_is_subheading:                   
                    # Diagnostic check: output warning if subhead isn't an h2
                    if any(line.startswith(tag) for tag in ["### ", "<h3", "#### ", "<h4"]):
                        print("take_inventory, WARNING, Found h3/h4 following h1, '{}', {}".format(line.strip(), path))
                
                item = start_line + 1, line_num - 1
                intro.append(item)
                in_intro = False

                ignore_subsequent_headings = True

    if in_intro:
        # If we've run out of lines looking for the next heading, article has only a single H1, so close the range.       
        item = start_line + 1, line_num
        intro.append(item)

    return code_blocks, intro, metadata


def is_allowlist_language(term):
    return True if term.lower() in ALLOWLIST_LANGUAGE_TAGS else False


def is_codefence(line, term):
    # A codefence means the term matches a list of known languages and is immediately preceded by ```; the line
    # also ends immediately after the term (stripping whitespace)
    
    line = line.lower().strip()  # Remove whitespace to account for instances where code fence has spaces after it
    term_lower = term.lower()    

    if is_allowlist_language(term_lower):
        pos = line.find(term_lower)

        if pos >= 3 and line[pos-3:pos] == "```" and (pos + len(term_lower)) == len(line):            
            return True

    return False


def classify_occurrence(line, pos_end, term, line_num, filename, code_lines, intro_lines, metadata_lines):
    """Classifies the occurrences of term within lines, returning a classification tag. Return value is a list
    of keys in the TAGS list. Here, line contains the full line of text; pos_end indicates the ending
    position of the term, which is needed when we have to look at the preceding text only.
    """

    # Some checks need the line text only up to the instance of the term.
    line_trunc = line[:pos_end]


    # Code-fence cases: term is a allowed language and is preceded directly by ```        
    if is_codefence(line, term):
        return TAGS["code_fence"]


    # Inline code is contained within a pair of ` or a pair of ```. To detect this, we count the number of ticks
    # preceding the term in the line. If the count is odd, then the term is within the ticks and is inline code.
    if line_trunc.count("`") % 2 != 0:
        return TAGS["code_inline"]


    # Code block cases: check if the occurrence line number falls within a known code block. The line text itself,
    # in this case, is indeterministic, which is why we go by line numbers.
    #
    # This check must be done before checking for other instances, because code in a block could include a
    # URL, a command that uses the term, etc. We also do this check before flagging a term in the intro text,
    # because intro text could contain code blocks.
    if any(lower <= line_num <= upper for (lower, upper, _) in code_lines):
        return TAGS["code_block"]

    
    # Preceding text cases: checked from innermost cases first, e.g. link_url before link_text.
    #    media_url: term is preceded by "src=", "<img", or "<video"
    #    alt_text: term is preceded by "![" or "alt="
    #    link_url: term is preceded by "](", "][", href=", or "]: "
    #    link_text: term is preceded by "[" or "<a"    
    #    h1_heading: term is preceded by "<h1"
    #    subheading: term is is preceded by "<h" (check after looking for h1 specifically)

    mappings = {
        TAGS["link_url"]: ["](", "][", "href=", "]: "], 
        TAGS["alt_text"]: ["![", "alt="],
        TAGS["link_text"]: ["[", "<a"],
        TAGS["media_url"]: ["src=", "<img", "<video"],
        TAGS["h1_heading"]: ["<h1"],
        TAGS["subheading"]: ["<h2", "<h3", "<h4", "<h5"]
        }

    for key, values in mappings.items():
        if any(line_trunc.rfind(value) != -1 for value in values):
            return key


    # Beginning of line cases. Check these after checking the "preceding text" cases    
    #    meta_title: line begins with "title:"
    #    meta_description: line begins with "description:"
    #    meta_keywords: line begins with "keywords:"
    #    meta_other: elsewhere in the metadata
    #    meta_redirect: line begins with "redirect_url:"
    #    h1: line begins with "# "
    #    subheading: line begins with "##"
    #    html_misc: line starts with "<!--" or "<div"

    mappings = {
        TAGS["meta_title"]: ["title:", "TOCTitle:", "PageTitle:"],
        TAGS["meta_description"]: ["description:", "MetaDescription:"],
        TAGS["meta_keywords"]: ["keywords:"],        
        TAGS["meta_redirect"]: ["redirect_url:"],
        TAGS["h1_heading"]: ["# "],
        TAGS["subheading"]: ["##"],
        TAGS["code_block"]: ["<pre"],
        TAGS["html_misc"]: ["<!--", "<div"]
        }
    
    for key, values in mappings.items():
        if any(line_trunc.startswith(value) for value in values):
            return key


    # Any term that falls into the metadata range is meta_other. We look only at the first metadata
    if len(metadata_lines) >= 1:
        lower, upper = metadata_lines[0]
        
        if lower <= line_num <= upper:
            return TAGS["meta_other"]


    # SPECIAL HACK SECTION :) All of these are here to get the .csv to come out right without
    # added manual classification. In some of these cases, we can certainly go fix the files in question,
    # but to keep them consistent within their docset would require changing a number of other files.
    # Thus adding special cases to this inventory tool is simpler.

    # Special case #1:
    #   azure-docs-pr\articles\service-fabric\service-fabric-service-model-schema.md contains a length Python script
    #   inside an HTML comment. A number of lines in this article show up for "Python" but are false positives, to
    #   we classify lines starting with "file.write" as html_misc
    if filename == "service-fabric-service-model-schema.md":
        if line_trunc.startswith("file.write"):
            return TAGS["html_misc"]

    # Special case #2:
    #   azure-docs-pr\articles\key-vault\key-vault-hsm-protected-keys.md contains a bunch of Python CLI commands
    #   that have nothing to do with Python; those commands aren't in code fences at all, and should be classified
    #   as code_block.
    if filename == "key-vault-hsm-protected-keys.md":
        if line_trunc.startswith('"%nfast_home'):
            return TAGS["html_misc"]

    # Special case #3:
    #   azure-docs-pr\articles\hdinsight\spark\apache-spark-deep-learning-caffe.md has a lot of indented code blocks
    #   without fences, containing a bunch of CLI stuff. 
    if filename == "apache-spark-deep-learning-caffe.md":
        if line_trunc.startswith('sudo apt-get install') or line_trunc.startswith("<value>"):
            return TAGS["code_block"]


    # Term is otherwise just in text, which we distinguish between intro text and other text
    if any(lower <= line_num <= upper for (lower, upper) in intro_lines):
        return TAGS["text_intro"]

    return TAGS["text"]
