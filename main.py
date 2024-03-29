import argparse
import datetime
import json
import os.path
import random
import pickle
from urllib import request
from urllib.request import urlretrieve
from numpy import dot
from numpy.linalg import norm

from googleapiclient.discovery import build
from httplib2 import Http
from oauth2client import client, tools
from oauth2client.file import Storage
from PIL import Image, ImageFilter

DEFAULT_MAXLIBRARYSIZE = 10000
DEFAULT_TILEWIDTH = 150
DEFAULT_TARGETTILESWIDE = 100
DEFAULT_DEFINITION = 1

class LibraryImage():
    url = ""
    filename = ""
    color = [[]]
    media_item_id = ""
    
    def __init__(self, url, color, filename, media_item_id):
        self.url = url
        self.color = color
        self.filename = filename
        self.media_item_id = media_item_id

def prepare_flow(secrets_path, scope):
    # Grab settings from the client_secrets.json file provided by Google
    with open(secrets_path, 'r') as fp:
        obj = json.load(fp)

    # The secrets we need are in the 'web' node
    secrets = obj['installed'] # ['web']

    # Return a Flow that requests a refresh_token
    return client.OAuth2WebServerFlow(
        client_id=secrets['client_id'],
        client_secret=secrets['client_secret'],
        scope=scope,
        redirect_uri=secrets['redirect_uris'][0],
        access_type='offline',
        prompt='force')

def auth_to_service():
    SCOPES = 'https://www.googleapis.com/auth/photoslibrary.readonly'
    store = Storage('credentials.json')
    creds = store.get()
    if not creds or creds.invalid:
        #flow = prepare_flow('client_secret.json', SCOPES)
        flow = client.flow_from_clientsecrets('client_secret.json', SCOPES)
        #try:
        creds = tools.run_flow(flow, store)
            
        #except Exception as msg:
        #    print("EXCEPTION!:  " + msg)
    http=creds.authorize(Http())
    return build('photoslibrary', 'v1',http, static_discovery=False)

def build_image_library(service, libsize, tolib, fromlib):
    print("Building image library (MAX %d images)..." % (libsize))

    if fromlib is not None and fromlib != "":
        libfile = open(fromlib, 'rb')
        library = pickle.load(libfile)
        libfile.close()
        print("Loaded {0} library items from file {1}".format(len(library), fromlib))
    else:
        imagecount = 0
        library = []

        searchFilter = {
            "pageSize": 100,
            "filters": {
                "mediaTypeFilter": {"mediaTypes": ["PHOTO"]},
                "contentFilter": {"excludedContentCategories": ["RECEIPTS", "DOCUMENTS", "WHITEBOARDS", "SCREENSHOTS", "FOOD", "UTILITY", "FASHION", "CRAFTS", "ARTS", "HOUSES"]}
            }
        }
        request = service.mediaItems().search(body=searchFilter)

        foundfiles = {}

        while request is not None:
            results = request.execute()
            try:
                if 'mediaItems' in results:
                    for result in results['mediaItems']:
                        if result['filename'] not in foundfiles:
                            library.append(LibraryImage(result['baseUrl'], [[]], result['filename'], result['id']))
                            foundfiles[result['filename']] = True
                            
                            imagecount = imagecount + 1
                            if (imagecount % 100 == 0): print(str(imagecount) + " images found  == " + str(datetime.datetime.now()),end="\r")
            except:
                print("=== Error finding media items ===")
                pass

            if imagecount >= libsize: break

            searchFilter['pageToken'] = ''
            if 'nextPageToken' in results:
                searchFilter['pageToken'] = results['nextPageToken']
            else:
                break

            request = service.mediaItems().search(body=searchFilter)

        if tolib is not None and tolib != "":
            libfileto = open(tolib, 'wb')
            pickle.dump(library, libfileto)
            libfileto.close()

    return library

def load_resource(source):
    resfile = open(source, 'rb')
    resource = pickle.load(resfile)
    resfile.close()
    print("Loaded {0}x{1} resource from file {2}".format(len(resource), len(resource[0]), source))
    return resource

def save_resource(resource, destination):
    resfile = open(destination, 'wb')
    pickle.dump(resource, resfile)
    resfile.close()

def download_image_library(library, definition, service):
    print("\nDownloading missing images...")
    targetWidth, targetHeight = definition, definition
    scaleString = "=w%d-h%d-c" % (targetWidth, targetHeight)
    downloadList = []

    for libImage in library:
        if not os.path.isfile('libimages%dx%d/%s' % (definition, definition, libImage.filename)):
            downloadList.append(libImage)

    progress = 0
    errors = 0
    status = ()
    for libImage in downloadList:
        progress = progress + 1
        print("Downloading image %d of %d (%f %% complete) [%d errors (%f %%)]" % (progress, len(downloadList), (progress * 100 / len(downloadList)), errors, (errors * 100 / progress)),end="\r")
        try:
            (filename, headers) = urlretrieve(libImage.url + scaleString, 'libimages%dx%d/%s' % (definition, definition, libImage.filename))
        except Exception as e:
            errors = errors + 1
            print(":::  ERROR downloading " + libImage.filename)
            print(e) # + "\n\nURL: " + libImage.url + scaleString + "\n\nError msg:") # + str(e) + "\n\n  ===>>>  " + str(status[0] + " >>>" + str(status[1])))
            image_try_again = service.mediaItems().get(mediaItemId=libImage.media_item_id)
            try:
                if image_try_again is not None:
                    result = image_try_again.execute()
                    urlretrieve(result['baseUrl'] + scaleString,'libimages%dx%d/%s' % (definition, definition, libImage.filename))
                    print("Replacement successful")
            except Exception as e2:
                print("Couldn't download a replacement, either")


def tint_image(im, color):
    color_map = []
    for component in color:
        color_map.extend(int(component/255.0*i) for i in range(256))
    return im.point(color_map)

def find_image_colors(library, definition):
    index = 0
    for libItem in library:
        if libItem.color is None:
            pass
        try:
            img = Image.open('libimages%dx%d/%s' % (definition, definition, libItem.filename))
            pixelmap = [[(0, 0, 0) for i in range(definition)] for j in range(definition)]
            for x in range(definition):
                for y in range(definition):
                    pixelmap[x][y] = img.getpixel((x, y))

            if (type(pixelmap[0][0]) is list or len(pixelmap[0][0]) < 3):  # Check that we got a 3x tuple back, and not an array, which happens sometimes on gifs.
                print("Bad color read from library image.")
            else:
                library[index].color = pixelmap
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

enum_lib = {}

def is_color_matrix_similar(colormap1, colormap2, image, library):
    global enum_lib
    if len(enum_lib) == 0:
        i = 0
        for lib_image in library:
            enum_lib[lib_image.filename] = i
            i += 1

    # This really just looks to see if the image is next to the original library image.  They could be vastly different.  Need to do pixelmap comparisons instaead.
    if colormap1.filename == '': return False
    indexof_color = enum_lib[colormap1.filename]
    indexof_image = enum_lib[image.filename]

    if abs(indexof_color - indexof_image) <= 10: return True
    return False

def does_image_exist_in_radius(tileMap, imageName, radius, point, library):
    xmin = 0 if point[0] < radius else point[0] - radius
    ymin = 0 if point[1] < radius else point[1] - radius
    xmax = len(tileMap) if point[0] + radius > len(tileMap) else point[0] + radius
    ymax = len(tileMap[0]) if point[1] + radius > len(tileMap[0]) else point[1] + radius
    for x in range(xmin, xmax):
        for y in range(ymin, ymax):
            if tileMap[x][y].filename == imageName.filename:
                return True
            if is_color_matrix_similar(tileMap[x][y], tileMap[point[0]][point[1]], imageName, library): # Check for pictures that are almost identical.
                return True
    return False

def get_target_dimensions(sourceImg, tileswide):
    return (tileswide, int(tileswide * (sourceImg.height / sourceImg.width)))

def get_shuffled_library_subset(library, quantity):
    libsize = len(library)
    index_array = random.sample(range(libsize), quantity)

    newlib = [library[index] for index in index_array]
    return newlib
        

def find_closest_library_image(library, colors, tileMap, tileMapLocation, definition):
    closestDistance = 999999.0
    pickedImage = library[0]
    changed_picked_image = False

    for libraryImg in get_shuffled_library_subset(library, 7000): #library:
        distance = -0.01
        for x in range(definition):
            for y in range(definition):
                if not (len(colors) < definition or len(libraryImg.color) < definition):
                    try:
                        distance = distance + (((float(colors[x][y][0]) - float(libraryImg.color[x][y][0]))** 2.0) + ((float(colors[x][y][1]) - float(libraryImg.color[x][y][1]))** 2.0) + ((float(colors[x][y][2]) - float(libraryImg.color[x][y][2]))** 2.0))**(0.5)
                    except:
                        print("ERROR trying to find distance.  LibraryImg.color:  " + str(libraryImg.color) + "   >> COLORS: "+ str(colors))
        
        distance = distance / definition
        if distance >= 0 and distance < closestDistance and not does_image_exist_in_radius(tileMap, libraryImg, 5, tileMapLocation, library):
            closestDistance = distance
            pickedImage = libraryImg
            changed_picked_image = True
            
    if not changed_picked_image:
        print("============ NEVER CHANGED THE PICK IMAGE =================")
    return pickedImage

def build_tile_map(sourceImg, library, targetDimensions, definition):
    tileMap = [[LibraryImage("", [[]], "", "") for i in range(targetDimensions[1])] for j in range(targetDimensions[0])]
    tileMapSequence = get_randomized_tile_map(targetDimensions[0], targetDimensions[1])
    sourceImg = sourceImg.resize((targetDimensions[0] * definition, targetDimensions[1] * definition))

    print("\nPicking tiles...")
    progress = 0
    for tile in tileMapSequence:
        print("Picking tile %d of %d (%f %% complete)" % (progress, len(tileMapSequence), (progress * 100 / len(tileMapSequence))),end="\r")
        x = tile[0][0] #x-value from the tile
        y = tile[0][1]  #y-value from the tile
        nextcolor = [[(0,0,0) for n in range(definition)] for m in range(definition)]
        for i in range(definition):
            for j in range(definition):
                nextcolor[i][j] = sourceImg.getpixel(((tile[0][0] * definition) + i, (tile[0][1] * definition) + j))

        pickedImage = find_closest_library_image(library, nextcolor, tileMap, tile[0], definition)
        tileMap[x][y] = pickedImage
        progress = progress + 1
    
    return tileMap

def repick_missing_images(imageErrors, sourceImg, library, targetDimensions, definition):
    return []

def download_required_images(tileMap, tileSize, service):
    print("\nDownloading any missing picked images...")
    imagesToDownload = []
    for x in range(len(tileMap)):
        for y in range(len(tileMap[0])):
            if not os.path.isfile("sourceimages%dx%d/%s" % (tileSize, tileSize, tileMap[x][y].filename)):
                imagesToDownload.append(tileMap[x][y])
    
    imagesToDownload = list(set(imagesToDownload))
    progress = 0
    imageErrors = []
    for image in imagesToDownload:
        print("Downloading image %d of %d (%f %% complete)" % (progress, len(imagesToDownload), (progress * 100 / len(imagesToDownload))),end="\r")
        try:
            urlretrieve("%s=w%d-h%d-c" % (image.url, tileSize, tileSize), ("sourceimages%dx%d/%s" % (tileSize, tileSize, image.filename)))
        except Exception as e:
            print(":::  ERROR downloading " + image.filename)
            #print(">>>>>    " + image.url)
            try:
                image_try_again = service.mediaItems().get(mediaItemId=image.media_item_id)
                if image_try_again is not None:
                    result = image_try_again.execute()
                    urlretrieve("%s=w%d-h%d-c" % (result['baseUrl'], tileSize, tileSize), ("sourceimages%dx%d/%s" % (tileSize, tileSize, image.filename)))
                    print("Replacement successful")
            except Exception as e2:
                print("Couldn't download a replacement, either")

            print(e)
            imageErrors.append(image)
        progress = progress + 1
    return imageErrors

def build_final_image(library, tileMap, sourceImg, targetDimensions, tileSize, output):
    print("\nStitching together the final image...")
    finalImage = Image.new("RGB", (targetDimensions[0] * tileSize, targetDimensions[1] * tileSize))

    progress = 0
    for x in range(targetDimensions[0]):
        for y in range(targetDimensions[1]):
            try:
                print("Placing tile %d of %d (%f %% complete)" % (progress, (targetDimensions[0] * targetDimensions[1]), (progress * 100 / (targetDimensions[0] * targetDimensions[1]))),end="\r")
                pickImg = Image.open("sourceimages%dx%d/%s" % (tileSize, tileSize, tileMap[x][y].filename))
                imgcopy = pickImg.copy()
                #imgcopy = tint_image(imgcopy, tileMap[x][y].color)
                finalImage.paste(imgcopy, (x * tileSize, y * tileSize))
            except:
                pass
            progress = progress + 1

    finalImage.save(output)

def setup_args():
    parser = argparse.ArgumentParser("Py-Photomosaic -- A Python Photomosaic Generator")
    parser.add_argument("-s", "--source", default="source.jpg", help="Input file for the source image used to build the mosaic. (default source.jpg)")
    parser.add_argument("-o", "--output", default="output.jpg", help="Output file for generated photomosaic (default output.jpg)")
    parser.add_argument("-l", "--libsize", type=int, default=DEFAULT_MAXLIBRARYSIZE, help="Maximum size of an image library to attempt to identify (default %d images).  Lower this to reduce number of files needed to download from Google." % (DEFAULT_MAXLIBRARYSIZE))
    parser.add_argument("-w", "--targetwidth", type=int, default=DEFAULT_TARGETTILESWIDE, help="Target width IN TILES, not pixels, for the final image. (default %d)" % (DEFAULT_TARGETTILESWIDE))
    parser.add_argument("-z", "--tilesize", type=int, default=DEFAULT_TILEWIDTH, help="Size of the tiles, in pixels.  Tiles will be squared, so a value of 150 would produce 150x150 tile sizes. (default %d)" % (DEFAULT_TILEWIDTH))
    parser.add_argument("-d", "--definition", type=int, default=DEFAULT_DEFINITION, help="What level of definition should be used in mapping tiles to source image.  Higher numbers provide higher defintion. (default %d)" % (DEFAULT_DEFINITION))
    parser.add_argument("-v", "--savelibto", default="", help="What file name to save the library to, if you want to re-use the library. (default, empty string - won't save)")
    parser.add_argument("-f", "--loadlibfrom", default="", help="What file name to load the library from, if you want to re-use the library. (default empty string - won't load)")
    parser.add_argument("-t", "--tileinfile", default="", help="What file name to load the tile map from, if you want to re-use the tile map. (default, empty string - won't load)")
    parser.add_argument("-u", "--tileoutfile", default="", help="What file name to save the tile map to, if you want to re-use the tile map. (default empty string - won't save)")
    return parser.parse_args()

def main():
    args = setup_args()
    sourceImg = Image.open(args.source)
    targetDimensions = get_target_dimensions(sourceImg, args.targetwidth)
    print("Target dimensions (in tiles): " + str(targetDimensions))
    if not os.path.isdir('libimages%dx%d' % (args.definition, args.definition)):
        os.mkdir('libimages%dx%d' % (args.definition, args.definition))
    if not os.path.isdir('sourceimages%dx%d' % (args.tilesize, args.tilesize)):
        os.mkdir('sourceimages%dx%d' % (args.tilesize, args.tilesize))
    service = auth_to_service()
    library = build_image_library(service, args.libsize, args.savelibto, args.loadlibfrom)
    download_image_library(library, args.definition, service)
    library = find_image_colors(library, args.definition)

    if (args.savelibto is not None and args.savelibto != ""):
        save_resource(library, args.savelibto)

    if (args.tileinfile is None or args.tileinfile == ""):
        tileMap = build_tile_map(sourceImg, library, targetDimensions, args.definition)
        if (args.tileoutfile is not None and args.tileoutfile != ""):
            save_resource(tileMap, args.tileoutfile)
    else:
        tileMap = load_resource(args.tileinfile)

    imageErrors = download_required_images(tileMap, args.tilesize, service)
    while len(imageErrors) > 0:
        imageErrors = repick_missing_images(imageErrors, sourceImg, library, targetDimensions, args.definition)
    build_final_image(library, tileMap, sourceImg, targetDimensions, args.tilesize, args.output)

if __name__ == '__main__':
    main()
