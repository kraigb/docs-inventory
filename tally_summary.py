import sys
import json

if __name__ == "__main__":
    file = sys.argv[1]

    if file is None:
        print("Usage: python tally_summary.py <json-file-path>")
        sys.exit(2)

    with open(file) as fp:
        data = json.load(fp)

        for item in data.keys():
            if item == "values":
                continue
            elif item == "mean":
                print(f'OVERALL MEAN: {"{0:.5g}".format(data[item])}')
            elif item == "stddev":
                print(f'OVERALL STDDEV: {"{0:.5g}".format(data[item])}')
            else:
                print(f'{item}: mean {"{0:.5g}".format(data[item]["mean"])}, stddev: {"{0:.5g}".format(data[item]["stddev"])}')
