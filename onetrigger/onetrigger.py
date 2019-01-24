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
 
import logging, sys, signal
from onetrigger.configparser import ConfigParser
from onetrigger.oneproviderclient import OneproviderClient


class OneTrigger:

    def __init__(self):
        self._config_logging()
        self._set_sig_handlers()
        self._config = ConfigParser().parse()
        self._oneprovider_client = OneproviderClient(self._config)

    def _config_logging(self):
        LOGGING_FORMAT = '%(asctime)s - %(levelname)s - %(message)s'
        logging.basicConfig(format=LOGGING_FORMAT, level=logging.INFO)

    def _set_sig_handlers(self):
        def sig_handler(sig, frame):
            logging.info('Closing OneTrigger... Bye!')
            sys.exit(0)
        for sig in (signal.SIGINT, signal.SIGTERM):
            signal.signal(sig, sig_handler)

    def _run(self):
        self._oneprovider_client.run()

    def _list_spaces(self):
        self._oneprovider_client.list_spaces()

    def main(self):
        {
            'run': self._run,
            'list-spaces': self._list_spaces
        }[self._config.command]()

def main():
    OneTrigger().main()

if __name__ == '__main__':
    main()