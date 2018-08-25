from typing import Tuple
import ssl
from flask import Blueprint, send_file, request
from flask_cors import cross_origin
from functools import lru_cache
import hashlib
import io
from PIL import Image
import urllib.request

from utilities import urlDecode

imageFetcher = Blueprint('imageFetcher', __name__)
ssl._create_default_https_context = ssl._create_unverified_context


@lru_cache(1000)
def strHash(string):
    # https://gist.github.com/nmalkin/e287f71788c57fd71bd0a7eec9345add
    return hashlib.sha256(string.encode('utf-8')).hexdigest()


def imageResize(image: Image, size: Tuple[int, int]) -> Image:
    return image.resize(size, Image.ANTIALIAS)


def getImageFromNetwork(url: str) -> Image:
    headers = {
        'User-Agent': 'Mozilla/5.0 (compatible; MSIE 10.0; Macintosh; Intel Mac OS X 10_7_3; Trident/6.0)'
    }
    res = urllib.request.urlopen(urllib.request.Request(url, headers=headers))
    img = Image.open(io.BytesIO(res.read()))
    return img


memcache = {}


def getImageFromMemcache(url: str, size: Tuple[int, int]) -> Image:
    # TODO: Make this LRU instead of infinitely growing
    global memcache

    urlHash = strHash(url)
    images = memcache.get(urlHash, None)
    if not images:
        print('Cache MISS :(')
        original = getImageFromNetwork(url)
        resized = imageResize(original, size)
        memcache[urlHash] = {
            'original': original,
            size: resized
        }
        return resized

    desiredSize = images.get(size, None)
    if desiredSize:
        print('Cache Hit!!')
        return desiredSize
    else:
        print('Cache Hit!!')
        original = images.get('original', None)
        return imageResize(original, size)


@imageFetcher.route('/fetch-image')
@cross_origin(origin='localhost', headers=['Content- Type', 'Authorization'])
def fetchImage():
    url = request.args.get('url')
    width = request.args.get('width')
    height = request.args.get('height')

    print('Requested image-fetch', url, width, height)

    url = urlDecode(url)
    size = int(width), int(height)

    image = getImageFromMemcache(url, size)
    print(image)

    output = io.BytesIO()
    image.convert('RGBA').save(output, format='PNG')
    output.seek(0, 0)

    return send_file(output, mimetype='image/png', as_attachment=False)

