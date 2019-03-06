These scripts use Python to search for terms across multiple documentation repositories. (Repositories are assumed to use the metadata formats for docs.microsoft.com.)

To use this tool:

1. Make sure you have Python 3 installed. Download from [https://www.python.org/downloads](https://www.python.org/downloads).

2. Run `pip install -r requirements.txt` to install needed libraries. (If you want to use a virtual environment instead of your global environment, run `python -m venv .env` then `.env\scripts\activate` before running `pip install`.)

3. Modify `config.json` so that any `content/path` elements point to a local path on your machine. If you haven't cloned this repo locally because you don't want to search it, leave the `path` element out and the repo will automatically be skipped.

4. Modify `config.json`'s `inventory` section to either add or edit inventories. `name` is a case-insensitive name for the inventory, and `terms` is an array of Python regular expressions to use as search terms.

5. Run `python take-inventory.py` and output is generated in `results_<date>_<random_int>.csv` and `results_<date>_<random_int>-with-metadata.csv` files, the latter of which includes various metadata values extracted from the files in question (see extract-metadata.py, which is invoked at the end of take-inventory.py).
