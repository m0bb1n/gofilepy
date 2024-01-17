import requests
import os
from io import BufferedReader
from .exceptions import GofileAPIException


GofileFile = None
GofileFolder = None

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

    def __init__(self, token: str = None, get_account: bool = True, verbose: bool = False):
        self.token = token
        self.server = GofileClient.get_best_server()
        self.verbose = verbose

        if get_account and token:
            self.get_account()

    @staticmethod
    def handle_response(resp: requests.Response):
        code = resp.status_code
        data = resp.json()
        got = None
        api_status = ''

        if data:
            api_status = data.get('status')
            got = data.get('data')


        if api_status != 'ok' or code != 200:
            raise GofileAPIException.__init_from_resp__(resp)
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

    def upload(self, file: BufferedReader=None, path: str=None, parent_id: str=None, token: str=None) -> GofileFile:
        if not file and not path:
            raise ValueError("GofileClient.upload() requires a BufferedReader or file path")

        upload_url = self.get_best_upload_url()
        token = self._get_token(token)

        data = {}
        if parent_id:
            data["folderId"] = parent_id
        if token:
            data["token"] = token

        files = {}
        if file:
            files["file"] = file
        elif path:
            files["file"] = open(path, "rb")

        resp = requests.post(upload_url, files=files, data=data)
        got = GofileClient.handle_response(resp)

        #Needed because json returned from API has different key values at this endpoint
        got["id"] = got.get("fileId", None)
        got["name"] = got.get("fileName", None)

        return  GofileFile.load_from_dict(got, client=self)
    

    def _get_content_raw_resp(self, content_id: str, token: str = None):
        token = self._get_token(token)
        req_url = self.API_ROUTE_GET_CONTENT_URL + "?contentId="+content_id

        if token:
            req_url += "&token="+token

        resp = requests.get(req_url)
        data = GofileClient.handle_response(resp)
        return resp, data


    def get(self, content_id: str, token: str = None):
        resp,data = self._get_content_raw_resp(content_id, token=token)
        return GofileContent.__init_from_resp__(resp, client=self)

    def get_folder(self, *args, **kwargs):
        return self.get(*args, **kwargs)

    def delete(self, *content_ids: str, token: str = None):
        token = self._get_token(token)
        data = {"contentsId": ",".join(content_ids), "token": token}
        resp = requests.delete(GofileClient.API_ROUTE_DELETE_CONTENT_URL, data=data)
        got = GofileClient.handle_response(resp)


    def _get_account_raw_resp(self, token: str = None):
        token = self._get_token(token)
        url = GofileClient.API_ROUTE_GET_ACCOUNT_URL + "?token=" + token
        resp = requests.get(url)
        data = GofileClient.handle_response(resp)
        return resp, data


    def get_account(self, token: str = None):
        resp, data = self._get_account_raw_resp(token=token)
        account = GofileAccount.load_from_dict(data)
        account._client = self
        account._raw = data

        if account.token == self.token:
            self.account = account #update client's copy of account

        return account

    def set_content_option(self, content_id: str, option: str, value, token: str = None):
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


    def copy_content(self, *content_ids: str, parent_id: str = None, token: str = None):
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
        
        """
        As of right now /copyContent does not return information about newly created content
        For this reason copy_content will just return None

        return GofileContent.__init_from_resp__(resp, client=self)
        """

    def create_folder(self, name: str, parent_id: str, token: str = None):
        token = self._get_token(token)

        data = {
            "parentFolderId": parent_id,
            "folderName": name
        }

        data["token"] = token

        resp = requests.put(GofileClient.API_ROUTE_CREATE_FOLDER_URL, data=data)
        got = GofileClient.handle_response(resp)

        return GofileContent.__init_from_resp__(resp, client=self) 

class GofileAccount (object):
    def __init__(self, token: str = None):
        self.token = token
        self.email = None
        self.tier = None
        self.root_id = None
        self.folder_cnt = None
        self.file_cnt = None
        self.total_size = None
        self.total_download_cnt = None
        self._raw = {}

    def override_from_dict(self, data: dict) -> None:
        self.token = data.get("token", self.token)
        self.email = data.get("email", self.email)
        self.tier = data.get("tier", self.tier)
        self.root_id = data.get("rootFolder", self.root_id)
        self.folder_cnt = data.get("foldersCount", self.folder_cnt)
        self.file_cnt = data.get("filesCount", self.file_cnt)
        self.total_size = data.get("totalSize", self.total_size)
        self.total_download_cnt = data.get("totalDownloadCount", self.total_download_cnt)

        self._raw = data

    @staticmethod
    def load_from_dict(data: dict):
        account = GofileAccount(data["token"])
        account.override_from_dict(data)
        return account
    
    def reload(self):
        resp, data = self._client._get_account_raw_resp(token=self.token)
        self.override_from_dict(data)
        self._raw = data

class GofileContent (object):
    def __init__(self, content_id: str, parent_id: str, _type: str = None, client: GofileClient = None):
        self.content_id = content_id
        self.parent_id = parent_id
        self._type = _type
        self._client = client
        self._raw = {}

        self.is_file_type = _type == "file"
        self.is_folder_type = _type == "folder"
        self.is_unknown_type = _type == None
        self.name = None
        self.is_deleted = False

    def __repr__ (self) -> str:
        _type = self._type
        if not _type:
            _type = "Unknown"

        return "<Gofile {}: content_id={} name={}>".format(_type.upper(), self.content_id, self.name)

    def delete (self) -> None:
        self._client.delete(self.content_id)
        self.is_deleted = True

    def copy_to (self, dest_id: str) -> None:
        self._client.copy_content(self.content_id, parent_id=dest_id)

    def copy (self, dest_id: str) -> None:
        self.copy_to(dest_id)

    def set_option(self, option: str, value, reload: bool = True) -> None:
        self._client.set_content_option(self.content_id, option, value)
        if reload:
            self.reload() #reload to get up to date information

    def reload (self):
        if self.is_folder_type or (self.is_unknown_type and self.parent_id == None):
            resp, data = self._client._get_content_raw_resp(self.content_id)

            if self.is_unknown_type:
                content = GofileContent.__init_from_resp__(resp, client=self._client)

            elif self.is_folder_type:
                self.override_from_dict(data)
                return self
        
        elif (self.is_unknown_type or self.is_file_type) and self.parent_id:
            resp, data = self._client._get_content_raw_resp(self.parent_id)
            content_data = data["contents"].get(self.content_id, None)
            content = None
            if content_data:
                content = GofileContent.__init_from_resp__({"data": content_data}, client=self._client)

                if self.is_file_type:
                    self.override_from_dict(content_data)

            return content

        else:
            raise NotImplemented

    @staticmethod
    def __init_from_resp__ (resp: requests.Response, _type: str = None, client: GofileClient = None):
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
    def __init__(self, content_id: str, parent_id: str, client: GofileClient = None):
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

    def override_from_dict(self, data: dict) -> None:
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

        self._raw = data

    @staticmethod
    def load_from_dict(data: dict, client: GofileClient = None):
        file = GofileFile(data["id"], data["parentFolder"], client=client)
        file.override_from_dict(data)
        file._raw = data
        return file

    def download(self, save_path: str):
        if self.direct_link:
            resp = requests.get(self.direct_link)
            with open(save_path, 'wb') as f:
                for chunk in resp.iter_content(chunk_size=1024):
                    if chunk:
                        f.write(chunk)
        else:
            raise Exception("Direct link needed - only for premium users") 

class GofileFolder (GofileContent):
    def __init__(self, name: str, content_id: str, parent_id: str, client: GofileClient = None):
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

    def __init_children_from_contents__(self, data: dict) -> None:
        children = []

        self.children_ids = data.get("childs")
        contents = data.get("contents", {})

        if contents.keys():
            for content in contents.values():
                child = GofileContent.__init_from_resp__({"data": content}, client=self._client)
                children.append(child)

        elif self.children_ids:
            for child_id in self.children_ids:
                child = GofileContent(child_id, parent_id=data["id"], client=self._client)
                children.append(child)
        return children


    def override_from_dict(self, data: dict) -> None:
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

        self.children = self.__init_children_from_contents__(data)

        self._raw = data


    @staticmethod
    def load_from_dict(data: dict, client: GofileClient = None) -> GofileFolder:
        parent_id = data.get("parentFolder", None)
        folder = GofileFolder(data["name"], data["id"], parent_id, client=client)
        folder.override_from_dict(data)
        folder._raw = data

        return folder

    def upload(self, file: BufferedReader = None, path: str = None) -> GofileFile:
        return self._client.upload(file=file, path=path, parent_id=self.content_id)

