from gofile import GofileClient

"""

Try to get example to work
for some reason file is not showing infolder
"""



#file = client.upload('test.txt')

'''
#files parameter can also be array!

files = [open('..'), open('..')..]
client.upload(files=files)
'''

"""
folder = client.get("ea509747-52b5-4d57-92cb-64d25b37f9bf")
print("--------")
print(folder.is_public)
print(folder.name)

f = folder.children[1]#.children[0]#.refresh()#.children[0]
print("@@@@@@@@@@@@@@@@@")
print(f.content_id)
print(f.name)
print(f.is_public)
#f.set_option("password", "test")
new = client.create_folder("GOOO", f.content_id)
client.copy_content(new.content_id, "0ce78b4c-8e1e-471c-ab3f-9e93fd3e67e7", parent_id=f.content_id)
f.delete()
"""

client = GofileClient(token="1AlzPNJYROGKSzaB99UudQfRkH3q7VZI", verbose=True)
folder = client.get("a5642691-83fe-46c8-8c2a-be6c4669f179")
a = client.get_account()

client.copy_content(folder.content_id, folder.content_id, parent_id=a.root_id)
"""
a = client.get_account()
root = client.get(a.root_id)

child = client.create_folder("NEW_FOLDER", parent_id=root.content_id)
child.set_option("password", "test")
file = client.upload(file=open('test.txt', 'rb'), parent_id=child.content_id)
print(file.name)
print(file.content_id)
"""

#child.delete()


#client.delete(file.content_id, token=file.token)

#client.download_file(file, "out.txt")
#downloads the file
#print(client.get_file_download_url(resp['code']), throw_if_not_200=True)

#removes the file
#client.delete(resp['code'], resp['removalCode'])




