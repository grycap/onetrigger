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
 
import os, json, logging, argparse, sys, signal, time, datetime
import requests

LOGGING_FORMAT = '%(asctime)s - %(levelname)s - %(message)s'
CONNECTION_RETRIES = 3
TIMEOUT = 10
WAIT_SECONDS = 10
CHANGES_PATH = '/api/v3/oneprovider/changes/metadata/'
SPACES_PATH = '/api/v3/oneprovider/spaces/'
FILES_PATH = '/api/v3/oneprovider/files/'
ATTRIBUTES_PATH = '/api/v3/oneprovider/attributes/'

logging.basicConfig(format=LOGGING_FORMAT, level=logging.INFO)

# Set signal handlers
def sig_handler(sig, frame):
    logging.info('Closing OneTrigger... Bye!')
    sys.exit(0)
for sig in (signal.SIGINT, signal.SIGTERM):
    signal.signal(sig, sig_handler)

# Read environment variables
env_host = os.environ.get('ONEPROVIDER_HOST')
env_token = os.environ.get('ONEDATA_ACCESS_TOKEN')
env_space_id = os.environ.get('ONEDATA_SPACE_ID')
env_webhook = os.environ.get('ONETRIGGER_WEBHOOK')
env_folder = os.environ.get('ONEDATA_SPACE_FOLDER')
env_insecure = json.loads(os.environ.get('ONEPROVIDER_INSECURE').lower()) if 'ONEPROVIDER_INSECURE' in os.environ else False

# Define argument parser
parser = argparse.ArgumentParser(description='Trigger webhooks by Onedata events')

parser.add_argument('-H', '--oneprovider-host', action='store', default=env_host, dest='host',
                    help='Oneprovider hostname or IP')
parser.add_argument('-t', '--token', action='store', default=env_token, dest='token',
                    help='Onedata access token')
parser.add_argument('-s', '--space-id', action='store', default=env_space_id, dest='space_id',
                    help='Onedata space ID')
parser.add_argument('-w', '--webhook', action='store', default=env_webhook, dest='webhook',
                    help='Webhook to send events')
parser.add_argument('-f', '--folder', action='store', default=env_folder, dest='folder',
                    help='Folder to listen events (Optional)')
parser.add_argument('-i', '--insecure', action='store_true', default=env_insecure, dest='insecure',
                    help='Connect to a provider without a trusted certificate')

settings = parser.parse_args()

# Check if required settings are set
required = True
if settings.host == None:
    logging.error('Oneprovider host is not provided. Please set it via "--oneprovider-host" argument or "ONEPROVIDER_HOST" environment variable')
    required = False
if settings.token == None:
    logging.error('Onedata access token is not provided. Please set it via "--token" argument or "ONEDATA_ACCESS_TOKEN" environment variable')
    required = False
if settings.space_id == None:
    logging.error('Onedata space ID is not provided. Please set it via "--space-id" argument or "ONEDATA_SPACE_ID" environment variable')
    required = False
if settings.webhook == None:
    logging.error('Webhook to send events is not provided. Please set it via "--webhook" argument or "ONETRIGGER_WEBHOOK" environment variable')
    required = False
if required == False:
    sys.exit(1)

header = {'X-Auth-Token': settings.token}
# Check connection
list_spaces_url = 'https://{0}{1}'.format(settings.host, SPACES_PATH)
try:
    r = requests.get(list_spaces_url, headers=header, verify=not settings.insecure)
    if r.status_code == 401:
        logging.error('Invalid token')
        sys.exit(1)
    elif r.status_code != 200:
        raise Exception
except Exception:
    logging.error('Error connecting to provider host')
    sys.exit(1)

# Get space name
space_url = 'https://{0}{1}{2}'.format(settings.host, SPACES_PATH, settings.space_id)
try:
    r = requests.get(space_url, headers=header, verify=not settings.insecure)
    if r.status_code == 200:
        space_name = r.json()['name']
    elif r.status_code == 404:
        logging.error('Invalid space ID')
        sys.exit(1)
    else:
        raise Exception
except Exception:
    logging.error('Error connecting to provider host')
    sys.exit(1)

# Check folder if folder option is set
folder_msg = ''
if settings.folder != None:
    settings.folder = settings.folder.strip('/')
    folder_url = 'https://{0}{1}{2}/{3}'.format(settings.host, FILES_PATH, space_name, settings.folder)
    try:
        r = requests.get(folder_url, headers=header, verify=not settings.insecure)
        if r.status_code == 200:
            folder_msg = '. Listening events on "/{0}/{1}/" folder'.format(space_name, settings.folder)
        elif r.status_code == 404:
            logging.warning('The provided folder does not exist. Listening events on space folder')
            settings.folder = None
        else:
            raise Exception
    except Exception:
        logging.error('Error connecting to provider host')
        sys.exit(1)

def post_event(file_id, file_path):
    event = {
        'id': file_id,
        'file': os.path.basename(file_path),
        'path': file_path,
        'eventSource': 'OneTrigger',
        'eventTime': datetime.datetime.utcnow().isoformat()
    }
    try:
        r = requests.post(settings.webhook, json=event)
        logging.info('File "{0}" uploaded. Event sent to {1} - {2}'.format(event['file'], settings.webhook, r.status_code))
    except Exception:
        logging.error('Error sending event to {0}'.format(settings.webhook))

# Subscribe to Oneprovider space file events
files = []
initialized = False
changes_url = 'https://{0}{1}{2}'.format(settings.host, CHANGES_PATH, settings.space_id)
attempts = 0
logging.info('Subscribing to file events in space "{0}" from provider "{1}"...{2}'.format(space_name, settings.host, folder_msg))
while attempts < CONNECTION_RETRIES:
    try:
        while True:
            # Get all files in folder and subfolders
            new_files = []
            paths = ['{0}/{1}'.format(space_name, settings.folder)] if settings.folder != None else [space_name]
            for path in paths:
                files_url = 'https://{0}{1}{2}'.format(settings.host, FILES_PATH, path)
                r = requests.get(files_url, headers=header, verify=not settings.insecure)
                if r.status_code == 200:
                    path_items = r.json()
                    for item in path_items:
                        if item['id'] in files:
                            new_files.append(item['id'])
                            continue
                        attributes_url = 'https://{0}{1}{2}'.format(settings.host, ATTRIBUTES_PATH, item['path'].lstrip('/'))
                        r = requests.get(attributes_url, headers=header, verify=not settings.insecure)
                        if r.status_code == 200:
                            attributes = r.json()
                            # Check subfolders
                            if attributes['type'].lower() == 'dir':
                                paths.append(item['path'])
                            if attributes['type'].lower() == 'reg':
                                new_files.append(item['id'])
                                if initialized and item['id'] not in files:
                                    post_event(item['id'], item['path'])
                        else:
                            raise Exception  
                else:
                    raise Exception
            attempts = 0
            files = new_files
            #logging.info('Connected - {0} files'.format(len(files)))
            initialized = True
            time.sleep(TIMEOUT)
    except Exception:
        logging.warning('Connection lost. Retrying...')
    attempts += 1
    time.sleep(WAIT_SECONDS)
logging.error('Connection error')
sys.exit(1)
