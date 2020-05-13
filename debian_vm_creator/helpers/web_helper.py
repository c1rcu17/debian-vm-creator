import shutil
import urllib.error
import urllib.request

from .exception_helper import AppException


class WebException(AppException):
    def __init__(self, url, error):
        super().__init__("Could not fetch {}: {}".format(url, error))


def fetch(url, save_file=None):
    try:
        response = urllib.request.urlopen(url)
    except urllib.error.HTTPError as error:
        raise WebException(url, error)
    except urllib.error.URLError as error:
        try:
            raise WebException(url, error.reason.strerror)
        except AttributeError:
            raise WebException(url, error.reason)
    else:
        if save_file:
            with open(save_file, "wb") as stream:
                shutil.copyfileobj(response, stream)
            return None
        return response.read()
