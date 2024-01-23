import pytest
from gofilepy import GofileClient

#integration testing for free features

FILE_PATH = __file__ #uploads script file for test 
STANDARD_TOKEN = "" #get token in dashboard at gofile.io/myProfile

guest_client = GofileClient()
standard_client = GofileClient(token=STANDARD_TOKEN, get_account=False) #get free token from dashboard

def assert_GofileFile(f):
    assert type(f.parent_id) == str
    assert type(f.page_link) == str
    assert type(f.name) == str
    assert type(f.md5) == str
    f.delete()
    assert f.is_deleted == True

def test_file_upload_standard():
   f = standard_client.upload(FILE_PATH, parent_id=standard_client.account.root_id)
   assert_GofileFile(f)

def test_file_upload_guest():
    f = guest_client.upload(FILE_PATH)
    assert_GofileFile(f)

def test_account_get():
    account = standard_client.get_account()

    assert account.tier == "standard"
    assert type(account.total_size) == int
    assert type(account.root_id) == str
    assert type(account.email) == str
    assert type(account.token) == str
    return account

def test_folder_create():
    name = "test_folder"
    folder = standard_client.create_folder(name, standard_client.account.root_id)

    assert folder.name == name
    assert folder.parent_id == standard_client.account.root_id
    return folder


def test_content_delete(c):
    assert c.is_deleted == False
    c.delete()
    assert c.is_deleted == True

if __name__ == "__main__":
    test_file_upload_guest()

    test_account_get()
    test_file_upload_standard()
    folder = test_folder_create()

    test_content_delete(folder)
