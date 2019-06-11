def detect_issues(content, path):
    line_num = 0

    for line in iter(content.splitlines(1)):  # The 1 arg means include \n
        line_num += 1

        if line_num == 1:
            # First line of file
            if line.startswith("ï»¿---"):
                print("take_inventory: WARNING: File is not utf-8 encoded. {}".format(path))
            else:
                if not line.startswith("---"):
                    print("take_inventory: WARNING: Metadata does not start on first line. {}".format(path))

                    