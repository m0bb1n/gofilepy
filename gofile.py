import requests
import os



class GofileClient (object):
    CREDS_STORED = False
    BASE_DOMAIN = 'gofile.io'
    API_SUBDOMAIN = 'apiv2'
    BASE_API_URL = 'https://'+API_SUBDOMAIN+'.'+BASE_DOMAIN
    API_ROUTE_GET_SERVER = BASE_API_URL + '/getServer'
    API_ROUTE_GET_FILE_SERVER = API_ROUTE_GET_SERVER + '?c={}'

    GET_UPLOAD_FORMAT = 'https://{}.gofile.io/getUpload?c={}'

    UPLOAD_URL_FORMAT = 'https://{}.gofile.io/upload'
    DELETE_URL_FORMAT = 'https://{}.gofile.io/deleteUpload?c={}&rc={}&removeAll=true'
    FILE_URL_FORMAT = 'https://'+BASE_DOMAIN+'/{}'
    DOWNLOAD_URL_FORMAT = 'https://{}.'+BASE_DOMAIN+'/download/{}/{}'
    server = None

    CREDS_STORED = False

    email = None
    password = None


    def __init__(self, email=None, default_password=None, verbose=False):
        if email or default_password:
            self.email = email
            self.password = default_password
            self.CREDS_STORED = True
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
        return GofileClient.UPLOAD_URL_FORMAT.format(self.server)

    @staticmethod
    def get_best_server(throw_if_not_200=False):
        url = GofileClient.API_ROUTE_GET_SERVER
        resp = requests.get(url)
        return GofileClient.handle_response(resp)['server']


    def delete(self, code, rc):
        url = self.DELETE_URL_FORMAT.format(self.server, code, rc)
        resp = requests.get(url)
        data = GofileClient.handle_response(resp)

    def get_file_info(self, code, server):
        #FILES WITH PASSWORD WONT WORK
        url = self.GET_UPLOAD_FORMAT.format(server, code)
        resp = requests.get(url)
        data = GofileClient.handle_response(resp)
        return data

    def get_file_download_url(self, code, filename=None):
        file_server_url = self.API_ROUTE_GET_FILE_SERVER.format(code)
        resp = requests.get(file_server_url)
        data = GofileClient.handle_response(resp)
        file_server = data['server']

        if not filename:
            file_info = self.get_file_info(code, file_server)
            for i, f in file_info['files'].items():
                filename = f['name']
                break
            pass

        url = self.DOWNLOAD_URL_FORMAT.format(file_server, code, filename)
        return url

    def download(self, code, out_path):
        file_server_url = self.API_ROUTE_GET_FILE_SERVER.format(code)
        resp = requests.get(file_server_url)
        meta = GofileClient.handle_response(resp)
        file_server = meta['server']
        data = self.get_file_info(code, file_server)
        content = requests.get(data['link'])
        with open(out_path, 'wb') as f:
            f.write(content)


    def upload(self, *, files=None, file_paths='', desc='', expire=None, tags=[], email=False, password=False):
        if email==False:
            email = self.email
        if password==False:
            password = self.password


        if files and type(files) != type(list):
            files = [files]

        if file_paths and type(file_paths) != type(list):
            file_paths = [file_paths]
            for fp in file_paths:
                files.append(open(fp, 'rb'))

        files_uploading = []
        for f in files:
            files_uploading.append(('filesUploaded',f))

        url = self.get_best_upload_url()
        data = {'email': email, 'password':password, 'description':desc}
        if len(tags):
            tags = ','.join(tags)
            data['tags'] = tags
        if expire:
            data['expire'] = expire

        if self.verbose:
            print("Gofile payload: {}".format(data))
        filenames = [os.path.basename(f.name) for f in files]
        resp = requests.post(url, data=data, files=files_uploading)
        got = GofileClient.handle_response(resp)



        got['download_urls'] = []
        got['info_urls'] = []
        for filename in filenames:
            durl = self.DOWNLOAD_URL_FORMAT.format(self.server, got['code'], filename)
            iurl = self.GET_UPLOAD_FORMAT.format(self.server, got['code'])
            got['download_urls'].append(durl)
            got['info_urls'].append(iurl)

        return got


