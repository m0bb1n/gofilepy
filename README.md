
# Gofilepy - Python wrapper for Gofile API


## Installation

Install Gofilepy with pip
```bash
  pip install gofilepy-api
```
    
## Usage/Examples

```python
from gofilepy import GofileClient

client = GofileClient(token="") #Get token from gofile.io.  Only premium accounts have access

#Free users can this function
file = client.upload(file=open("./test.txt", "rb"))

print(file.name)
print(file.page_link) #View and download file at this link

#BFunctions shown below are premium users only
account = client.get_account()

print(account.email)
print(account.tier)

root_folder_id = account.root_id
root = client.get(root_folder_id)

child = client.create_folder("NEW_FOLDER", parent_id=root.content_id)
child.set_option("password", "secret_password") #Set password to "secret_password".  More options available https://gofile.io/api


```


## Links

 - [Gofile REST API reference](https://gofile.io/api)
 - [Donate to Gofile](https://www.buymeacoffee.com/gofile)


