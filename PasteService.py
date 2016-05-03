import sys
import requests
import traceback

# interface paste services are expected to follow
class IPasteService:
    def create(self, text):
      pass

# possible exceptions IPasteService.create may throw
class CannotConnect(Exception):
    def __init__(self, url):
        self.url = url
    def __str__(self):
        return "error: unable to connect to '" + self.url + "'"

class HttpError(Exception):
    def __init__(self, code):
        self.code = code
    def __str__(self):
        return "error: http call returned code " + self.code

# TODO: expiration? unlisted?
class Umiki(IPasteService):
    def __init__(self, apiKey):
        self.url = "https://serv2.pink/api/umiki/v1"
        self.apiKey = apiKey
    def createPayload(self, text):
        return {
            'api_key': self.apiKey,
            'content': text,
        }
    def create(self, text):
        payload = self.createPayload(text)

        try:
            r = requests.post(self.url, payload)
        except Exception, err:
            sys.stderr.write("Could not connect to url:\n")
            traceback_string = traceback.format_exc()
            sys.stderr.write(traceback_string + '\n')

            raise CannotConnect(self.url)
        try:
            # will cause an exception if the request is bad...
            r.raise_for_status()
        except Exception, err:
            traceback_string = traceback.format_exc()
            sys.stderr.write('HTTP error:\n' + traceback_string + '\n')

            raise HttpError(r.status_code)

        return r.json()['url']

