import os

setup_dir = os.getcwd()[:-12]

ignore = ["environment"]

def get_files(DIR: str, files: list) -> list:

    for i in ignore:
        if DIR.endswith(f"\\{i}\\"):
            return files

    for file in os.listdir(DIR):
        is_folder = file.split(".")[0] == file 
        is_cache = file.startswith("__") and file.endswith("__")

        if file.endswith(".py"):
            files.append(DIR + "\\" + file)

        elif is_folder and not is_cache:
                get_files(DIR + "\\" + file, files)

    for file in files:
        for ignored in ignore:
            if f"\\{ignored}\\" in file:
                files.remove(file)

    return files

for i in get_files(setup_dir, []):
    print(i)