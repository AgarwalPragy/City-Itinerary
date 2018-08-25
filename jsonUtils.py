import dataclasses
import json

__all__ = ['J', 'EnhancedJSONEncoder']


class J(dict):
    pass


class EnhancedJSONEncoder(json.JSONEncoder):
    # https://stackoverflow.com/a/51286749/2570622
    def default(self, o):
        if dataclasses.is_dataclass(o):
            return dataclasses.asdict(o)
        return super().default(o)