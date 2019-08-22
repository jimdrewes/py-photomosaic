# In this step, we're going to add the images found into a library object.
# To do this, we add a LibraryImage class, and iterate through the results to add instances of that class to a list.

from httplib2 import Http
from oauth2client import client, tools
from oauth2client.file import Storage
from apiclient.discovery import build

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
    library = []

    service = auth_to_service()
    request = service.mediaItems().search()
    results = request.execute()

    for result in results['mediaItems']:
        library.append(LibraryImage(result['baseUrl'], (0,0,0), result['filename']))

    return library

def main():
    library = build_image_library()
    # find_image_colors()
    # open_source_image()
    # build_tile_map()
    # build_final_image()

    print(library)

if __name__ == '__main__':
    main()