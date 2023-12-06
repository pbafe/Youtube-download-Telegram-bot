from mega import Mega
from configparser import ConfigParser
import time

# requirements
# pip install mega.py

# Mega credentials specified in config.ini file
# create a folder in mega to be used for the storage and get its ID

def upload(file_path):
    config = ConfigParser()
    config.read("config.ini")
    mega_username = config.get("Mega", "username")
    mega_pwd = config.get("Mega", "pwd")
    mega_folder = 'XXXXXX'

    mega = Mega()

    m = mega.login(mega_username, mega_pwd) 

    files = m.get_files_in_node(mega_folder) # Hardcoded value for downloads folder to avoid targetting other folders with same name

    # Delete files that are older than 15 minutes
    for file in files:
        if (int(time.time()) - int(files[file]['ts'])) > 900: #900 sec == 15 min
            m.delete(file)
            print("Old, deleted: ", file)
        #else:
        #    print("New: ", file)

    # Upload a file to the "downloads" folder
    file = m.upload(file_path, mega_folder)
    # Get the public link for the uploaded file
    link = m.get_upload_link(file)

    # EMPTY BIN
    m.empty_trash()
    
    return link
