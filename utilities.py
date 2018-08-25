from typing import List, Any, Dict, TypeVar, Generic
from unidecode import unidecode
import datetime
from collections import defaultdict
import string
import math
from functools import lru_cache
from urllib.parse import unquote
from fuzzywuzzy import fuzz

__all__ = ['processName', 'doesFuzzyMatch', 'getCurrentTime', 'scaleRating', 'getWilsonScore', 'urlDecode', 'sanitizeName', 'tree', 'UnionFind']

allowedChars = set(string.ascii_lowercase + string.digits + '-')

@lru_cache(None)
def sanitizeName(name: str) -> str:
    # TODO: improve this
    return name.strip()


@lru_cache(None)
def processName(name: str) -> str:
    """Replaces spaces with hyphens, normalize unicode data, convert to lowercase, remove special chars"""
    normalized: str = unidecode(name.strip())
    nohyphen = normalized.replace(' ', '-')
    lowercase = nohyphen.lower()
    nospecial = ''.join(c for c in lowercase if c in allowedChars)
    return nospecial


@lru_cache(None)
def doesFuzzyMatch(name1: str, name2: str, threshold: int=90) -> bool:
    return fuzz.partial_ratio(processName(name1), processName(name2)) > threshold


def getCurrentTime() -> str:
    strFormat = '%y-%m-%d %H:%M:%S'
    return datetime.datetime.now().strftime(strFormat)


def scaleRating(givenRating: float, worstRating: int, bestRating: int) -> float:
    meanShifted = (givenRating - worstRating + 1)
    range = bestRating - worstRating + 1
    return meanShifted * 10 / range


def getWilsonScore(p, n) -> float:
    z = 1.96 # consider 95% confidence interval 
    lower_bound = (p + z*z/(2*n) - z*math.sqrt((p*(1-p) + z*z/(4*n) )/n) )/ (1 + z*z/n)
    return lower_bound


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

