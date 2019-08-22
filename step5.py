# In this step, we're going to download all of the library images, so we can evaluate their color.
# Don't forget to create the images directory

from httplib2 import Http
from oauth2client import client, tools
from oauth2client.file import Storage
from apiclient.discovery import build
from urllib import request
from urllib.request import urlretrieve
import datetime

MAXLIBRARYSIZE = 1000

class LibraryImage():
    url = ""
    filename = ""
    color = (0, 0, 0)
    
    def __init__(self, url, color, filename):
        self.url = url
        self.color = color
        self.filename = filename

def auth_to_service():
    SCOPES = 'https://www.googleapis.com/auth/photoslibrary.readonly'
    store = Storage('credentials.json')
    creds = store.get()
    if not creds or creds.invalid:
        flow = client.flow_from_clientsecrets('client_secret.json', SCOPES)
        creds = tools.run_flow(flow, store)
    return build('photoslibrary', 'v1', http=creds.authorize(Http()))

def build_image_library():
    print("Building image library (MAX %d images)..." % (MAXLIBRARYSIZE))
    imagecount = 0
    library = []

    service = auth_to_service()
    
    searchFilter = {
        "pageSize": 100,
        "filters": {
            "mediaTypeFilter": {"mediaTypes": ["PHOTO"]},
            "contentFilter": {"excludedContentCategories": ["RECEIPTS", "DOCUMENTS", "WHITEBOARDS", "SCREENSHOTS"]}
        }
    }
    request = service.mediaItems().search(body=searchFilter)

    while request is not None:
        results = request.execute()
        for result in results['mediaItems']:
            library.append(LibraryImage(result['baseUrl'], (0,0,0), result['filename']))
            
            imagecount = imagecount + 1
            if (imagecount % 100 == 0): print(str(imagecount) + " images found  == " + str(datetime.datetime.now()),end="\r")

        if imagecount >= MAXLIBRARYSIZE: break

        searchFilter['pageToken'] = ''
        if results['nextPageToken']:
            searchFilter['pageToken'] = results['nextPageToken']

        request = service.mediaItems().search(body=searchFilter)

    return library

def download_image_library(library):
    print("\nDownloading %d library images..." % len(library))

    progress = 0
    for libImage in library:
        print("Downloading image %d of %d (%f %% complete)" % (progress, len(library), (progress * 100 / len(library))),end="\r")
        urlretrieve(libImage.url, 'images/' + libImage.filename)
        progress = progress + 1


def main():
    library = build_image_library()
    download_image_library(library)
    # find_image_colors()
    # open_source_image()
    # build_tile_map()
    # build_final_image()

if __name__ == '__main__':
    main()