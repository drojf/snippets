from io import BytesIO
from zipfile import ZipFile
from urllib.request import urlopen

resp = urlopen("https://www.python.org/ftp/python/3.7.7/python-3.7.7-embed-win32.zip")
zipfile = ZipFile(BytesIO(resp.read()))
zipfile.extractall(path="output")