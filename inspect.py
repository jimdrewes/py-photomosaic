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


def load_resource(source):
    resfile = open(source, 'rb')
    resource = pickle.load(resfile)
    resfile.close()
    #print("Loaded {0}x{1} resource from file {2}".format(len(resource), len(resource[0]), source))
    return resource

def save_resource(resource, destination):
    resfile = open(destination, 'wb')
    pickle.dump(resource, resfile)
    resfile.close()


def main():
    tilemap = load_resource('quality100_6_tile_map.lib')

if __name__ == '__main__':
    main()
