from typing import Tuple, Optional
import ssl
from flask import Blueprint, send_file, request
from flask_cors import cross_origin
from functools import lru_cache
import hashlib
import io
from PIL import Image
from resizeimage import resizeimage
import urllib.request

from utilities import urlDecode

imageFetcher = Blueprint('imageFetcher', __name__)
ssl._create_default_https_context = ssl._create_unverified_context

brokenImage = 'https://banner2.kisspng.com/20180403/cte/kisspng-london-eye-the-london-pass-skyline-tourist-attract-london-eye-5ac3a5c3c91f47.3845406215227713958238.jpg'


@lru_cache(1000)
def strHash(string):
    # https://gist.github.com/nmalkin/e287f71788c57fd71bd0a7eec9345add
    return hashlib.sha256(string.encode('utf-8')).hexdigest()


def imageResize(image: Image, size: Tuple[int, int]) -> Image:
    return resizeimage.resize_cover(image, size, validate=False)


def getImageFromNetwork(url: str) -> Image:
    headers = {
        'User-Agent': 'Mozilla/5.0 (compatible; MSIE 10.0; Macintosh; Intel Mac OS X 10_7_3; Trident/6.0)'
    }
    res = urllib.request.urlopen(urllib.request.Request(url, headers=headers))
    img = Image.open(io.BytesIO(res.read()))
    return img


memcache = {}


def getImageFromMemcache(url: str, size: Optional[Tuple[int, int]]) -> Image:
    # TODO: Make this LRU instead of infinitely growing
    global memcache

    urlHash = strHash(url)
    images = memcache.get(urlHash, None)
    if not images:
        print('Cache MISS for', url)
        try:
            original = getImageFromNetwork(url)
        except Exception as e:
            return getImageFromMemcache(brokenImage, size)
        memcache[urlHash] = {
            'original': original
        }
        if size:
            resized = imageResize(original, size)
            memcache[urlHash][size] = resized
            return resized
        else:
            return original

    desiredSize = images.get(size, None)
    if desiredSize:
        # print('Cache Hit!!')
        return desiredSize
    else:
        # print('Cache Hit!!')
        original = images.get('original', None)
        if size is None:
            return original
        return imageResize(original, size)


@imageFetcher.route('/api/fetch-image')
@cross_origin(origin='localhost', headers=['Content- Type', 'Authorization'])
def fetchImage():
    url = request.args.get('url')
    width = request.args.get('width', 'null')
    height = request.args.get('height', 'null')

    # print('Requested image-fetch', url, width, height)

    url = urlDecode(url)
    if width != 'null' and height != 'null':
        size = int(width), int(height)
    else:
        size = None

    image = getImageFromMemcache(url, size)
    # print(image)

    output = io.BytesIO()
    image.convert('RGBA').save(output, format='PNG')
    output.seek(0, 0)

    return send_file(output, mimetype='image/png', as_attachment=False)


@imageFetcher.route('/api/prefetch')
@cross_origin(origin='localhost', headers=['Content- Type', 'Authorization'])
def preFetchCityImages():
    cityNames = ['agra', 'amsterdam',
                 'bangkok', 'barcelona',
                 'dubai',
                 'mumbai',
                 'riyadh', 'rome',
                 'seoul', 'shanghai', 'singapore',
                 'taipei', 'tokyo',
                 'vienna']
    size = 1500, 875
    cityName, num = None, None
    try:
        for cityName in cityNames:
            for num in range(1, 4):
                getImageFromMemcache('http://localhost:5000/resources/city-images/{}-{}.jpg'.format(cityName, num), size)
    except Exception as e:
        return 'city: {}-{}. Error: {}'.format(cityName, num, e)
    return 'All good!'
