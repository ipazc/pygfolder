#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
#MIT License
#
#Copyright (c) 2017 Iván de Paz Centeno
#
#Permission is hereby granted, free of charge, to any person obtaining a copy
#of this software and associated documentation files (the "Software"), to deal
#in the Software without restriction, including without limitation the rights
#to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
#copies of the Software, and to permit persons to whom the Software is
#furnished to do so, subject to the following conditions:
#
#The above copyright notice and this permission notice shall be included in all
#copies or substantial portions of the Software.
#
#THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
#IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
#FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
#AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
#LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
#OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
#SOFTWARE.

from concurrent.futures import ThreadPoolExecutor
import json
import os
from time import sleep
from oauthlib.oauth2 import WebApplicationClient
from requests_oauthlib import OAuth2Session

__author__ = 'Iván de Paz Centeno'


FOLDER_MIME = "application/vnd.google-apps.folder"

def retry(func_wrap):
    def fun(obj, *args, **kwargs):
        retry = -1
        retrieved = False
        result = []

        while not retrieved and retry < 2:
            retry += 1
            result, status_code, retry_func = func_wrap(obj, *args, **kwargs)

            if status_code > 299:
                retry_func()
            else:
                retrieved = True

        if retry == 2:
            raise Exception("Seems that the authorization code is not valid anymore.")

        return result
    return fun


class PyGFolder(object):
    def __init__(self, root_folder="/", root_ids=None, token=None, resolve=True):
        from os.path import expanduser
        self.root_folder = root_folder

        self.home = expanduser("~")
        self.config = {}
        self.__load_config_file()
        self.scope = ['https://www.googleapis.com/auth/userinfo.email',
                 'https://www.googleapis.com/auth/userinfo.profile',
                 'https://www.googleapis.com/auth/drive']
        self.drive_api = "https://www.googleapis.com/drive/v3"
        self.token = token or None
        self.oauth = OAuth2Session(self.config['client_id'], redirect_uri=self.config['redirect_uris'][0],
                          scope=self.scope, client=WebApplicationClient(self.config['client_id']))

        if not token and 'refresh_token' in self.config:
            self.__refresh_token()
        elif not token and 'code' in self.config:
            self.__build_token_from_code()

        self.root_ids = root_ids or ["root"]

        if resolve and self.token and root_folder.split("/") != ["", ""]:
            if root_folder.startswith("/"):
                root_folder = root_folder[1:]
            result = self[root_folder]
            self.root_ids = result.root_ids
            self.root_folder = result.root_folder

    def has_token(self):
        return self.token is not None

    def request_token(self):
        file_path = os.path.join(self.home, ".pygfolderrc")

        authorization_url, state = self.oauth.authorization_url(
                self.config['auth_uri'],
                access_type="offline", prompt="select_account")

        print('Please go to {} and authorize access.'.format(authorization_url))
        print('Then fill the {} file with a key named "code" setting the value retrieved from the authorization url.'.format(file_path))
        self.__clear_config_code()

        print("Waiting for update of the file...")
        while 'code' not in self.config:
            self.__load_config_file()
            sleep(3)

        print("Updated, requesting token...")
        self.__build_token_from_code()
        self.__save_config_file()

    def __build_token_from_code(self):
        self.token = self.oauth.fetch_token(self.config['token_uri'], code=self.config['code'],
            client_secret=self.config['client_secret'])
        self.config['refresh_token'] = self.token['refresh_token']

    def __save_config_file(self):
        file_path = os.path.join(self.home, ".pygfolderrc")

        with open(file_path, "w") as f:
            json.dump({'installed': self.config}, f, indent=4)

    def __clear_config_code(self):
        if 'code' in self.config:
            del self.config['code']
        if 'refresh_token' in self.config:
            del self.config['refresh_token']

        self.__save_config_file()

    def __load_config_file(self):
        file_path = os.path.join(self.home, ".pygfolderrc")
        if os.path.exists(file_path):
            with open(file_path) as f:
                self.config = json.load(f)['installed']
        else:
            raise Exception("The config file {} is required. It must be a json file with a key 'installed' containing the json credentials (client_id, client_secret, token_uri, auth_uri, ...). You can download this file directly from your credentials section of the Google API console for Google Drive.".format(file_path))

    def __refresh_token(self):
        if 'refresh_token' not in self.config:
            raise Exception("No refresh token available, invoke request_token() at least once before using the object.")
        self.token = self.oauth.refresh_token(self.config['token_uri'], refresh_token=self.config['refresh_token'],
                            client_id=self.config['client_id'], client_secret=self.config['client_secret'])

    def files(self):
        query = {'q': "'{}' in parents and trashed = false and not mimeType = '{}'".format(self.root_ids[-1], FOLDER_MIME), 'pageSize': 1000}

        result = []
        for element_list in self.__retrieve_elements(query):
            result += [file['name'] for file in element_list]

        return result

    def keys(self):
        query = {'q': "'{}' in parents and trashed = false".format(self.root_ids[-1]), 'pageSize': 1000}

        result = []
        for element_list in self.__retrieve_elements(query):
            result += [file['name'] for file in element_list]

        return result

    def folders(self):
        query = {'q': "'{}' in parents and trashed = false and mimeType = '{}'".format(self.root_ids[-1], FOLDER_MIME), 'pageSize': 1000}

        result = []
        for element_list in self.__retrieve_elements(query):
            result += [file['name'] for file in element_list]

        return result

    @retry
    def __retrieve_element(self, query, page_token=None):
        params = dict(query)

        if page_token:
            params['pageToken'] = page_token

        response = self.oauth.get("{}/files".format(self.drive_api), params=params)
        status_code = response.status_code
        files_json = response.json()

        return files_json, status_code, self.__refresh_token

    def __retrieve_elements(self, query):
        pool = ThreadPoolExecutor(2)

        completely_fetched = False
        buffer = None

        while not completely_fetched:
            elements = (buffer and buffer.result()) or self.__retrieve_element(query)

            completely_fetched = not 'nextPageToken' in elements

            if not completely_fetched:
                buffer = pool.submit(self.__retrieve_element, query, page_token=elements['nextPageToken'])

            yield elements['files']

    @retry
    def __file_meta(self, file_name, root_id=None):
        root_id = root_id or "root"
        response = self.oauth.get("{}/files".format(self.drive_api), params={'q': "'{}' in parents and trashed = false and name = '{}'".format(root_id, file_name)})

        metadata_json = response.json()
        if 'files' in metadata_json:
            result = [file for file in metadata_json['files']]
            if len(result) == 0:
                raise KeyError("File {} not found.".format(file_name))
            else:
                result = result[0]
        else:
            result = {}

        return result, response.status_code, self.__refresh_token

    @retry
    def __get_file(self, item, mimetype=None):
        if item.startswith("/"): item = item[1:]

        keys = [key for key in item.split("/") if key.strip() != ""]

        if len(keys) > 1:
            pygfolder = self[keys[0]]
            return pygfolder[os.path.join(*keys[1:])], 200, self.__refresh_token

        metadata = self.__file_meta(item, self.root_ids[-1])

        if metadata['mimeType'] == FOLDER_MIME:
            result = PyGFolder(os.path.join(self.root_folder, item), root_ids=self.root_ids + [metadata['id']], token=self.token, resolve=False)
            status_code = 200
        elif "application/vnd.google-apps" in metadata['mimeType']:

            if mimetype is None:
                raise KeyError("The specified file is in Google's format and must be exported in order to be downloaded. The problem is that I cannot infer the MimeType for exporting it automatically. You must use the export() function, specifying the desired MimeType, in order to retrieve its contents.")
            else:
                response = self.oauth.get("{}/files/{}/export".format(self.drive_api, metadata['id']), params={'mimeType': mimetype})
                result = response.content
                status_code= response.status_code

        else:
            response = self.oauth.get("{}/files/{}".format(self.drive_api, metadata['id']), params={'alt': 'media'})
            result = response.content
            status_code = response.status_code

        return result, status_code, self.__refresh_token

    def __getitem__(self, item):
        return self.__get_file(item)

    def export(self, item, mimetype):
        return self.__get_file(item, mimetype=mimetype)

    @retry
    def __make_folder(self, folder_name):
        creation_data = {
                "name": folder_name,
                "parents": [self.root_ids[-1]],
                "mimeType": FOLDER_MIME,
            }
        response = self.oauth.post("{}/files".format(self.drive_api), json=creation_data)

        return folder_name, response.status_code, self.__refresh_token

    @retry
    def __setitem__(self, key, value):
        if key.startswith("/"): key = key[1:]

        keys = key.split("/")

        if len(keys) > 1:
            try:
                pygfolder = self[keys[0]]
            except KeyError:
                # Folder doesn't exist. Let's create it.
                pygfolder = self[self.__make_folder(keys[0])]
            pygfolder[os.path.join(*keys[1:])] = value

            return "Done", 200, self.__refresh_token

        key = keys[0]

        try:
            # Modify the file
            metadata = self.__file_meta(key, self.root_ids[-1])
            if 'folder' in metadata['mimeType']:
                raise KeyError("Folders can't be modified.")
            file_id = metadata['id']

        except KeyError:
            # Create the file.
            creation_data = {
                "name": key,
                "parents": [self.root_ids[-1]]
            }
            response = self.oauth.post("{}/files".format(self.drive_api), json=creation_data)

            if response.status_code != 200:
                return None, response.status_code, self.__refresh_token

            file_id = response.json()['id']

        response = self.oauth.patch("https://www.googleapis.com/upload/drive/v3/files/{}".format(file_id), data=value)
        return response.json, response.status_code, self.__refresh_token

    def __iter__(self, extra_option=""):

        query = {'q': "'{}' in parents and trashed = false".format(self.root_ids[-1]), 'pageSize': 1000}

        if extra_option != "":
            query['q'] += " and {}".format(extra_option)

        for element_list in self.__retrieve_elements(query):
            for file in element_list:
                yield file['name']

    def items(self, extra_option=""):
        query = {'q': "'{}' in parents and trashed = false".format(self.root_ids[-1]), 'pageSize': 1000}

        if extra_option != "":
            query['q'] += " and {}".format(extra_option)

        pool = ThreadPoolExecutor(2)

        for element_list in self.__retrieve_elements(query):
            buffer = None

            for file in element_list:
                submission = pool.submit(self.__getitem__, file['name'])

                if buffer:
                    yield buffer[0], buffer[1].result()

                buffer = (file['name'], submission)

            if buffer:
                yield buffer[0], buffer[1].result()

    def files_items(self):
        for file, content in self.items(extra_option="not mimeType = '{}'".format(FOLDER_MIME)):
            yield file, content

    def folders_items(self):
        for file, content in self.items(extra_option="mimeType = '{}'".format(FOLDER_MIME)):
            yield file, content

    def __len__(self):
        return len(self.keys())

    def __str__(self):
        return "PyGFolder: {}".format(self.root_folder)

    def __repr__(self):
        return "PyGFolder: {}".format(self.root_folder)

    def __delitem__(self, item):
        if item.startswith("/"): item = item[1:]

        keys = [key for key in item.split("/") if key.strip() != ""]

        if len(keys) > 1:
            pygfolder = self[keys[0]] # type: PyGFolder
            del pygfolder[os.path.join(*keys[1:])]
        else:
            metadata = self.__file_meta(item, self.root_ids[-1])
            self.__remove_id(metadata['id'])

    @retry
    def __remove_id(self, id):
        response =self.oauth.delete("{}/files/{}".format(self.drive_api, id))
        status_code = response.status_code
        result = ""

        return result, status_code, self.__refresh_token
