import sys
import pprint


class AppException(Exception):
    def message(self):
        return str(self)

    def log(self, log_function=None):
        if log_function is None:
            log_function = lambda x: print(x, file=sys.stderr)

        log_function(self.message())
        return self


def printattrs(obj):
    attrs = {}

    for attr in dir(obj):
        if attr.startswith("__"):
            continue

        try:
            value = getattr(obj, attr)
        except AttributeError:
            continue

        if not callable(value):
            attrs[attr] = value

    pprint.pprint(attrs)
    return obj
