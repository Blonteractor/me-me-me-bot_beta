import os
from typing import List
from colorama import init, Fore, Back

setup_dir = os.getcwd()[:-12]

ignored = [r"C:\\Users\\Administrator\\Desktop\MeMeMe_Code\\me-me-me-bot\\Database", r"C:\\Users\\Administrator\\Desktop\\MeMeMe_Code\\me-me-me-bot\\cache.nhentai.net"]

def get_packages(files: list) -> list:
    packages = []
    lines = []

    for file in files:
        with open(file, errors="ignore", encoding="utf8") as f:
            lines.append(f.read().split("\n"))

    for file in lines:
        for line in file:

            if line.startswith("import "):
                package_import_line = line[7:]

                if not package_import_line.split(" as ")[0] == package_import_line:
                    packages.append(package_import_line.split(" as ")[0])

                else:
                    for package in package_import_line.split(","):
                        packages.append(package.strip())

            elif line.startswith("from "):
                package_import_line = line[5:]

                packages.append(package_import_line.split("import ")[0])

    for index, package in enumerate(packages):
        if package.endswith(" "):
            packages[index] = package[:-1]
            

    packages_filtered: List[str]= []

    for package in packages:
        if package not in packages_filtered:
            packages_filtered.append(package)

    for package in packages_filtered:
        if package in get_filenames(files=files):
            packages_filtered.remove(package)

    with open("packages.txt", 'w') as f:
        f.write("\n".join(packages_filtered))

    return packages_filtered

def get_files(DIR: str, files: list) -> list:

    for file in os.listdir(DIR):
        is_folder = file.split(".")[0] == file 
        is_cache = file.startswith("__") and file.endswith("__")

        if file.endswith(".py"):
            files.append(DIR + "\\" + file)

        elif is_folder and not is_cache:
            if file not in ignored:
                get_files(DIR + "\\" + file, files)

    return files

def get_filenames(files: list) -> list:
    filenames: List[str] = []

    for file in files:
        filenames.append(os.path.basename(file)[:-3])

    return filenames

def install_packages(file):
    packages = []

    with open("packages.txt") as f:
        for package in f.read().split("\n"):
            packages.append(package)

    for package in packages:
        os.system(f"pip install {package}")

files = get_files(setup_dir, [])

packages = get_packages(files)

print("Please reveiw the contents of packages.txt")
os.startfile("packages.txt")

valid_response = False
responses = {"no": False, "yes": True, "yea": True, "perhaps": True, "nop": False, "nope": False}

while not valid_response:
    response = input("Install packages from packages.txt?: ")

    if response in responses:
        response_bool = responses[response]
        valid_response = True
    else:
        print("Invalid response")
        valid_response = False

init(convert=True)

if response_bool:
    install_packages(os.getcwd() + "\\" + "packages.txt")

    print(Fore.BLACK + Back.GREEN + "DONE, packages installed.")
else:
    init(convert=True)
    print(Fore.BLACK + Back.CYAN + "DONE, packages not installed.")

print(Fore.WHITE+Back.BLACK)