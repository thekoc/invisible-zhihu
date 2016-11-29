import requests
import json
import os
import logging
from zhihu import ZhihuClient as WebClient
from bs4 import BeautifulSoup
from .tools import url_to_qid

log = logging.getLogger(__name__)
log.addHandler(logging.NullHandler())

class QuestionSpider(object):
    def __init__(self):
        self.web_client = WebClient()
        self.cookies_path = 'cookies.json'
        self.cookies = json.load(open(self.cookies_path))
        if os.path.isfile(self.cookies_path):
            self.web_client.login_with_cookies(self.cookies_path)
        else:
            self.web_client.create_cookies(self.cookies_path)

    def get_newest_topic_question_urls(self, topic_id):
        question_urls = []
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/45.0.2454.101 Safari/537.36',
        }
        s = requests.Session()
        req = s.get('https://www.zhihu.com/topic/{topic_id}/newest'.format(topic_id=topic_id), headers=headers, cookies=self.cookies)
        soup = BeautifulSoup(req.text, 'html.parser')
        host = 'https://www.zhihu.com'
        for t in soup.find_all('a', class_='question_link'):
            question_urls.append(host + t['href'])
        return question_urls

    def get_new_question_urls(self):
        topic_ids = [19551424]
        urls = []
        for i in topic_ids:
            urls += self.get_newest_topic_question_urls(i)
        return urls


class QuestionProducer(object):
    def __init__(self, database, client):
        self.database = database
        self.client = client
        self.spider = QuestionSpider()
        self.valid_urls = set()
        self.gen = self.question_generator()

    def question_generator(self):
        while True:
            archived_urls = self.database.get_question_urls()
            new_urls = self.spider.get_new_question_urls()
            url_set = set(archived_urls + new_urls)
            for url in url_set:
                yield url

    def next_question_url(self):
        return next(self.gen)
