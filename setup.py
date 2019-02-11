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

from setuptools import setup, find_namespace_packages

# Load readme
with open('README.md', mode='r', encoding='utf-8') as f:
    readme = f.read()

# Load version
with open('onetrigger/version.py', mode='r', encoding='utf-8') as f:
    exec(f.read())

setup(name='onetrigger',
      version=__version__,
      description='Trigger webhooks by Onedata events',
      long_description=readme,
      long_description_content_type='text/markdown',
      url='https://github.com/grycap/onetrigger',
      author='GRyCAP - Universitat Politecnica de Valencia',
      author_email='serisgal@i3m.upv.es',
      license='Apache 2.0',
      packages=find_namespace_packages(),
      install_requires=['requests', 'tabulate'],
      entry_points={
          'console_scripts': [
              'onetrigger=onetrigger.onetrigger:main'
          ]
      },
      classifiers=[
          'Programming Language :: Python :: 3',
          'License :: OSI Approved :: Apache Software License',
          'Environment :: Console'
      ],
      zip_safe=False)
