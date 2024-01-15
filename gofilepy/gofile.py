import requests
import os

class GofileAccount (object):
    def __init__(self, token):
        self.token = token
        self.email = None
        self.tier = None
        self.root_id = None
        self.folder_cnt = None
        self.file_cnt = None
        self.total_size = None
        self.total_download_cnt = None
        self._raw = {}

    def override_from_dict(self, data):
        self.token = data.get("token", self.token)
        self.email = data.get("email", self.email)
        self.tier = data.get("tier", self.tier)
        self.root_id = data.get("rootFolder", self.root_id)
        self.folder_cnt = data.get("foldersCount", self.folder_cnt)
        self.file_cnt = data.get("filesCount", self.file_cnt)
        self.total_size = data.get("totalSize", self.total_size)
        self.total_download_cnt = data.get("totalDownloadCount", self.total_download_cnt)

    @staticmethod
    def load_from_dict(data):
        account = GofileAccount(data["token"])
        account.override_from_dict(data)
        return account
    
    def reload(self):
        resp, data = self._client._get_account_raw_resp(token=self.token)
        self.override_from_dict(data)
        self._raw = data

class GofileContent (object):
    def __init__(self, content_id, parent_id, _type=None, client=None):
        self.content_id = content_id
        self.parent_id = parent_id
        self._type = _type
        self._client = client
        self._raw = {}

        self.is_file_type = _type == "file"
        self.is_folder_type = _type == "folder"
        self.is_unknown_type = _type == None
        self.is_deleted = False

    def delete (self):
        self._client.delete(self.content_id)
        self.is_deleted = True

    def copy (self, dest_id):
        pass

    def set_option(self, option, value, reload=True):
        self._client.set_content_option(self.content_id, option, value)
        if reload:
            self.reload() #reload to get up to date information
        #GofileClient.set_content_option(self.content_id, option, value)

    def reload (self):
        if self.is_folder_type or self.is_unknown_type:
            resp, data = self._client._get_content_raw_resp(self.content_id)
            if self.is_unknown_type:
                content = GofileContent.__init_from_resp__(resp, client=self._client)

            elif self.is_folder_type:
                self.override_from_dict(data)
                return self

            return content

        else:
            raise NotImplemented

    @staticmethod
    def __init_from_resp__ (resp, _type=None, client=None):
        if type(resp) == requests.models.Response:
            resp = resp.json()
            
        got = resp["data"] 
        _type = got.get("type", _type)
        content = None

        if _type == "file":
            content = GofileFile.load_from_dict(got, client=client)
        elif _type == "folder":
            content = GofileFolder.load_from_dict(got, client=client)
        else:
            raise NotImplemented

        return content


class GofileFile (GofileContent):
    def __init__(self, content_id, parent_id, client=None):
        super().__init__(content_id, parent_id, _type="file", client=client)
        self.name = None 
        self.time_created = None
        self.size = None
        self.download_cnt = None
        self.mimetype = None
        self.server = None
        self.direct_link = None
        self.page_link = None
        self.md5 = None

    def override_from_dict(self, data):
        self.content_id = data.get("id", self.content_id)
        self.parent_id = data.get("parentFolder", self.parent_id)
        self.name = data.get("name", self.name)
        self.time_created = data.get("createTime", self.time_created)
        self.size  = data.get("size", self.size)
        self.download_cnt = data.get("downloadCount", self.download_cnt)
        self.mimetype = data.get("mimetype", self.mimetype)
        self.md5 = data.get("md5", self.md5)
        self.server = data.get("serverChoosen", self.server)
        self.direct_link = data.get("link", self.direct_link)
        self.page_link = data.get("downloadPage", self.page_link) 

    @staticmethod
    def load_from_dict(data, client=None):
        file = GofileFile(data["id"], data["parentFolder"], client=client)
        file.override_from_dict(data)
        file._raw = data
        return file

    def download(self, save_path):
        if self.direct_link:
            resp = requests.get(self.direct_link)
            with open(save_path, 'wb') as f:
                for chunk in resp.iter_content(chunk_size=1024):
                    if chunk:
                        f.write(chunk)
        else:
            raise Exception("Direct link needed - only for premium users") 

class GofileFolder (GofileContent):
    def __init__(self, name, content_id, parent_id, client=None):
        super().__init__(content_id, parent_id, _type="folder", client=client)
        self.name = name
        self.children = []
        self.children_ids = []
        self.total_size = None
        self.total_download_cnt = None
        self.time_created = None
        self.is_public = None
        self.is_owner = None
        self.is_root = None
        self.has_password = None
        self.code = None

    def override_from_dict(self, data):
        self.content_id = data.get("id", self.content_id)
        self.parent_id = data.get("parentFolder", self.parent_id)
        self.name = data.get("name", self.name)
        self.time_created = data.get("createTime", self.time_created)
        self.is_public  = data.get("public", self.is_public)
        self.is_owner = data.get("isOwner", self.is_owner)
        self.is_root = data.get("isRoot", False)
        self.has_password = data.get("password", self.has_password)
        self.code = data.get("code", self.code)
        self.total_size = data.get("totalSize", self.total_size)
        self.total_download_cnt = data.get("totalDownloadCount", self.total_download_cnt)
        self.children_ids = data.get("childs")


    @staticmethod
    def load_from_dict(data, client=None):
        parent_id = data.get("parentFolder", None)
        folder = GofileFolder(data["name"], data["id"], parent_id, client=client)
        folder.override_from_dict(data)

        children = []
        contents = data.get("contents", {})

        if contents.keys():
            for content in contents.values():
                child = GofileContent.__init_from_resp__({"data": content}, client=client)
                children.append(child)

        elif folder.children_ids:
            for child_id in folder.children_ids:
                child = GofileContent(child_id, data["id"], client=client)
                children.append(child)

        folder.children = children
        folder._raw = data

        return folder


class GofileClient (object):
    server = None
    BASE_DOMAIN = 'gofile.io'
    API_SUBDOMAIN = 'api'
    BASE_API_URL = 'https://'+API_SUBDOMAIN+'.'+BASE_DOMAIN

    API_ROUTE_GET_SERVER_URL = BASE_API_URL + '/getServer'
    API_ROUTE_GET_ACCOUNT_URL = BASE_API_URL + "/getAccountDetails"
    API_ROUTE_GET_CONTENT_URL = BASE_API_URL + "/getContent"

    API_ROUTE_DELETE_CONTENT_URL = BASE_API_URL + "/deleteContent"
    API_ROUTE_COPY_CONTENT_URL = BASE_API_URL + "/copyContent"
    API_ROUTE_CREATE_FOLDER_URL = BASE_API_URL + "/createFolder"
    API_ROUTE_SET_OPTION_URL = BASE_API_URL +  "/setOption"

    API_ROUTE_DOWNLOAD_PATH = "download"
    API_ROUTE_UPLOAD_CONTENT_PATH = "uploadFile"

    API_STORE_FORMAT = "https://{}.{}/{}"

    def __init__(self, token=None, verbose=False):
        self.token = token
        self.server = GofileClient.get_best_server()
        self.verbose = verbose

    @staticmethod
    def handle_response(resp):
        code = resp.status_code
        data = resp.json()
        got = None
        api_status = ''

        if data:
            api_status = data.get('status')
            got = data.get('data')


        if api_status != 'ok':
            raise Exception('Gofile api error: {}'.format(api_status))

        if code != 200:
            raise Exception('GofileClient could not get data [{}]'.format(code))

        return got


    def get_best_upload_url(self):
        return self.API_STORE_FORMAT.format(self.server, self.BASE_DOMAIN, self.API_ROUTE_UPLOAD_CONTENT_PATH)


    @staticmethod
    def get_best_server(throw_if_not_200=False):
        resp = requests.get(GofileClient.API_ROUTE_GET_SERVER_URL)
        return GofileClient.handle_response(resp)['server']


    def download_file(self, file, save_path):
        raise NotImplemented

    def _get_token(self, token):
        if not token:
            token = self.token
            if not self.token:
                token = ""
        return token

    def upload(self, file=None, file_path=None, token=None, parent_id=None):
        if not file and not file_path:
            raise ValueError("GofileClient.upload() requires a file object or file path")

        upload_url = self.get_best_upload_url()
        token = self._get_token(token)

        if token:
            upload_url+= "?token={}".format(token)
            if parent_id:
                upload_url+= "&folderId={}".format(parent_id)

        files = {}

        if file:
            files["file"] = file
        elif file_path:
            files["file"] = open(file_path, "rb")

        resp = requests.post(upload_url, files=files)
        got = GofileClient.handle_response(resp)

        #Needed because json returned from API has different key values at this endpoint
        got["id"] = got.get("fileId", None)
        got["name"] = got.get("fileName", None)

        return  GofileFile.load_from_dict(got, client=self)
    

    def _get_content_raw_resp(self, content_id, token=None):
        token = self._get_token(token)
        req_url = self.API_ROUTE_GET_CONTENT_URL + "?contentId="+content_id

        if token:
            req_url += "&token="+token

        resp = requests.get(req_url)
        data = GofileClient.handle_response(resp)
        return resp, data


    def get(self, content_id, token=None):
        resp,data = self._get_content_raw_resp(content_id, token=token)
        return GofileContent.__init_from_resp__(resp, client=self)



    def delete(self, *content_ids, token=None):
        token = self._get_token(token)
        data = {"contentsId": ",".join(content_ids), "token": token}
        resp = requests.delete(GofileClient.API_ROUTE_DELETE_CONTENT_URL, data=data)
        got = GofileClient.handle_response(resp)


    def _get_account_raw_resp(self, token=None):
        token = self._get_token(token)
        url = GofileClient.API_ROUTE_GET_ACCOUNT_URL + "?token=" + token
        resp = requests.get(url)
        data = GofileClient.handle_response(resp)
        return resp, data


    def get_account(self, token=None):
        resp, data = self._get_account_raw_resp(token=token)
        account = GofileAccount.load_from_dict(data)
        account._client = self
        account._raw = data

        if account.token == self.token:
            self.account = account #update client's copy of account

        return account

    def set_content_option(self, content_id, option, value, token=None):
        token = self._get_token(token)

        if type(value) == bool: #api expects bools to be string
            if value:
                value = "true"
            else:
                value = "false"

        data = {
            "contentId": content_id,
            "token": token,
            "option": option,
            "value": value
        }

        resp = requests.put(GofileClient.API_ROUTE_SET_OPTION_URL, data=data)
        got = GofileClient.handle_response(resp)


    def copy_content(self, *content_ids, parent_id=None, token=None):
        if not parent_id:
            raise ValueError("Must pass a parent folder id: parent_id=None")

        token = self._get_token(token)
        data = {
            "contentsId": ",".join(content_ids),
            "folderIdDest": parent_id,
            "token": token
        }

        resp = requests.put(GofileClient.API_ROUTE_COPY_CONTENT_URL, data=data)
        got = GofileClient.handle_response(resp)

    def create_folder(self, name, parent_id, token=None):
        token = self._get_token(token)

        data = {
            "parentFolderId": parent_id,
            "folderName": name
        }

        data["token"] = token

        resp = requests.put(GofileClient.API_ROUTE_CREATE_FOLDER_URL, data=data)
        got = GofileClient.handle_response(resp)

        return GofileContent.__init_from_resp__(resp, client=self) 

