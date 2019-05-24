# OneTrigger - Trigger webhooks by Onedata events
# Copyright (C) GRyCAP - I3M - UPV
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import os, logging, sys, time, datetime
import requests
from tabulate import tabulate


class OneproviderClient:

    CONNECTION_RETRIES = 3
    TIMEOUT = 10
    WAIT_SECONDS = 10
    SPACES_PATH = '/api/v3/oneprovider/spaces/'
    FILES_PATH = '/api/v3/oneprovider/files/'
    ATTRIBUTES_PATH = '/api/v3/oneprovider/attributes/'

    def __init__(self, settings):
        self._settings = settings
        self._header = {'X-Auth-Token': settings.token}

    def _check_space(self):
        self._settings.space = self._settings.space.strip('/')
        space_url = 'https://{0}{1}'.format(self._settings.host, self.SPACES_PATH)
        try:
            r = requests.get(space_url, headers=self._header, verify=not self._settings.insecure)
            if r.status_code == 200:
                spaces = r.json()
                space_names = []
                for space in spaces:
                    space_names.append(space['name'])
                if self._settings.space not in space_names:
                    logging.error('The space "{0}" does not exist. Please check the available spaces with the "list-spaces" subcommand.'.format(self._settings.space))
                    sys.exit(1)
            elif r.status_code == 401:
                logging.error('Invalid token')
                sys.exit(1)
            else:
                raise Exception
        except Exception:
            logging.error('Error connecting to provider host')
            sys.exit(1)

    def _check_folder(self):
        folder = None
        if self._settings.folder != None:
            folder = self._settings.folder.strip('/')
            folder_url = 'https://{0}{1}{2}/{3}'.format(self._settings.host, self.FILES_PATH, self._settings.space, folder)
            try:
                r = requests.get(folder_url, headers=self._header, verify=not self._settings.insecure)
                if r.status_code == 404:
                    logging.warning('The folder "{0}" does not exist. Listening events on space folder'.format(folder))
                    folder = None
                elif r.status_code != 200:
                    raise Exception
            except Exception:
                logging.error('Error connecting to provider host')
                sys.exit(1)
        return folder

    def _post_event(self, file_id, file_path):
        event = {
            'Key': file_path,
            'Records': [
                {
                    'objectKey': os.path.basename(file_path),
                    'objectId': file_id,
                    'eventTime': datetime.datetime.utcnow().isoformat(),
                    'eventSource': 'OneTrigger'
                }
            ]
        }
        try:
            r = requests.post(self._settings.webhook, json=event)
            logging.info('File "{0}" uploaded. Event sent to {1} - {2}'.format(
                event['Records'][0]['objectKey'], self._settings.webhook, r.status_code))
        except Exception:
            logging.error(
                'Error sending event to {0}'.format(self._settings.webhook))

    def _subscribe(self, folder):
        folder_msg = '' if folder == None else '. Listening events on "/{0}/{1}/" folder'.format(self._settings.space, folder)
        files = []
        initialized = False
        attempts = 0
        logging.info('Subscribing to file events in space "{0}" from provider "{1}"...{2}'.format(self._settings.space, self._settings.host, folder_msg))
        while attempts < self.CONNECTION_RETRIES:
            try:
                while True:
                    # Get all files in folder and subfolders
                    new_files = []
                    paths = ['{0}/{1}'.format(self._settings.space, folder)] if folder != None else [self._settings.space]
                    for path in paths:
                        files_url = 'https://{0}{1}{2}'.format(self._settings.host, self.FILES_PATH, path)
                        r = requests.get(files_url, headers=self._header, verify=not self._settings.insecure)
                        if r.status_code == 200:
                            path_items = r.json()
                            for item in path_items:
                                if item['id'] in files:
                                    new_files.append(item['id'])
                                    continue
                                attributes_url = 'https://{0}{1}{2}'.format(self._settings.host, self.ATTRIBUTES_PATH, item['path'].lstrip('/'))
                                r = requests.get(attributes_url, headers=self._header, verify=not self._settings.insecure)
                                if r.status_code == 200:
                                    attributes = r.json()
                                    # Check subfolders
                                    if attributes['type'].lower() == 'dir':
                                        paths.append(item['path'])
                                    if attributes['type'].lower() == 'reg':
                                        new_files.append(item['id'])
                                        if initialized and item['id'] not in files:
                                            self._post_event(item['id'], item['path'])
                                else:
                                    raise Exception  
                        else:
                            raise Exception
                    attempts = 0
                    files = new_files
                    #logging.info('Connected - {0} files'.format(len(files)))
                    initialized = True
                    time.sleep(self.TIMEOUT)
            except Exception:
                logging.warning('Connection lost. Retrying...')
            attempts += 1
            time.sleep(self.WAIT_SECONDS)
        logging.error('Connection error')
        sys.exit(1)

    def run(self):
        self._check_space()
        folder = self._check_folder()
        self._subscribe(folder)

    def _print_spaces(self, spaces):
        table = []
        for space in spaces:
            table.append([space['name'], space['spaceId']])
        print(tabulate(table, headers=['Name', 'Space ID']))

    def list_spaces(self):
        list_spaces_url = 'https://{0}{1}'.format(self._settings.host, self.SPACES_PATH)
        try:
            r = requests.get(list_spaces_url, headers=self._header, verify=not self._settings.insecure)
            if r.status_code == 200:
                spaces = r.json()
                self._print_spaces(spaces)
            elif r.status_code == 401:
                logging.error('Invalid token')
                sys.exit(1)
            else:
                raise Exception
        except Exception:
            logging.error('Error connecting to provider host')
            sys.exit(1)
