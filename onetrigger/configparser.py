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

import os, json, argparse, logging, sys
from onetrigger.version import __version__


class ConfigParser:

    def __init__(self):
        self._parse_env_config()
        self._create_parser()
        self._create_subparsers()

    def _parse_env_config(self):
        self._env_host = os.environ.get('ONEPROVIDER_HOST')
        self._env_token = os.environ.get('ONEDATA_ACCESS_TOKEN')
        self._env_space = os.environ.get('ONEDATA_SPACE')
        self._env_webhook = os.environ.get('ONETRIGGER_WEBHOOK')
        self._env_folder = os.environ.get('ONEDATA_SPACE_FOLDER')
        self._env_insecure = json.loads(os.environ.get('ONEPROVIDER_INSECURE').lower()) if 'ONEPROVIDER_INSECURE' in os.environ else False

    def _create_parser(self):
        self._parser = argparse.ArgumentParser(description='Trigger webhooks by Onedata events')
        self._parser.add_argument('-v', '--version', action='version', version='version {0}'.format(__version__),
                            help='show OneTrigger version')

        # Parent parser to describe shared arguments
        self._parent_parser = argparse.ArgumentParser(add_help=False)
        self._parent_parser.add_argument('-H', '--oneprovider-host', action='store', default=self._env_host, dest='host',
                            help='Oneprovider hostname or IP')
        self._parent_parser.add_argument('-t', '--token', action='store', default=self._env_token, dest='token',
                            help='Onedata access token')
        self._parent_parser.add_argument('-i', '--insecure', action='store_true', default=self._env_insecure, dest='insecure',
                            help='Connect to a provider without a trusted certificate (Optional)')

    def _create_subparsers(self):
        self._subparsers = self._parser.add_subparsers(title='Commands', dest='command')
        self._subparsers.required = True
        self._create_run_parser()
        self._create_list_spaces_parser()

    def _create_run_parser(self):
        self._run_parser = self._subparsers.add_parser('run', parents=[self._parent_parser], help='Run OneTrigger')
        self._run_parser.add_argument('-s', '--space', action='store', default=self._env_space, dest='space',
                            help='Onedata space')
        self._run_parser.add_argument('-w', '--webhook', action='store', default=self._env_webhook, dest='webhook',
                            help='Webhook to send events')
        self._run_parser.add_argument('-f', '--folder', action='store', default=self._env_folder, dest='folder',
                            help='Folder to listen events (Optional)')

    def _create_list_spaces_parser(self):
        self._list_spaces_parser = self._subparsers.add_parser('list-spaces', parents=[self._parent_parser], help='List available spaces')

    def _check_config(self, config):
        required = True
        if config.host == None:
            logging.error('Oneprovider host is not provided. Please set it via "--oneprovider-host" argument or "ONEPROVIDER_HOST" environment variable')
            required = False
        if config.token == None:
            logging.error('Onedata access token is not provided. Please set it via "--token" argument or "ONEDATA_ACCESS_TOKEN" environment variable')
            required = False
        if config.command == 'run':
            if config.space == None:
                logging.error('Onedata space is not provided. Please set it via "--space" argument or "ONEDATA_SPACE" environment variable')
                required = False
            if config.webhook == None:
                logging.error('Webhook to send events is not provided. Please set it via "--webhook" argument or "ONETRIGGER_WEBHOOK" environment variable')
                required = False
        if required == False:
            sys.exit(1)

    def parse(self):
        config = self._parser.parse_args()
        self._check_config(config)
        return config

