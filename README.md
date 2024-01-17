
# Gofilepy - Unofficial Python wrapper for Gofile API

![PyPI Package](https://badge.fury.io/py/gofilepy-api.svg)
[![Downloads](https://static.pepy.tech/badge/gofilepy-api)](https://pepy.tech/project/gofilepy-api)
![PyPI - Wheel](https://img.shields.io/pypi/wheel/gofilepy-api)
![PyPI - Python Version](https://img.shields.io/pypi/pyversions/gofilepy-api)
![PyPI - License](https://img.shields.io/pypi/l/gofilepy-api)

A true wrapper for Gofile's REST API.
## Installation

Install Gofilepy with pip
```bash
  pip install gofilepy-api
```

## Documentation
- [gofilepy docs/reference](https://m0bb1n.github.io/gofilepy/)
- [Gofile REST API reference](https://gofile.io/api)


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
from gofilepy.exceptions import GofileAPIAuthenticationError

client = GofileClient(token="") #Get token from gofile.io.

print(client.account.email)
print(client.account.tier)

root_folder_id = client.account.root_id
root = client.get(root_folder_id)

child = client.create_folder("NEW_FOLDER", parent_id=root.content_id)
child.set_option("description", "New folder created with gofilepy") #More options available https://gofile.io/api


# Registering changes to local variable
child.content_id in root.children_ids # = false because it hasn't been updated
root.reload() #Gets any new changes/updates to the folder
child.content_id in root.children_ids # = true after root folder has been reloaded


# Copying content (files & folders)
child.copy_to(child.parent_id) #Duplicates folder in same directory

root.reload() #Now root.children_ids has another id

child.delete() #Deletes folder


```


## Links
 - [Gofilepy docs](https://m0bb1n.github.io/gofilepy/)
 - [Gofile REST API reference](https://gofile.io/api)
 - [Gofile Premium ](https://gofile.io/premium)
 - [Donate to Gofile](https://www.buymeacoffee.com/gofile)


