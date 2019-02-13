To use this tool

1. Make sure you have Python 3 installed. Download from https://www.python.org/downloads.

2. Modify folders.txt to list the local folders you want to search. Each line contains a docset name, a space, then the local path. *.md is appended automatically.

3. Modify terms.txt to list the terms you want to search. Each line has an individual term and can include spaces.

4. Run "python take-inventory.py" and output is in a results_<date>_<random_int>.csv file.

After a run, the text_results folder contains intermediate files from the findstr command line, which are of the form <docset>-<search-term>.txt. These can be deleted once you have the .csv file.

Questions or comments to kraigb.
