# Here we'll randomize the sequence in which tiles are selected, in order to prevent blocking.

from httplib2 import Http
from oauth2client import client, tools
from oauth2client.file import Storage
from apiclient.discovery import build
from urllib import request
from urllib.request import urlretrieve
from PIL import Image, ImageFilter
import datetime
import os.path
import random

MAXLIBRARYSIZE = 3000
TILEWIDTH = 150
TILEHEIGHT = 150
TARGETTILESWIDE = 50

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

def get_randomized_tile_map(width, height):
    tileMapSequence = []
    print("\nRandomizing tile map plan...")
    for x in range(width):
        for y in range(height):
            tileMapSequence.append(((x,y), ""))
    
    for index in range(0, len(tileMapSequence)):
        sourcetile = tileMapSequence[index]
        randindex = random.randint(0, len(tileMapSequence) - 1)
        randtile = tileMapSequence[randindex]
        tileMapSequence[index] = randtile
        tileMapSequence[randindex] = sourcetile

    return tileMapSequence

def does_image_exist_in_radius(tileMap, imageName, radius, point):
    xmin = 0 if point[0] < radius else point[0] - radius
    ymin = 0 if point[1] < radius else point[1] - radius
    xmax = len(tileMap) if point[0] + radius > len(tileMap) else point[0] + radius
    ymax = len(tileMap[0]) if point[1] + radius > len(tileMap[0]) else point[1] + radius
    for x in range(xmin, xmax):
        for y in range(ymin, ymax):
            if tileMap[x][y].filename == imageName:
                return True
    return False

def get_target_dimensions(sourceImg):
    return (TARGETTILESWIDE, int(TARGETTILESWIDE * (sourceImg.height / sourceImg.width)))

def find_closest_library_image(library, color, tileMap, tileMapLocation):
    closestDistance = 9999.0
    pickedImage = library[0]

    for libraryImg in library:
        distance = (((float(color[0]) - float(libraryImg.color[0]))** 2.0) + ((float(color[1]) - float(libraryImg.color[1]))** 2.0) + ((float(color[2]) - float(libraryImg.color[2]))** 2.0))**(0.5)
        if distance < closestDistance and not does_image_exist_in_radius(tileMap, libraryImg.filename, 5, tileMapLocation):
            closestDistance = distance
            pickedImage = libraryImg
            
    return pickedImage

def build_tile_map(sourceImg, library, targetDimensions):
    tileMap = [[LibraryImage("", (0,0,0), "") for i in range(targetDimensions[1])] for j in range(targetDimensions[0])]
    tileMapSequence = get_randomized_tile_map(targetDimensions[0], targetDimensions[1])
    sourceImg = sourceImg.resize((targetDimensions[0], targetDimensions[1]))

    print("\nPicking tiles...")
    progress = 0
    for tile in tileMapSequence:
        print("Picking tile %d of %d (%f %% complete)" % (progress, len(tileMapSequence), (progress * 100 / len(tileMapSequence))),end="\r")
        x = tile[0][0] #x-value from the tile
        y = tile[0][1] #y-value from the tile
        nextcolor = sourceImg.getpixel(tile[0])
        pickedImage = find_closest_library_image(library, nextcolor, tileMap, tile[0])
        tileMap[x][y] = pickedImage
        progress = progress + 1
    
    return tileMap

def download_required_images(tileMap):
    print("\nDownloading any missing picked images...")
    imagesToDownload = []
    for x in range(len(tileMap)):
        for y in range(len(tileMap[0])):
            if not os.path.isfile('sourceimages/' + tileMap[x][y].filename):
                imagesToDownload.append(tileMap[x][y])
    
    imagesToDownload = list(set(imagesToDownload))
    progress = 0
    for image in imagesToDownload:
        print("Downloading image %d of %d (%f %% complete)" % (progress, len(imagesToDownload), (progress * 100 / len(imagesToDownload))),end="\r")
        try:
            urlretrieve("%s=w%d-h%d-c" % (image.url, TILEWIDTH, TILEHEIGHT), 'sourceimages/' + image.filename)
        except:
            print(":::  ERROR downloading " + image.filename)
        progress = progress + 1

def build_final_image(library, tileMap, sourceImg, targetDimensions):
    print("\nStitching together the final image...")
    finalImage = Image.new("RGB", (targetDimensions[0] * TILEWIDTH, targetDimensions[1] * TILEHEIGHT))

    progress = 0
    for x in range(targetDimensions[0]):
        for y in range(targetDimensions[1]):
            try:
                print("Placing tile %d of %d (%f %% complete)" % (progress, (targetDimensions[0] * targetDimensions[1]), (progress * 100 / (targetDimensions[0] * targetDimensions[1]))),end="\r")
                pickImg = Image.open('sourceimages/' + tileMap[x][y].filename)
                finalImage.paste(pickImg, (x * TILEWIDTH, y * TILEHEIGHT))
            except:
                pass
            progress = progress + 1

    finalImage.save("output.jpg")

def main():
    library = build_image_library()
    library = download_image_library(library)
    library = find_image_colors(library)
 
    sourceImg = Image.open('source.jpg')
    targetDimensions = get_target_dimensions(sourceImg)
    print("Target dimensions (in tiles): " + str(targetDimensions))

    tileMap = build_tile_map(sourceImg, library, targetDimensions)
    download_required_images(tileMap)
    build_final_image(library, tileMap, sourceImg, targetDimensions)

if __name__ == '__main__':
    main()