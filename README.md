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

## Getting Auth set up
You need to have a Google API key in order for py-photomosaic to work.  Specifically, you need an Installed App ID.

https://developers.google.com/identity/protocols/OAuth2InstalledApp

1. Go to the API Library in the Google Dev Console
 1. https://console.developers.google.com/apis/library
1. You may have to select your project from the top-left, if you have multiple projects in the dev console.
1. Search for the Google Photos API.
1. Click to ENABLE
1. Click "Create Credentials"
1. Select the Photos library API, then Other UI for where you'll be calling the API from
1. You'll need to set up an OAuth consent screen.  The wizard will take you through it.
1. Download the client secret JSON file, and add it to your py-photomosaic project folder.  (Make sure it's named `client_secret.json`
1. When you first run the application, it'll pop open a web browser, and ask you to log in to Google and authorize the py-photomosaic app.
 1. When this is complete, a `credentials.json` file will appear in your project folder.
 
