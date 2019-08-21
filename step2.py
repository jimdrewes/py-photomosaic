# In this step, we're going to start building the build_image_library() function.
# To do this, we need to see if we can get a list of images from a Google Photos library.
# Google Photos can be accessed through the Python Google API library:
#   https://github.com/googleapis/google-api-python-client
# Library documentation is here:
#   https://developers.google.com/photos/library/reference/rest/
# Python Google OAuth specific docs can be found here:
#   https://github.com/googleapis/google-api-python-client/blob/master/docs/oauth.md

from httplib2 import Http
from oauth2client import client, tools
from oauth2client.file import Storage
from apiclient.discovery import build

def auth_to_service():
    SCOPES = 'https://www.googleapis.com/auth/photoslibrary.readonly'
    store = Storage('credentials.json')
    creds = store.get()
    if not creds or creds.invalid:
        flow = client.flow_from_clientsecrets('client_secret.json', SCOPES)
        creds = tools.run_flow(flow, store)
    return build('photoslibrary', 'v1', http=creds.authorize(Http()))

def build_image_library():
    service = auth_to_service()
    request = service.mediaItems().search()
    result = request.execute()
    return result

def main():
    library = build_image_library()
    # find_image_colors()
    # open_source_image()
    # build_tile_map()
    # build_final_image()

    print(library)

if __name__ == '__main__':
    main()