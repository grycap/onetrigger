# OneTrigger

[![Docker Build Status](https://img.shields.io/docker/cloud/build/grycap/onetrigger.svg)](https://hub.docker.com/r/grycap/onetrigger/) [![Build Status](https://travis-ci.org/grycap/onetrigger.svg?branch=master)](https://travis-ci.org/grycap/onetrigger) [![PyPi version](https://img.shields.io/pypi/v/onetrigger.svg)](https://pypi.org/project/onetrigger/) [![License](https://img.shields.io/badge/license-Apache%202-blue.svg)](https://www.apache.org/licenses/LICENSE-2.0)

A command-line tool to detect Onedata file events in order to trigger a webhook.

## Installation

OneTrigger requires `python3` and the `python3-pip` tool. A package is available at the Python Package Index (PyPI) under the name `onetrigger`, so you can easily install it executing:

```bash
pip3 install onetrigger
```

You can also download a binary in the [releases](https://github.com/grycap/onetrigger/releases) section.

## Usage

Parameters can be passed via arguments or environment variables. All available commands and his parameters are described below:

### Command `run`

Subscribe to file events.

| Argument                             | Environment variable   | Description                                                                       |
|--------------------------------------|------------------------|-----------------------------------------------------------------------------------|
| `-H HOST`, `--oneprovider-host HOST` | `ONEPROVIDER_HOST`     | Oneprovider hostname or IP.                                                       |
| `-t TOKEN`, `--token TOKEN`          | `ONEDATA_ACCESS_TOKEN` | Onedata access token.                                                             |
| `-s SPACE`, `--space SPACE`          | `ONEDATA_SPACE`        | Onedata space.                                                                    |
| `-w WEBHOOK`, `--webhook WEBHOOK`    | `ONETRIGGER_WEBHOOK`   | Webhook to send events.                                                           |
| `-f FOLDER`, `--folder FOLDER`       | `ONEDATA_SPACE_FOLDER` | Folder to listen events (Optional).                                               |
| `-i`, `--insecure`                   | `ONEPROVIDER_INSECURE` | Connect to a provider without a trusted certificate (Optional). Default: `False`. |

### Command `list-spaces`

List your available spaces in Oneprovider.

| Argument                             | Environment variable   | Description                                                                       |
|--------------------------------------|------------------------|-----------------------------------------------------------------------------------|
| `-H HOST`, `--oneprovider-host HOST` | `ONEPROVIDER_HOST`     | Oneprovider hostname or IP.                                                       |
| `-t TOKEN`, `--token TOKEN`          | `ONEDATA_ACCESS_TOKEN` | Onedata access token.                                                             |
| `-i`, `--insecure`                   | `ONEPROVIDER_INSECURE` | Connect to a provider without a trusted certificate (Optional). Default: `False`. |

### Examples

#### Subscribing to file events

```bash
onetrigger run -H example.com -t xxxxx -s my-onedata-space -w http://example.com/webhook -f my-folder
```

#### Deploy on Kubernetes

OneTrigger can be deployed on Kubernetes using our public Docker Hub image [grycap/onetrigger](https://hub.docker.com/r/grycap/onetrigger) by applying a YAML file like this:

```yaml
apiVersion: apps/v1beta1
kind: Deployment
metadata:
  name: onetrigger
spec:
  replicas: 1
    spec:
      containers:
      - name:  onetrigger
        image: grycap/onetrigger:latest
        imagePullPolicy: Always
        env:
        - name: ONEPROVIDER_HOST
          value: "example.com"
        - name: ONEDATA_ACCESS_TOKEN
          value: "xxxxx"
        - name: ONEDATA_SPACE
          value: "my-onedata-space"
        - name: ONETRIGGER_WEBHOOK
          value: "http://example.com/webhook"
        - name: ONEDATA_SPACE_FOLDER
          value: "my-folder"
```

## Event format

When a new file is created inside the space (or the specified folder) a JSON formatted event is sent to the webhook following the structure of the example shown below:

```json
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
```
