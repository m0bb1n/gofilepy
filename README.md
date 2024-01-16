
# Gofilepy - Unofficial Python wrapper for Gofile API

A true wrapper for Gofile's REST API.
## Installation

Install Gofilepy with pip
```bash
  pip install gofilepy-api
```


## Usage/Examples (Free Users)

```python
from gofilepy import GofileClient

client = GofileClient()

#Free users can this function
file = client.upload(file=open("./test.txt", "rb"))

print(file.name)
print(file.page_link) #View and download file at this link

```


## Usage/Examples (Premium Users)

```python
from gofilepy import GofileClient

client = GofileClient(token="") #Get token from gofile.io.  Only premium accounts have access

account = client.get_account()

print(account.email)
print(account.tier)

root_folder_id = account.root_id
root = client.get(root_folder_id)

child = client.create_folder("NEW_FOLDER", parent_id=root.content_id)
child.set_option("description", "New folder created with gofilepy") #More options available https://gofile.io/api


# Registering changes to local variable
child.content_id in root.children_ids # = false because it hasn't been updated
root.reload() #Gets any new changes/updates to the folder
child.content_id in root.children_ids # = true after root folder has been reloaded


# Copying content (files & folders)
child.copy(root.content_id) #Duplicates folder in same directory

root.reload() #Now root.children_ids has another id

child.delete() #Deletes folder


```


## Links

 - [Gofile REST API reference](https://gofile.io/api)
 - [Gofile Premium ](https://gofile.io/premium)
 - [Donate to Gofile](https://www.buymeacoffee.com/gofile)


