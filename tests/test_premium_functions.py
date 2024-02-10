import pytest
import os
from time import sleep, time
from gofilepy import GofileClient
from gofilepy.options import FolderOption, FileOption

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

def test_content_delete(c):
    assert c.is_deleted == False
    c.delete()
    assert c.is_deleted == True

def test_content_copy(c):
    #copyContent api doesn't return any data so assertion reload parent folder to see an increase in children
    folder = client.get(c.parent_id)
    num_of_children = len(folder.children)

    c.copy_to(c.parent_id)
    sleep(9) #copyContent endpoint seems to take the longest to register changes
    folder.reload()

    assert len(folder.children) == num_of_children + 1

def test_file_set_options(f):
    f.set_option(FileOption.HAS_DIRECT_LINK, True)
    sleep(5)
    f.reload()

    assert type(f.direct_link) == str

def test_folder_set_options(folder):
    desc = "A short description"
    tags = ["test","gofilepy"]
    folder.set_option(FolderOption.IS_PUBLIC, False)
    folder.set_option(FolderOption.PASSWORD, "secret")
    folder.set_option(FolderOption.DESCRIPTION, desc)
    folder.set_option(FolderOption.TAGS, tags)
    folder.set_option(FolderOption.EXPIRE, time()+120) #Expires in 2 mins
    sleep(5)

    folder.reload()

    assert folder.has_password == True
    assert folder.is_public == False
    assert folder.description == desc 
    assert folder.tags == tags

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

def test_folder_create(parent_id=None):
    if not parent_id:
        parent_id = client.account.root_id
    name = "test_folder"
    folder = client.create_folder(name, parent_id)

    assert folder.name == name
    assert folder.parent_id == parent_id 
    return folder


def test_recursive_folder_reload():
    f1 = test_folder_create()
    f2 = test_folder_create(parent_id=f1.content_id)
    f3 = test_folder_create(parent_id=f2.content_id)
    fi = test_file_upload(f3.content_id)

    sleep(5)
    a = client.get_folder(f1.content_id)

    assert a.content_id == a.children[0].parent_id
    assert a.children[0].is_folder_type

    assert a.children[0].children[0].is_unknown_type
    a.children[0].children[0].reload()

    assert a.children[0].children[0].is_folder_type

    if a.children[0].children[0].children[0].is_unknown_type:
        a.children[0].children[0].children[0].reload()

    assert a.children[0].children[0].children[0].is_file_type

    test_content_delete(f1)

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

    test_recursive_folder_reload()

