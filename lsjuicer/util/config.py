import os
import appdirs

APPNAME = "Juicer"
AUTHOR = "ardoi"
user_dir = appdirs.user_data_dir(APPNAME, AUTHOR)
db_file = os.path.join(user_dir, 'tables.db')
folders = {'user_folder': user_dir,
           'ome_folder': os.path.join(user_dir, 'converted'),
           'log_folder': os.path.join(user_dir, 'log')}

def create_folder(folder_name):
    folder_name = folders[folder_name]
    if not os.path.isdir(folder_name):
        os.makedirs(folder_name)

def create_folders():
    create_folder("user_folder")
    create_folder("ome_folder")
    create_folder("log_folder")

create_folders()
