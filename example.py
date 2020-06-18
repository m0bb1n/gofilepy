from gofile import GofileClient


client = GofileClient(email='YOUR EMAIL', verbose=True)
resp = client.upload(files=open('test.txt', 'rb'), tags=['test', '123'], desc='Interesting test')

'''
#files parameter can also be array!

files = [open('..'), open('..')..]
client.upload(files=files)
'''

#downloads the file
print(client.get_file_download_url(resp['code']))

#removes the file
client.delete(resp['code'], resp['removalCode'])



