import requests
import os
import shutil
import json
import time
from bs4 import BeautifulSoup

class QuestionSpider(object):
    def __init__(self, question_queue):
        self.question_queue = question_queue

    def get_new_quetion_urls(self):
        question_urls = []
        s = requests.Session()
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/45.0.2454.101 Safari/537.36',
        }
        s.headers.update(headers)
        req = s.get('https://www.zhihu.com/topic/19551424/newest')
        soup = BeautifulSoup(req.text, 'html.parser')
        host = 'https://zhihu.com'
        for t in soup.find_all('a', class_='question_link'):
            question_urls.append(host + t['href'])
        return question_urls

    def update(self):
        for url in self.get_new_quetion_urls():
            self.question_queue.put(url)

class QuestionProcesser(object):
    def __init__(self, client, url):
            self.status = None
            self.question = client.from_url(url)
            self.url = url
            self.client = client
            self.work_directory = str(self.question.id) + '.question'
            self.answer_directory = os.path.join(self.work_directory, 'answers')
            self.deleted_answer_directory = os.path.join(self.work_directory, 'deleted')
            self.status_path = os.path.join(self.work_directory, 'status.json')
            for d in [self.work_directory, self.answer_directory, self.deleted_answer_directory]:
                if not os.path.isdir(d):
                    os.mkdir(d)
            if not os.path.isfile(self.status_path):
                self.status = {'available_answer_ids': self.get_available_answer_ids()}
            else:
                with open(self.status_path) as f:
                    self.status = json.load(f)

            self.available_answer_ids = set(self.status['available_answer_ids'])

    def __del__(self):
        if self.status:
            with open(self.status_path, 'w') as f:
                json.dump(self.status, f)

    def copy_to_deleted(self, answer_id):
        file_path = os.path.join(self.answer_directory, str(answer_id) + '.html')
        if not os.path.isfile(file_path):
            raise FileNotFoundError(file_path)
        else:
            shutil.copy(file_path, self.deleted_answer_directory)

    def save_to_answer(self):
        for a in self.question.answers:
            if not a.suggest_edit.status:
                if not os.path.isfile(os.path.join(self.answer_directory, str(a.id) + '.html')):
                    a.save(path=self.answer_directory, filename=str(a.id))

    def get_available_answer_ids(self):
        return [a.id for a in self.question.answers if not a.suggest_edit.status]

    def update(self):
        new_ids = set(self.get_available_answer_ids())
        deleted_ids = self.available_answer_ids.difference(new_ids)
        for i in deleted_ids:
            self.copy_to_deleted(i)
        self.available_answer_ids = new_ids
        self.status['available_answer_ids'] = list(new_ids)
        self.save_to_answer()

    def run(self, interval):
        while True:
            self.update()
            time.sleep(interval)

    def pedding(self):
        while True:
            pass
