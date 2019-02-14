These scripts use the Windows findstr command-line tool and some Python processing to search for terms across multiple documentation repositories. (Repositories are assumed to use the metadata formats for docs.microsoft.com.)

To use this tool:

1. Make sure you have Python 3 installed. Download from [https://www.python.org/downloads](https://www.python.org/downloads).

2. Run `pip install -r requirements.txt` to install needed libraries. (If you want to use a virtual environment instead of your global environment, run `python -m venv .env` then `.env\scripts\activate` before running `pip install`.)

3. Modify `folders.txt` to list the local folders you want to search. Each line contains a docset name, a space, then the local path. *.md is appended automatically.

4. Modify `terms.txt` to list the terms you want to search. Each line has an individual term and can include spaces and regular expressions (which are allowed by findstr).

5. Run "python take-inventory.py" and output is generated in `results_<date>_<random_int>.csv` and `results_<date>_<random_int>-with-metadata.csv` files, the latter of which includes various metadata values extracted from the files in question (see extract-metadata.py, which is invoked at the end of take-inventory.py).

Note that after a run, the `text_results` folder contains intermediate files from the findstr command line, which are of the form `<docset>-<search-term>.txt`. These can be deleted once you have the .csv files.
