# In this step, we're going to evaluate the colors of the images in the library,
# and store them in some kind of data structure.

from httplib2 import Http
from oauth2client import client, tools
from oauth2client.file import Storage
from apiclient.discovery import build
from urllib import request
from urllib.request import urlretrieve
from PIL import Image, ImageFilter
import datetime
import os.path

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
    print("\nDownloading missing images...")
    targetWidth, targetHeight = 1, 1
    scaleString = "=w%d-h%d-c" % (targetWidth, targetHeight)
    downloadList = []

    for libImage in library:
        if not os.path.isfile('images/' + libImage.filename):
            downloadList.append(libImage)

    progress = 0
    for libImage in downloadList:
        print("Downloading image %d of %d (%f %% complete)" % (progress, len(downloadList), (progress * 100 / len(downloadList))),end="\r")
        try:
            urlretrieve(libImage.url + scaleString, 'images/' + libImage.filename)
        except:
            print(":::  ERROR downloading " + libImage.filename)
            downloadList.remove(libImage)
        progress = progress + 1
    
    return library

def find_image_colors(library):
    index = 0
    for libItem in library:
        try:
            img = Image.open('images/' + libItem.filename)
            pixel = img.getpixel((0, 0))
            library[index].color = pixel
        except:
            pass

        index = index + 1

    return library


def main():
    library = build_image_library()
    library = download_image_library(library)
    library = find_image_colors(library)
    # open_source_image()
    # build_tile_map()
    # build_final_image()
    print(library[0].color)

if __name__ == '__main__':
    main()