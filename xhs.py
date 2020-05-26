from requests_html import AsyncHTMLSession
from requests import Request
from loguru import logger
import asyncio
import paco
import simplejson as json
# import json
from box import Box
import maya

BQueue = asyncio.Queue


start_url = 'https://www.xiaohongshu.com/discovery/item/5ebac8aa000000000100240a'
session = AsyncHTMLSession()





class PlatformItemError(Exception):
    """Raise if it's deleted remotely or under review"""
    def  __init__(self, info):
        self.info = info

    def __str__(self):
        return f'platform item error: {self.info}'



class Task:

    def __init__(self, url=start_url):
        self.response = None
        self.parse_result = None
        self.url = url

    @classmethod
    def build_from_url(cls, url):
        return cls(url)

    


class Fetcher:

    def __init__(self):
        self.session = session
        self.start_url = start_url
        self.queue = BQueue()
        self.tasks = []
        self.profiles = []
        self.sid = 0

    async def get_resp(self, task: Task) -> Task:
        task.response = await session.request('GET', task.url)
        asyncio.sleep(5)
        return task

    def _get_json_content(self, task: Task) -> str:
        content = task.response.html.find('script')[-1].text[
            len('window.__INITIAL_SSR_STATE__='):
        ]
        return content.replace("undefined", "null")

    def _get_box(self, content) -> Box:
        box = Box(json.loads(content))
        if "ErrorPage" in box:
            asyncio.sleep(3)
            raise PlatformItemError(box.ErrorPage.info)
        
        return box
        
    def standarize_xhs_images(self, url: str) -> str:
        if url.startswith("//ci.xiaohongshu.com"):
            return "https:" + url
        return url


    async def run(self, task: Task):
        while True:
            try:
                task = await self.get_resp(task)
                if 'profile' in task.url:
                    self.extract_post_links(task)
                if 'discover' in task.url:
                    self.parse_post(task)
                    self.extract_post_links(task)
                task = await self.get_task()
            except:
                continue
 
        
    def extract_post_links(self, task):
        content = self._get_json_content(task) 
        notes = self._get_box(content).NoteView.panelData
        for note in notes:
            new_task = Task.build_from_url(
                f"https://www.xiaohongshu.com/discovery/item/{note.id}"
            )
            self.tasks.append(new_task)
        return self.tasks

    async def get_task(self) -> Task:
        logger.info(self.tasks)
        self.sid += 1
        return self.tasks[self.sid]



    def parse_post(self, task: Task) -> dict:
        content = self._get_json_content(task)
        logger.info(content)
        box = self._get_box(content).NoteView.noteInfo
        # comment_info = self._get_box(content).NoteView.commentInfo
        author_url_tmpl = 'https://www.xiaohongshu.com/user/profile/{}'
        normal_post_url_tmpl = 'https://www.xiaohongshu.com/discovery/item/{}'

        
        # try:
        #     logger.error(comment_info.total)
        #     comment_contents = [content for content in comment_info.comments.content]
        # except:
        #     comment_contents = []


        item = {
            "id": box.id,
            "real_url": normal_post_url_tmpl.format(box.id),
            "title": box.title or box.generatedTitle,
            "images": [self.standarize_xhs_images(img.url) for img in box.imageList],
            "desc": box.desc,
            "comments": box.comments,
            "likes": box.likes,
            "favs": box.collects,
            "user_id": box.user.id,
            'profile_url': author_url_tmpl.format(box.user.id),
            'profile_avatar': box.user.image,
            'profile_name': box.user.nickname,
            "post_time": maya.parse(box.time, timezone="Asia/Shanghai").epoch,
        }

        task.parse_result = item

        if item['comments'] == 2 or item['comments'] == 1: 
            write_data(item)

        

        logger.info(f'{item=}')

        return item


def write_data(item: dict):
    with open('data.json', 'a+') as f:
        f.write(json.dumps(item) + '\n')

if __name__ == '__main__':
    task = Task()
    fetch = Fetcher()
    paco.run(fetch.run(task))
