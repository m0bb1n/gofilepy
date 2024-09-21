import requests
import os
from io import BufferedReader
from .exceptions import GofileAPIException
from .options import FileOption, FolderOption, ContentOption


GofileFile = None
GofileFolder = None
GofileAccount = None

class GofileClient (object):
    server = None
    _BASE_DOMAIN = 'gofile.io'
    _API_SUBDOMAIN = 'api'
    _BASE_API_URL = 'https://'+_API_SUBDOMAIN+'.'+_BASE_DOMAIN

    _API_ROUTE_GET_SERVER_URL = _BASE_API_URL + '/servers'

    _API_ROUTE_GET_ACCOUNT_URL = _BASE_API_URL + "/accounts/{}"
    _API_ROUTE_GET_ACCOUNT_ID_URL = _BASE_API_URL + "/accounts/getid"

    _API_ROUTE_GET_CONTENT_URL = _BASE_API_URL + "/contents/{}"
    _API_ROUTE_DELETE_CONTENT_URL = _BASE_API_URL + "/contents"
    _API_ROUTE_COPY_CONTENT_URL = _BASE_API_URL + "/contents/copy"

    _API_ROUTE_CREATE_FOLDER_URL = _BASE_API_URL + "/contents/createFolder"
    _API_ROUTE_SET_OPTION_URL = _BASE_API_URL +  "/contents/{}/update"

    _API_ROUTE_CREATE_FILE_DIRECT_LINK_URL = _BASE_API_URL + "/contents/{}/directlinks"

    _API_ROUTE_DOWNLOAD_PATH = "download"
    _API_ROUTE_UPLOAD_CONTENT_PATH = "uploadFile"

    _API_STORE_FORMAT = "https://{}.{}/{}"

    def __init__(self, zone: str = "na", token: str = None, get_account: bool = True, verbose: bool = False):
        self.token = token
        if token:
            self.headers = GofileClient.create_authorization_header(token)

        self._servers = GofileClient.get_best_server()
        self.server = GofileClient.get_preferred_server(zone, self._servers) 
        self.verbose = verbose

        if get_account and token:
            self.get_account()

    @staticmethod
    def create_authorization_header(token):
        return {"Authorization": f"Bearer {token}"}

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
        return self._API_STORE_FORMAT.format(self.server, self._BASE_DOMAIN, self._API_ROUTE_UPLOAD_CONTENT_PATH)



    @staticmethod
    def get_best_server(throw_if_not_200=False):
        resp = requests.get(GofileClient._API_ROUTE_GET_SERVER_URL)
        return GofileClient.handle_response(resp)['servers']
    
    @staticmethod
    def get_preferred_server(zone: str, servers: list, strict: bool = False):
        for sv in servers:
            if sv["zone"] == zone:
                return sv["name"]

        if not strict:
            return servers[0]["name"]



    def create_file_direct_link(self, content_id, token=None, expire=None, ips_allowed=[], domains_allowed=[], username=None, password=None, file=None):
        token = self._get_token(token)
        headers = self.create_authorization_header(token)

        data = {}
        if expire:
            data["expireTime"] = expire
        if ips_allowed:
            data["sourceIpsAllowed"] = ips_allowed
        if domains_allowed:
            data["domainsAllowed"] = domains_allowed
        if username or password:
            if not (username and password):
                raise ValueError("username AND password both needed create direct link creation")
            data["auth"] = [username, password]

        resp = requests.post(
                GofileClient._API_ROUTE_CREATE_FILE_DIRECT_LINK_URL.format(content_id),
                data=data,
                headers=headers
                )

        return GofileFileDirectLink._load_from_dict(GofileClient.handle_response(resp), file=file)

    def _download_file_from_direct_link(self, direct_link, out_dir="./"):
        fn = direct_link.rsplit('/', 1)[1]
        resp = requests.get(direct_link, stream=True, allow_redirects=None)
        if resp.status_code != 200:
            raise GofileAPIException("Could not download file", code=resp.status_code)

        out_path = os.path.join(out_dir, fn)
        with open(out_path, 'wb') as f:
            for chunk in resp.iter_content(chunk_size=1024):
                if chunk:
                    f.write(chunk)
        return out_path


    def _get_token(self, token):
        if not token:
            token = self.token
            if not self.token:
                token = ""
        return token

    def upload(self, path: str=None, file: BufferedReader=None, parent_id: str=None, token: str=None) -> GofileFile:
        if not file and not path:
            raise ValueError("GofileClient.upload() requires a BufferedReader or file path")

        upload_url = self.get_best_upload_url()
        token = self._get_token(token)
        headers = {}
        if token:
            headers = self.create_authorization_header(token)

        data = {}
        if parent_id:
            data["folderId"] = parent_id

        files = {}
        if file:
            files["file"] = file
        elif path:
            files["file"] = open(path, "rb")

        resp = requests.post(upload_url, files=files, data=data, headers=headers)
        got = GofileClient.handle_response(resp)

        #Needed because json returned from API has different key values at this endpoint
        got["id"] = got.get("id", None)
        got["name"] = got.get("name", None)

        return  GofileFile._load_from_dict(got, client=self)
    

    def _get_content_raw_resp(self, content_id: str, token: str = None):
        token = self._get_token(token)
        headers = GofileClient.create_authorization_header(token)

        resp = requests.get(self._API_ROUTE_GET_CONTENT_URL.format(content_id), headers=headers)
        data = GofileClient.handle_response(resp)
        return resp, data


    def get(self, content_id: str, token: str = None):
        resp,data = self._get_content_raw_resp(content_id, token=token)
        return GofileContent.__init_from_resp__(resp, client=self)

    def get_folder(self, *args, **kwargs):
        """Retrieves folder using content_id"""
        return self.get(*args, **kwargs)

    def delete(self, *content_ids: str, token: str = None):
        """Calls Gofile API to delete provided content_ids."""
        token = self._get_token(token)
        headers = GofileClient.create_authorization_header(token)
        data = {"contentsId": ",".join(content_ids), "token": token}
        resp = requests.delete(GofileClient._API_ROUTE_DELETE_CONTENT_URL, data=data, headers=headers)
        got = GofileClient.handle_response(resp)

    def _get_account_raw_resp(self, token: str = None):
        token = self._get_token(token)
        headers = GofileClient.create_authorization_header(token) 
        resp = requests.get(GofileClient._API_ROUTE_GET_ACCOUNT_ID_URL, headers=headers)
        data = GofileClient.handle_response(resp)
        return resp, data


    def get_account_id(self):
        """GET ACCOUNT STUFF HERE.  TO GET ACCOUNT INFO U HAVE TO GET ACCOUNT_ID FIRST"""
        pass

    def get_account(self, token: str = None) -> GofileAccount:
        """If token is provided returns specified account, otherwise token defaults to self.token.
          \If token is default self.account is updated"""
        token = self._get_token(token)
        resp, data = self._get_account_raw_resp(token=token)
        account = GofileAccount._load_from_account_id(data["id"], token)
        account._client = self
        account._raw = data

        if account.token == self.token:
            self.account = account #update client's copy of account

        return account

    def set_content_option(self, content_id: str, option: str, value, token: str = None):
        """Sets content option like 'description', 'public', etc (more at gofile.io/api).  Note that folder and file content have different options"""
        token = self._get_token(token)
        headers = self.create_authorization_header(token)

        value = ContentOption._process_option_value(option, value) #checks file types and formats for api

        data = {
            "attribute": option,
            "attributeValue": value
        }

        resp = requests.put(GofileClient._API_ROUTE_SET_OPTION_URL.format(content_id), data=data, headers=headers)
        got = GofileClient.handle_response(resp)


    def copy_content(self, *content_ids: str, parent_id: str = None, token: str = None):
        """Copy provided content_ids to destination folder's content_id.  Currently returns None because api doesn't return any information.  Will have to query parent folder"""
        if not parent_id:
            raise ValueError("Must pass a parent folder id: parent_id=None")

        token = self._get_token(token)
        headers = self.create_authorization_header(token)
        data = {
            "contentsId": ",".join(content_ids),
            "folderId": parent_id,
            "token": token
        }

        resp = requests.post(GofileClient._API_ROUTE_COPY_CONTENT_URL, data=data, headers=headers)
        got = GofileClient.handle_response(resp)
        
        """
        As of right now /copyContent does not return information about newly created content
        For this reason copy_content will just return None

        return GofileContent.__init_from_resp__(resp, client=self)
        """

    def create_folder(self, name: str, parent_id: str, token: str = None):
        """Creates folder in specified parent folder's content_id"""
        token = self._get_token(token)
        headers = self.create_authorization_header(token)

        data = {
            "parentFolderId": parent_id,
            "folderName": name
        }

        resp = requests.post(GofileClient._API_ROUTE_CREATE_FOLDER_URL, data=data, headers=headers)
        got = GofileClient.handle_response(resp)

        return GofileContent.__init_from_resp__(resp, client=self) 

class GofileAccount (object):
    token: str
    """Token of account, found on Gofile.io"""
    email: str
    """Email address of account"""
    tier: str
    """Tier of GofileAccount either Standard or Premium"""
    root_id: str
    """Root folder's content_id of Gofile account"""
    folder_cnt: int
    """Number of children folders"""
    file_cnt: int
    """Number of children files"""
    total_size: int
    """Total size of Accounts' contents"""
    total_download_cnt: int
    """Total download count of Accounts' contents"""

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

    def _override_from_dict(self, data: dict) -> None:
        self.token = data.get("token", self.token)
        self.email = data.get("email", self.email)
        self.tier = data.get("tier", self.tier)
        self.root_id = data.get("rootFolder", self.root_id)
        self.folder_cnt = data.get("statsCurrent", {}).get("foldersCount", self.folder_cnt)
        self.file_cnt = data.get("statsCurrent", {}).get("filesCount", self.file_cnt)
        self.total_size = data.get('statsCurrent', {}).get("storage", self.total_size)
        self.total_download_cnt = data.get('statsCurrent', {}).get("trafficWebDownloaded", self.total_download_cnt)

        self._raw = data

    @staticmethod
    def _load_from_account_id(account_id: str, token: str):
        headers = GofileClient.create_authorization_header(token) 
        resp = requests.get(
            GofileClient._API_ROUTE_GET_ACCOUNT_URL.format(account_id),
            headers=headers
        )
        data = GofileClient.handle_response(resp)
        return GofileAccount._load_from_dict(data)


    @staticmethod
    def _load_from_dict(data: dict):
        account = GofileAccount(data["token"])
        account._override_from_dict(data)
        return account
    
    def reload(self):
        resp, data = self._client._get_account_raw_resp(token=self.token)
        self._override_from_dict(data)
        self._raw = data

class GofileContent (object):
    name: str
    """Name of content"""
    content_id: str
    """Gofile API's unique content id"""
    parent_id: str
    """Content_id of parent folder"""
    _type: str
    """GofileContent subtypes, either 'file', 'folder' or 'unknown'."""
    is_file_type: bool
    """If GofileContent is a file"""
    is_folder_type: bool
    """If GofileContent is a folder"""
    is_unknown_type: bool
    """If GofileContent is unknown (call reload() to update)"""
    is_deleted: bool
    """If content is deleted (will only register if called by it's own method delete())"""

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
        self.time_created = None
        self.is_deleted = False

    def __repr__ (self) -> str:
        _type = self._type
        if not _type:
            _type = "Unknown"

        return "<Gofile {}: content_id={} name={}>".format(_type.upper(), self.content_id, self.name)

    def delete (self) -> None:
        """Deletes itself.  When called successfully is_deleted = True"""
        guest_token = self._raw.get("guestToken")
        self._client.delete(self.content_id, token=guest_token)
        self.is_deleted = True

    def copy_to (self, dest_id: str) -> None:
        """Copies itself to destination folder's content_id"""
        self._client.copy_content(self.content_id, parent_id=dest_id)

    def copy (self, dest_id: str) -> None:
        self.copy_to(dest_id)

    def set_option(self, option: str, value, reload: bool = True) -> None:
        """Sets content option.  Full option list available at m0bb1n.github.io/gofilepy/gofilepy/options.html"""
        self._client.set_content_option(self.content_id, option, value)
        if reload:
            self.reload() #reload to get up to date information

    def reload (self):
        """Reloads any new updates to content.  If is_unknown_type must call reload() before fully usable"""
        if self.is_folder_type or (self.is_unknown_type and self.parent_id == None):
            resp, data = self._client._get_content_raw_resp(self.content_id)

            if self.is_unknown_type:
                content = GofileContent.__init_from_resp__(resp, client=self._client)

            elif self.is_folder_type:
                self._override_from_dict(data)
                return self
        
        elif (self.is_unknown_type or self.is_file_type) and self.parent_id:
            resp, data = self._client._get_content_raw_resp(self.parent_id)
            content_data = data["contents"].get(self.content_id, None)

            if content_data:
                if self.is_unknown_type:
                    #re-init instance as sub class (GofileFile or GofileFolder) of GofileContent
                    match content_data['type']:
                        case "folder":
                            self.__class__ = GofileFolder
                            self.__init__(
                                content_data["name"], content_data["id"],
                                content_data["parentFolder"], client=self._client
                            )
                        
                        case "file":
                            self.__class__ = GofileFile
                            self.__init__(
                                content_data["id"], content_data["parentFolder"],
                                client=self._client
                            )

                        case _:
                            raise TypeError("Type '{}' is not a valid option".format(content_data['type']))

                self._override_from_dict(content_data)

            return self 

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
            content = GofileFile._load_from_dict(got, client=client)
        elif _type == "folder":
            content = GofileFolder._load_from_dict(got, client=client)
        else:
            raise NotImplemented

        return content


class GofileFileDirectLink (object):
    direct_link_id: str
    """Direct link id - used to modify direct link"""
    expire: int
    """Expire time of direct link"""
    ips_allowed: list[str]
    """List of source IPs allowed to access the direct link"""
    domains_allowed: list[str]
    """List of domains allowed to access the direct link"""
    username: str
    """Username to access authenticated direct link"""
    password: str
    """Password to access authenticated direct link"""

    def __init__(self, _id, direct_link, expire, ips_allowed=[], domains_allowed=[], username=None, password=None, file=None):
        self.direct_link_id = _id
        self.link = direct_link
        self.expire = expire
        self.ips_allowed = ips_allowed
        self.domains_allowed = domains_allowed
        self.username = username
        self.password = password
        self.file = file

    @classmethod
    def _load_from_dict (cls, data: dict, file=None):
        #change to load/override from dict
        link = cls(
            data["id"],
            data["directLink"],
            data["expireTime"],
            domains_allowed=data["domainsAllowed"],
            ips_allowed=data["sourceIpsAllowed"],
            file=file
        )
        if len(data["auth"]):
            link.username = data["auth"][0]
            link.password = data["auth"][1]

        link._raw = data 

        return link

class GofileFile (GofileContent):
    time_created: int
    """Time that file was uploaded"""
    size: int
    """Size of file (in bytes)"""
    download_cnt: int
    """Amount of times the file has been downloaded"""
    mimetype: str
    """Mimetype of file"""
    server: str
    """subdomain server from where file will be downloaded (Premium)"""
    page_link: str
    """Page link to view and get download url for file"""
    md5: str
    """Hash function of file for verification"""

    direct_links: list[GofileFileDirectLink]
    """List of GofileFileDirectLinks - look at class for more info (Premium)"""

    def __init__(self, content_id: str, parent_id: str, client: GofileClient = None):
        super().__init__(content_id, parent_id, _type="file", client=client)
        self.name = None 
        self.time_created = None
        self.size = None
        self.download_cnt = None
        self.mimetype = None
        self.server = None
        self.page_link = None
        self.md5 = None
        self.direct_links = []

    def _override_from_dict(self, data: dict) -> None:
        self.content_id = data.get("id", self.content_id)
        self.parent_id = data.get("parentFolder", self.parent_id)
        self.name = data.get("name", self.name)
        self.time_created = data.get("createTime", self.time_created)
        self.size  = data.get("size", self.size)
        self.download_cnt = data.get("downloadCount", self.download_cnt)
        self.mimetype = data.get("mimetype", self.mimetype)
        self.md5 = data.get("md5", self.md5)
        self.server = data.get("serverChoosen", None)
        direct_links = data.get("directLinks", [])
        for link_data in direct_links:
            GofileFileDirectLink._load_from_dict(link_data, file=self)

        self.page_link = data.get("downloadPage", self.page_link) 

        self._raw = data

    @staticmethod
    def _load_from_dict(data: dict, client: GofileClient = None):
        file = GofileFile(data["id"], data["parentFolder"], client=client)
        file._override_from_dict(data)
        file._raw = data
        return file

    def create_direct_link(self, *args, **kwargs):
        data = self._client.create_file_direct_link(self.content_id, *args, file=self, **kwargs)
        self.direct_links.append(data)
        return data

    def download(self, out_dir: str = "./") -> str:
        """Downloads file to passed dir (default is working directory). Note: The option directLink
          \needs to be True (Premium)"""

        if self.direct_links:
            return self._client._download_file_from_direct_link(self.direct_links[0].link, out_dir=out_dir)

        else:
            raise Exception("Direct link needed - set option directLink=True (only for premium users)") 





class GofileFolder (GofileContent):
    children: list[GofileContent]
    """Children of folder, either GofileFolder or GofileFile type"""
    children_ids: list[str]
    """List of childrens' content ids"""
    time_created: int
    """Time folder was created"""
    total_size: int
    """Total size of folders' contents (in bytes)"""
    is_public: bool
    """Is folder publicly accessible"""
    is_owner: bool
    """If caller is folder owner"""
    is_root: bool
    """If folder is root folder"""
    has_password: bool
    """If folder is password protected"""
    description: str
    """A user set description using set_option"""
    tags: list
    """User set tags using set_option"""
    code: str
    """Folder shortcode to access from the browser"""

    def __init__(self, name: str, content_id: str, parent_id: str, client: GofileClient = None):
        super().__init__(content_id, parent_id, _type="folder", client=client)
        self.name = name
        self.children = []
        self.children_ids = []
        self.total_size = None
        self.total_download_cnt = None
        self.time_created = None
        self.tags = []
        self.is_public = None
        self.is_owner = None
        self.is_root = None
        self.description = None
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


    def _override_from_dict(self, data: dict) -> None:
        self.content_id = data.get("id", self.content_id)
        self.parent_id = data.get("parentFolder", self.parent_id)
        self.name = data.get("name", self.name)
        self.time_created = data.get("createTime", self.time_created)
        self.is_public  = data.get("public", self.is_public)
        self.is_owner = data.get("isOwner", self.is_owner)
        self.is_root = data.get("isRoot", False)
        self.has_password = data.get("password", self.has_password)
        self.description = data.get("description", self.description)
        self.code = data.get("code", self.code)
        self.total_size = data.get("totalSize", self.total_size)
        self.total_download_cnt = data.get("totalDownloadCount", self.total_download_cnt)
        self.children_ids = data.get("childs")
        self.children = self.__init_children_from_contents__(data)

        self.tags = data.get("tags", "").split(",")
        if self.tags[0] == "":
            self.tags = []



        self._raw = data


    @staticmethod
    def _load_from_dict(data: dict, client: GofileClient = None) -> GofileFolder:
        parent_id = data.get("parentFolder", None)
        folder = GofileFolder(data["name"], data["id"], parent_id, client=client)
        folder._override_from_dict(data)
        folder._raw = data

        return folder

    def upload(self, path: str = None, file: BufferedReader = None) -> GofileFile:
        return self._client.upload(file=file, path=path, parent_id=self.content_id)

