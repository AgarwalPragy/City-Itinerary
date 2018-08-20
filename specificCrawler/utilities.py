from unidecode import unidecode
import datetime
import json
import string

allowedChars = set(string.ascii_lowercase + string.digits + '-')


def processName(name: str) -> str:
    """Replaces spaces with hyphens, normalize unicode data, convert to lowercase, remove special chars"""
    normalized: str = unidecode(name.strip())
    nohyphen = normalized.replace(' ', '-')
    lowercase = nohyphen.lower()
    nospecial = ''.join(c for c in lowercase if c in allowedChars)
    return nospecial


def getCurrentTime() -> str:
    strFormat = '%y-%m-%d %H:%M:%S'
    return datetime.datetime.now().strftime(strFormat)


def scaleRating(givenRating: float, worstRating: int, bestRating: int) -> float:
    meanShifted = (givenRating - worstRating + 1)
    range = bestRating - worstRating + 1
    return meanShifted * 10 / range

