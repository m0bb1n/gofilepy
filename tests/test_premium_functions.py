import pytest
import os
from time import sleep, time
from gofilepy import GofileClient

#integration testing for premium features

FILE_PATH = __file__ #uploads script file for test 
PREMIUM_TOKEN = "" #get token in dashboard at gofile.io/myProfile (paid user)

client = GofileClient(token=PREMIUM_TOKEN, get_account=False)

def test_file_upload(parent_id):
    f = client.upload(FILE_PATH, parent_id=parent_id)
    assert type(f.parent_id) == str
    assert type(f.page_link) == str
    assert type(f.name) == str
    assert type(f.md5) == str
    return f


def test_account_get():
    account = client.get_account()

    assert account.tier == "premium"
    assert type(account.total_size) == int
    assert type(account.root_id) == str
    assert type(account.email) == str
    assert type(account.token) == str

def test_content_copy(c):
    #copyContent api doesn't return any data so assertion reload parent folder to see an increase in children
    folder = client.get(c.parent_id)
    num_of_children = len(folder.children)

    c.copy_to(c.parent_id)
    sleep(9) #copyContent endpoint seems to take the longest to register changes
    folder.reload()

    assert len(folder.children) == num_of_children + 1

def test_file_set_options(f):
    f.set_option("directLink", True)
    sleep(5)
    f.reload()

    assert type(f.direct_link) == str

def test_folder_set_options(folder):
    desc = "A short description"
    folder.set_option("public", False)
    folder.set_option("password", "secret")
    folder.set_option("description", desc)
    folder.set_option("tags", ["test","gofilepy"])
    folder.set_option("expire", int(time()+120)) #Expires in 2 mins
    sleep(5)

    folder.reload()

    assert folder.has_password == True
    assert folder.is_public == False
    assert folder.description == desc 

def test_file_download(f):
    path =  f.download()
    data_download = None
    data_local = None

    with open(FILE_PATH, "rb") as f_local:
        data_local = f_local.read()
    with open(path, "rb") as f_download:
        data_download = f_download.read()

    assert data_local == data_download
    os.remove(path) #remove downloaded test file

def test_folder_create():
    name = "test_folder"
    folder = client.create_folder(name, client.account.root_id)

    assert folder.name == name
    assert folder.parent_id == client.account.root_id
    return folder


if __name__ == "__main__":
    test_account_get()

    folder = test_folder_create()
    test_folder_set_options(folder)

    f = test_file_upload(folder.content_id)
    test_file_set_options(f)
    test_content_copy(f)
    test_file_download(f)

    test_content_delete(f)
    test_content_delete(folder)

