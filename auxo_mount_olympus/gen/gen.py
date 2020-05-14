import os 
import pathlib
import datetime

CWD = pathlib.Path.cwd() 

def generate(directory, service_name, author, description, last_modified=None, verbose=True):
    parse_folder_name = service_name.split(" ") 
    folder_name = 'serviceExe'
    for word in parse_folder_name: 
        folder_name += word.capitalize()
    # mkdir top dir 
    top_dir = CWD.joinpath(directory, folder_name)

    try: 
        top_dir.mkdir(exist_ok=False) 
    except FileExistsError as e: 
        # Folder already exists -- dele
        print(f"gen.py {e}: {folder_name} already exists, delete it then regenerate")
        return 

    # Create the empty folder_name/__init__.py, folder_name/folder_name.py, folder_name/folder_name.txt
    py_file = top_dir.joinpath(f'{folder_name}.py')
    txt_file = top_dir.joinpath(f'{folder_name}.txt')
    init_file = top_dir.joinpath('__init__.py')
    py_file.touch()
    txt_file.touch()
    init_file.touch()

    # write to the files 
    service_name = " ".join(word.capitalize() for word in parse_folder_name)
    txt_file.write_text(populate_txt_file(service_name, author, description, last_modified))
    # py_file.write_text("hey")
    print(f"Successful created {folder_name}!")


def populate_txt_file(service_name, author, description, last_modified):
    if last_modified is None: 
        now = datetime.datetime.now() 
        last_modified = now.strftime("%m-%d %H:%M:%S")

    out = f"Name: {service_name}\nAuthor: {author}\nLast Modified: {last_modified}\nDescription: {description}"
    return out 

def populate_py_file(service_name, author, description):
    # TODO: Finish creating this. Use Jinja? 
    pass 


if __name__ == "__main__":
    service_name = "hello world"
    directory = pathlib.Path("../../auxo_olympus/lib/services")
    author = "Bella"
    last_modified = "NA"
    description = "NA"

    generate(directory, service_name, author, last_modified, description)