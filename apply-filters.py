# Custom filtration--read a .CSV file line by line and apply pandas queries, which provide
# the equivalent of what you can accomplish with filters in Excel; only here, you can automate
# the process and apply a wider range of filters to the same column.
#
# Filters are expressed in a filters.txt file, where each line is a pandas query to apply,
# passed in order to the pandas dataframe.filter method.

import pandas as pd
import sys
from utilities import get_next_filename, parse_filters_arguments

# Get input file arguments, defaulting to folders.txt and terms.txt
filters_file, args = parse_filters_arguments(sys.argv[1:])

if filters_file == None or args == None:
    print("Usage: python apply-filters.py [--filters <filters_file>] <input_file>\nFilters file defaults to filters. txt.")
    sys.exit(2)

input_file = args[0]

# Making the output filename assumes the input filename has only one .
elements = input_file.split('.')
output_file = elements[0] + '-filtered.' + elements[1]

filters = [line.rstrip('\n') for line in open(filters_file)]

print("apply-filters: Starting filtration")

# Read the CSV file as a pandas dataframe. Note that the CSV file should have valid
# identifiers in column names for the queries to work.
df = pd.read_csv(input_file)

print("Data size = %d" % (len(df.index)))

for query in filters:
    # Skip comments
    if query.startswith('#'):
        continue

    # Apply filter
    print("apply-filters: Applying %s" % (query))
    df.query(query, inplace=True)
    print("apply-filters: Data size = %d" % (len(df.index)))

df.to_csv(output_file, sep=',', encoding='utf-8')

print("apply-filters: Competed filtration")
