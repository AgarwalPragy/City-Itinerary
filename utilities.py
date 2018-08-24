from typing import List
from unidecode import unidecode
import datetime
import json
import string
import math
from urllib.parse import unquote
from fuzzywuzzy import fuzz

__all__ = ['processName', 'getCurrentTime', 'scaleRating', 'getWilsonScore', 'urldecode']

allowedChars = set(string.ascii_lowercase + string.digits + '-')


def getBestCityName(allAliasesForCity: List[str]) -> str:
    return sorted(allAliasesForCity, key=len, reverse=True)[0] # returning the longest name
    # TODO: improve this to make it more intelligent


def processName(name: str) -> str:
    """Replaces spaces with hyphens, normalize unicode data, convert to lowercase, remove special chars"""
    normalized: str = unidecode(name.strip())
    nohyphen = normalized.replace(' ', '-')
    lowercase = nohyphen.lower()
    nospecial = ''.join(c for c in lowercase if c in allowedChars)
    return nospecial


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

def urldecode(urlstring: str) -> str:
    return unquote(urlstring)