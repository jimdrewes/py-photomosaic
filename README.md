# py-photomosaic
Python-based photomosaic generator with Google Photos connectivity

## Pre-Requirements
py-photomosaic assumes a few pre-requirements:
1. Python v3
1. A Google Photos account filled with 1,000 or more images to use as library images

## Getting Started
Start by cloning the repository to get the latest version.

`git clone https://github.com/jimdrewes/py-photomosaic.git`

**To access the code used in the "Building a Photomosaic Generator in Python" presentation:**
Pull from the `presentation-v1.0` tag

`git checkout tags/presentation-v1.0 -b presentation`

Next, install the required Python libraries.
* httplib2
  * `pip install httplib2`
* oauth2client
  * `pip install oauth2client`
* apiclient
  * `pip install apiclient`
* Google API client for Python (apiclient.discovery)
  * `pip install --upgrade google-api-python-client`
* Pillow (PIL)
  * `pip install Pillow`
