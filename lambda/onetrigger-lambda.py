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

import os, logging, sys, time, datetime, json
import requests

# Configure logging
LOGGING_FORMAT = '%(asctime)s - %(levelname)s - %(message)s'
logging.basicConfig(format=LOGGING_FORMAT, level=logging.INFO)


class OneTriggerLambda:

    SPACES_PATH = '/api/v3/oneprovider/spaces/'
    FILES_PATH = '/api/v3/oneprovider/files/'
    ATTRIBUTES_PATH = '/api/v3/oneprovider/attributes/'
    LAMBDA_ASYNC_HEADER = {'X-Amz-Invocation-Type': 'Event'}

    def __init__(self):
        self._host = os.environ.get('ONEPROVIDER_HOST')
        self._token = os.environ.get('ONEDATA_ACCESS_TOKEN')
        self._space = os.environ.get('ONEDATA_SPACE')
        self._header = {'X-Auth-Token': self._token}
        self._folders = self._get_folders()
        self._webhooks = self._get_webhooks()
        self.response_body = {}

    @staticmethod
    def get_latest_execution_timestamp():
        """
        Get the latest execution timestamp as an integer using
        the current timestamp and the execution frequency (in minutes)
        stored in the environment variable EXECUTION_FREQUENCY.
        """
        execution_frequency = int(os.environ.get('EXECUTION_FREQUENCY')) * 60
        return int(time.time()) - execution_frequency

    def _set_warning(self, msg):
        """
        Log a warning and add it to the response body.
        """
        logging.warning(msg)
        if 'warnings' in self.response_body:
            self.response_body['warnings'].append(msg)
        else:
            self.response_body['warnings'] = [msg]

    def _get_folders(self):
        """
        Get a dictionary of folders defined in environment variables:
        
        ONETRIGGER_FOLDER_XX (where XX is the key of the folder)
        """
        folders = {}

        for key, value in os.environ.items():
            if key.startswith('ONETRIGGER_FOLDER_'):
                folder_key = key.split('_')[2]
                folders[folder_key] = value

        return folders

    def _get_webhooks(self):
        """
        Get a dictionary of webhooks defined in environment variables:
        
        ONETRIGGER_WEBHOOK_XX (where XX is the key of the webhook)
        """
        webhooks = {}

        for key, value in os.environ.items():
            if key.startswith('ONETRIGGER_WEBHOOK_'):
                webhook_key = key.split('_')[2]
                webhooks[webhook_key] = value

        return webhooks

    def _check_space(self):
        """
        Check access to the space with the provided credentials.
        """
        space_url = 'https://{0}{1}'.format(self._host, self.SPACES_PATH)
        r = requests.get(space_url, headers=self._header)
        if r.status_code == 200:
            spaces = r.json()
            space_names = []
            for space in spaces:
                space_names.append(space['name'])
            if self._space not in space_names:
                raise Exception('The space "{0}" does not exist.'.format(self._space))
        elif r.status_code == 401:
            raise Exception('Invalid token')
        else:
            raise Exception('Error connecting to provider host')

    def _check_folders(self, timestamp):
        """
        Check if defined folders exists in the space and clear 
        the ones that have a 'mtime' < timestamp.
        Update the folders' dictionary with the valid ones.
        """
        # Create new requests session and set the header
        s = requests.Session()
        s.headers.update(self._header)

        valid_folders = {}
        for key, folder in self._folders.items():
            folder_url = 'https://{0}{1}{2}/{3}'.format(self._host, self.ATTRIBUTES_PATH, self._space, folder)
            r = s.get(folder_url)
            if r.status_code == 404:
                self._set_warning('The folder "{0}" does not exist. Ignoring it.'.format(folder))
            elif r.status_code == 200:
                attributes = r.json()
                if attributes['type'].lower() == 'dir' and int(attributes['mtime']) > timestamp:
                    valid_folders[key] = folder
            else:
                raise Exception('Error connecting to provider host')

        s.close()

        self._folders = valid_folders

    def _post_event(self, key, file_id, file_path):
        """
        Send a JSON event to webhook following the structure:
            
        {
            "Key": "/my-onedata-space/files/file.txt",
            "Records": [
                {
                    "objectKey": "file.txt",
                    "objectId": "0000034500046EE9C67756964233836666330363031303664303964623739666562393165336632306232613736236664323861626330656664643566313938313333336633356232333838623137",
                    "eventTime": "2019-02-07T09:51:04.347823",
                    "eventSource": "OneTrigger"
                }
            ]
        }
        """
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
            r = requests.post(self._webhooks[key], json=event, headers=self.LAMBDA_ASYNC_HEADER)
            logging.info('File "{0}" uploaded. Event sent to {1} - {2}'.format(
                event['Records'][0]['objectKey'], self._webhooks[key], r.status_code))
        except Exception as e:
            self._set_warning('Error sending event to {0} - {1}'.format(self._webhooks[key], e))

    def _check_files(self, timestamp):
        """
        Check if new files have been created in the provided folders
        since the specified timestamp and post events.
        """
        # Create new requests session and set the header
        s = requests.Session()
        s.headers.update(self._header)

        for key, folder in self._folders.items():
            paths = ['{0}/{1}'.format(self._space, folder)]
            for path in paths:
                files_url = 'https://{0}{1}{2}'.format(self._host, self.FILES_PATH, path)
                r = s.get(files_url)
                if r.status_code == 200:
                    path_items = r.json()
                    for item in path_items:
                        attributes_url = 'https://{0}{1}{2}'.format(self._host, self.ATTRIBUTES_PATH, item['path'].lstrip('/'))
                        r = s.get(attributes_url)
                        if r.status_code == 200:
                            attributes = r.json()
                            if int(attributes['mtime']) > timestamp:
                                if attributes['type'].lower() == 'dir':
                                    paths.append(item['path'].lstrip('/'))
                                elif attributes['type'].lower() == 'reg':
                                    if 'new_files' in self.response_body:
                                        self.response_body['new_files'].append(item['path'])
                                    else:
                                        self.response_body['new_files'] = [item['path']]
                                    self._post_event(key, item['id'], item['path'])
                        else:
                            raise Exception('Unable to get attributes of item "{0}"'.format(item['path']))
                else:
                    raise Exception('Unable to list files in folder "{0}"'.format(path))

        s.close()

    def _create_response(self, body, status_code):
        """
        Generate HTTP response
        """
        return {
            'statusCode': status_code,
            'body': json.dumps(body),
            'isBase64Encoded': False
        }

    def main(self):
        """
        Main method.
        """
        try:
            # Get the latest execution timestamp
            timestamp = self.get_latest_execution_timestamp()
            # Ensure that the defined space exists
            self._check_space()
            # Check if folders exists and clear the ones that
            # have a 'mtime'< timestamp
            self._check_folders(timestamp)
            # Check folders for new files and post events
            self._check_files(timestamp)
            return self._create_response(self.response_body, 200)
        except Exception as e:
            logging.error(e)
            return self._create_response({'error': str(e)}, 500)


def lambda_handler(event, context):
    """
    Handler to execute the function.
    """
    return OneTriggerLambda().main()

if __name__ == '__main__':
    print(OneTriggerLambda().main())