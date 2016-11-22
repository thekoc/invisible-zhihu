import requests
import json
import os
from zhihu import ZhihuClient as WebClient
from bs4 import BeautifulSoup


class QuestionSpider(object):
    def __init__(self):
        self.web_client = WebClient()
        self.cookies_path = 'cookies.json'
        self.cookies = json.load(open(self.cookies_path))
        if os.path.isfile(self.cookies_path):
            self.web_client.login_with_cookies(self.cookies_path)
        else:
            self.web_client.create_cookies(self.cookies_path)

    def get_new_question_urls(self):
        question_urls = []
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/45.0.2454.101 Safari/537.36',
        }
        s = requests.Session()
        req = s.get('https://www.zhihu.com/topic/19673476/newest', headers=headers, cookies=self.cookies)
        soup = BeautifulSoup(req.text, 'html.parser')
        host = 'https://www.zhihu.com'
        for t in soup.find_all('a', class_='question_link'):
            question_urls.append(host + t['href'])
        return question_urls
