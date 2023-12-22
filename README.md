# django-peertube-runner-connector: A django application to connect to a peertube runner and transcode videos 

[![Python version](https://img.shields.io/badge/Python-3.10%20|%203.11%20|%203.12-blue.svg)](https://www.python.org/)
[![Django version](https://img.shields.io/badge/Django-4.2%20|%205.0%20-green.svg)](https://www.djangoproject.com/)
[![CircleCI](https://circleci.com/gh/openfun/django-peertube-runner-connector/tree/main.svg?style=svg)](https://circleci.com/gh/openfun/django-peertube-runner-connector/tree/main)

## Overview 
django-peertube-runner-connector is designed to use [Peertube](https://github.com/Chocobozzz/PeerTube/) transcoding runners outside of Peertube App. It implements a set of endpoints with [Django Rest Framework](https://www.django-rest-framework.org/) and a [SocketIO](https://python-socketio.readthedocs.io/en/latest/) server that allow runners to request jobs, updated job status, download media files and upload the transcoded media files. It provides a function that can be used by your app that will launch the transcoding process.

To make use of the SocketIO server, this app only work in ASGI.


## Architecture

### Runner API

This part will interact with Peertube runners. It is not designed to be used by a user as it reproduces what the Peertube App is doing in order to manage runners / jobs.


#### Runner Behavior

Jobs are stored in a Database, and runners hit the `/request` endpoint to get the available jobs to transcode.


### The transcode video function

The function receives a video file and a name, and then creates transcoding jobs for it.

We use function `probe` of [python-ffmpeg](https://github.com/kkroening/ffmpeg-python) library, to get a thumbnail and all the necessary metadata to create transcoding jobs. Once the jobs are created, the WebSocket server emits an event to inform runners of a new pending jobs.


#### Job implementation

Currently we didn't implement all the transcoding jobs the runner can do. We are planning to implement more jobs in the future. For now, the API only implements the following jobs:

- [x] HLS transcoding
- [ ] VOD web video transcoding
- [ ] Live transcoding
- [ ] VOD audio merge transcoding
- [ ] Video Studio transcoding

Theses jobs are created and handled through their respective classes in `api.transcoding.utils.job_handlers` directory. Some of them are already almost implemented but are not used, so they are commented.

### SocketIO server

The SocketIO server is used to communicate with runners. It is only used to inform runners of new jobs, thus, make this part very simple. It implements only one function that emits the event `available-jobs` to runners when a new job is created. Once a runner receives this event, it will hit the `/request` endpoint in the Runner API to get the new job.

## Installation

Once you have installed the library, you will need to setup your project to use it (see [configuration](#configuration) part). You can find a demo application in the `tests` directory.

### PyPi

To install the library with pip, enter the following command:

```shell
pip install django-peertube-runner-connector
```

### Local
To install the library locally, enter the following commands at the root of the project:

build the library:
```shell
python setup.py sdist bdist_wheel
```

This should create a ``dist`` directory with the library files.

Then you can go in your application, source your virtual environment and install the library with pip:
```shell
pip install /path/to/django-peertube-runner-connector/dist/django_peertube_runner_connector-1.tar
```

## Setup

### Configuration


```python
# settings.py
INSTALLED_APPS = [
    # ...
    "rest_framework",
    "django_peertube_runner_connector.apps.DjangoPeertubeRunnerConnectorConfig",
    "storages", # optional django-storages library
]

# Transcoding resolution settings
TRANSCODING_ALWAYS_TRANSCODE_ORIGINAL_RESOLUTION = False
TRANSCODING_RESOLUTIONS_144P = False
TRANSCODING_RESOLUTIONS_240P = False
TRANSCODING_RESOLUTIONS_360P = True
TRANSCODING_RESOLUTIONS_480P = True
TRANSCODING_RESOLUTIONS_720P = True
TRANSCODING_RESOLUTIONS_1080P = False
TRANSCODING_RESOLUTIONS_1440P = False
TRANSCODING_RESOLUTIONS_2160P = False

# Transcoding fps settings
TRANSCODING_FPS_MIN = 1
TRANSCODING_FPS_STANDARD = [24, 25, 30]
TRANSCODING_FPS_HD_STANDARD = [50, 60]
TRANSCODING_FPS_AUDIO_MERGE = 25
TRANSCODING_FPS_AVERAGE = 30
TRANSCODING_FPS_MAX = 60
TRANSCODING_FPS_KEEP_ORIGIN_FPS_RESOLUTION_MIN = 720

# Max number of times a job can fail before being marked as failed
TRANSCODING_RUNNER_MAX_FAILURE = 5

# The callback path to a function that will be called when a video transcoding ended
TRANSCODING_ENDED_CALLBACK_PATH = ""

# The django-peertube-runner-connector app uses the django storage system to store the transcoded videos.
# It uses the "videos" storage where you can configure the storage backend you want to use.
STORAGES = {
    "default": {
        "BACKEND": "django.core.files.storage.FileSystemStorage",
    },
    "videos": {  # This is the storage used to store the transcoded videos
        "BACKEND": "app.storage.MyCustomFileSystemVideoStorage", # You can use the storage backend you want
    },
    "staticfiles": {
        "BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage",
    },
}
```


#### Storage

Django-peertube-runner-connector uses the django storage system to store the transcoded videos. It uses the "videos" storage where you can configure the storage backend you want to use. To use an S3 like storage, you can use the [django-storages](https://django-storages.readthedocs.io/en/latest/) library. Here is an example of a custom storage backend that uses the S3 storage:

```python
# app/storage.py
from storages.backends.s3boto3 import S3Boto3Storage


class MyS3VideoStorage(S3Boto3Storage):
  """Custom S3 storage class."""

  bucket_name = "my-bucket"
```

then you can use it in your settings:

```python
# settings.py

# ... S3 settings

STORAGES = {
    "default": {
        "BACKEND": "django.core.files.storage.FileSystemStorage",
    },
    "videos": {  
        "BACKEND": "app.storage.MyS3VideoStorage", # Your custom storage backend
    },
    "staticfiles": {
        "BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage",
    },
}
```

#### Server

To make use of the SocketIO server, you need to have ASGi server like [uvicorn](https://www.uvicorn.org/).

Here is an example on how to configure your asgi server to use the SocketIO server:


```python
from configurations.asgi import get_asgi_application

django_asgi_app = get_asgi_application()


# its important to make all other imports below this comment
import socketio 

from django_peertube_runner_connector.socket import sio 


application = socketio.ASGIApp(sio, django_asgi_app)

```

Add the runners api views to your urls:

```python
# urls.py
from django_peertube_runner_connector.urls import (
    urlpatterns as django_peertube_runner_connector_urls,
)

urlpatterns += django_peertube_runner_connector_urls
```

If your application is distributed on multiple servers, you will probably need
to use a message queue. We manage redis and redis sentinel manager. For this,
you have to define this settings

#### Redis sentinel

- `DJANGO_PEERTUBE_RUNNER_CONNECTOR_SENTINELS`: A list of sentinel nodes. 
Each node is represented by a pair (hostname, port). Example: [('localhost', 26379)]
- `DJANGO_PEERTUBE_RUNNER_CONNECTOR_SENTINELS_MASTER`: The master sentinel name. Example: mymaster

#### Redis

- `DJANGO_PEERTUBE_RUNNER_CONNECTOR_REDIS`: The redis url. Example: `redis://localhost:6379`

Voilà! Your server should be ready!


### Demo application

For testing purpose, you can find a basic django app using the django-peertube-runner-connector library in the `tests` directory. You use run it with the following commands:

Create your virtual environment:
```shell
python -m venv env
source env/bin/activate
```

Install the dependencies:
```shell
pip install -e ."[dev]"
```

Go to the tests directory:
```shell
cd tests
```

Create the database and run the migrations:
```shell
python manage.py migrate
```

Collect the static files:
```shell
python manage.py collectstatic
```

Create a super user:
```shell
python manage.py createsuperuser
```

Launch the server with an asgi server like uvicorn:
```shell
python -m uvicorn app.asgi:application --reload
```

Once the server is running, you can register your server to a peertube runner. 

#### Registering a Peertube runner

First you will to generate a registration token. To do so, use the following command and keep the registrationToken for late:
```shell
python tests/manage.py create_runner_registration_token
```

First you will need a Peertube runner. To launch one, follow the instructions (theses instructions are made by me and for development purpose only)

Clone and go to the [peertube repository](https://github.com/Chocobozzz/PeerTube)
```shell
git clone https://github.com/Chocobozzz/PeerTube
```
```shell
cd PeerTube
```

Install the dependencies
```shell
cd apps/peertube-runner
npm install
cd ../../
```
Build the runner
```shell
npm run build:peertube-runner
```

Launch the runner
```shell
./apps/peertube-runner/dist/peertube-runner.js server
```

Open a new terminal in the same directory and register your runner to your django app
```shell
./apps/peertube-runner/dist/peertube-runner.js register --url http://localhost:8000 --registration-token $MY_TOKEN --runner-name transcode-api
```

#### Created a transcoding jobs and receive the transcoded video

You can now launch a transcoding job with using the ``http://127.0.0.1:8000/videos/upload`` end point of the django app by sending a multipart/form-data request with your file as the value of the ``videoFile`` key. This video view is given by the test app not by the django-peertube-runner-connector app. This should population a directory named ``video-[uuid]`` in the root of the project with the result of the transcoding job.

### Launch test

To launch the tests, enter the following commands at the root of the project:

Create your virtual environment:
```shell
python -m venv env
source env/bin/activate
```

Install the dependencies:
```shell
pip install -e ."[dev]"
```

Launch the tests:
```shell
make test
```


## License

This work is released under the MIT License (see [LICENSE](./LICENSE)).