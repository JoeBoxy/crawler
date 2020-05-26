import requests
from requests_html import HTMLSession

session = HTMLSession()
resp = session.get("http://xhslink.com/kgWig")
print(resp.text)