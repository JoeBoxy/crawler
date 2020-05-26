import requests, re, json
from urllib import request
from requests import Session
from requests_html import HTMLSession
import paco
from box import Box


target_url = 'https://v.douyin.com/Eq3ojG/ '

header = {
    'user-agent': 'Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/71.0.3578.80 Mobile Safari/537.36'
}
session = HTMLSession()
request_url = session.get(target_url).html.url


pattern = re.compile(r'video/(\d+)')
pattern2 = re.compile(r'dytk: "(.*)"')
videoId = re.search(pattern, request_url).group(1)


html = session.get(target_url).html.find("script")[-1].text
dytk = re.search(pattern2, html).group(1)

url_tmp = "https://www.iesdouyin.com/web/api/v2/aweme/iteminfo/?item_ids={}&dytk={}"

url = (url_tmp.format(videoId, dytk))
# print(url)
resp = session.get(url)

box = Box(resp.json()['item_list'][0])
print(box.author.uid)
