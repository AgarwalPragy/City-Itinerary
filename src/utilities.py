from typing import List, Any, Dict, TypeVar, Generic
from unidecode import unidecode
import datetime
from collections import defaultdict
import string
import math
from functools import lru_cache
from urllib.parse import unquote
from fuzzywuzzy import fuzz
from math import radians, sin, cos, atan2, sqrt
from tunable import stopWords, synonyms, distanceOverEstimatorFactor

__all__ = ['maxArgMax', 'processName', 'doesFuzzyMatch', 'getCurrentTime', 'scaleRating', 'getWilsonScore', 'urlDecode', 'sanitizeName', 'tree', 'UnionFind', 'roundUpTime']

allowedChars = set(string.ascii_lowercase + string.digits + '-')


def avg(items):
    return sum(items) / len(items)


def maxArgMax(items, key=lambda x: x):
    maxScore = -float('inf')
    bestItem = None
    for item in items:
        score = key(item)
        if score > maxScore:
            maxScore = score
            bestItem = item
    return bestItem, maxScore


@lru_cache(None)
def sanitizeName(name: str) -> str:
    # TODO: improve this
    return name.strip().replace('|', '').replace('/', '')


@lru_cache(None)
def processName(name: str) -> str:
    """Removes spaces, normalize unicode data, convert to lowercase, remove special chars"""
    stopRemoved = name.lower()
    for stopw in stopWords:
        stopRemoved = stopRemoved.replace(stopw, ' ')
    synonymReplaced = stopRemoved
    for syn, word in synonyms:
        synonymReplaced = synonymReplaced.replace(syn, word)

    normalized: str = unidecode(synonymReplaced.strip())
    nohyphen = normalized.replace(' ', '')
    lowercase = nohyphen.lower()
    nospecial = ''.join(c for c in lowercase if c in allowedChars)
    return nospecial


@lru_cache(None)
def doesFuzzyMatch(name1: str, name2: str, threshold: int) -> bool:
    n1, n2 = processName(name1), processName(name2)
    similar = fuzz.ratio(n1, n2) > threshold
    contained = fuzz.partial_ratio(n1, n2) > threshold
    return contained or similar


def getCurrentTime() -> str:
    strFormat = '%y-%m-%d %H:%M:%S'
    return datetime.datetime.now().strftime(strFormat)


def scaleRating(givenRating: float, worstRating: int, bestRating: int) -> float:
    meanShifted = (givenRating - worstRating + 1)
    range = bestRating - worstRating + 1
    return meanShifted * 10 / range


def getWilsonScore(p, n) -> float:
    z = 1.96 # consider 95% confidence interval
    if n > 0:
        lower_bound = (p + z*z/(2*n) - z*math.sqrt((p*(1-p) + z*z/(4*n) )/n) )/ (1 + z*z/n)
    else:
        lower_bound = 0
    return lower_bound


def roundUpTime(val):
    hours = int(val)
    minutes = (val - hours) * 60
    minutes = int(math.ceil(minutes / 15) * 15)
    return hours + (minutes/60)


def urlDecode(url: str) -> str:
    return unquote(url)


def tree():
    return defaultdict(tree)


Titem = TypeVar('Titem')
class UnionFind(Generic[Titem]):
    def __init__(self):
        self.parents: Dict[Titem, Titem] = {}
        self.ranks: Dict[Titem, int] = defaultdict(lambda: 1)

    def __getitem__(self, x: Titem) -> Titem:
        par = self.parents.get(x, x)
        if x == par: return x
        root = self[self.parents[x]]
        self.parents[x] = root
        return root

    def rank(self, x: Titem) -> int:
        return self.ranks[self[x]]

    def union(self, *items: Titem) -> None:
        items = tuple(self[x] for x in items)
        largest = max(items, key=self.rank)
        for x in items:
            if x != largest:
                self.ranks[largest] += self.ranks[x]
                del self.ranks[x]
                self.parents[x] = largest


def latlngDistance(lat1, lon1, lat2, lon2):
    # approximate radius of earth in km
    R = 6373.0
    lat1 = radians(float(lat1))
    lon1 = radians(float(lon1))
    lat2 = radians(float(lat2))
    lon2 = radians(float(lon2))

    dlon = lon2 - lon1
    dlat = lat2 - lat1

    a = sin(dlat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(dlon / 2) ** 2
    c = 2 * atan2(sqrt(a), sqrt(1 - a))

    distance = R * c
    return distance*distanceOverEstimatorFactor


def floatCompare(a, b, rel_tol=1e-09, abs_tol=0.0):
    # https://stackoverflow.com/a/33024979
    return abs(a-b) <= max(rel_tol * max(abs(a), abs(b)), abs_tol)
