import requests
import os
import shutil
import json
import time
from bs4 import BeautifulSoup
from tools import qid_to_url
from tools import aid_to_url
from tools import tid_to_url
from tools import uid_to_url
from zhihu import ZhihuClient as WebClient
from archive import ZhihuDatabase


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


class QuestionProcessor(object):
    def __init__(self, question):
        self.answer_processor_set = set()
        self.database = ZhihuDatabase('zhihu.db')
        self.stop = False
        self.question = question
        self.question_id = self.question.id
        self.url = qid_to_url(self.question.id)
        self.title = self.question.title
        self.excerpt = self.question.excerpt
        self.database.insert_question(self.question_id, self.title, self.url, self.excerpt)
        author = self.question.author
        self.database.insert_user(author.id, author.name, uid_to_url(author.id))
        for topic in self.question.topics:
            tid = topic.id
            self.database.insert_topic(tid, topic.name, tid_to_url(tid))
            self.database.insert_relationship_topic_question_id(tid, self.question_id)

    def update_answers(self):
        for a in self.question.answers:
            if not self.stop:
                ap = AnswerProcessor(a)
                self.answer_processor_set.add(ap)
                try:
                    ap.update()
                finally:
                    self.answer_processor_set.remove(ap)

    def get_current_visible_answer_ids(self):
        try:
            ids = [a.id for a in self.question.answers]
            return ids
        except Exception as e:
            print(e)
            return self.meta_info['visible_answer_ids']

    def get_archived_visible_answer_ids(self):
        return set(self.database.get_visible_answer_ids(self.question_id))

    def update(self):
        if False:
            pass
        else:
            try:
                new_ids = set(self.get_current_visible_answer_ids())
            except Exception as e:
                print('get new answer failed')
                new_ids = self.get_archived_visible_answer_ids()
                raise e
            deleted_ids = self.get_archived_visible_answer_ids().difference(new_ids)
            for i in deleted_ids:
                self.database.mark_answer_deleted(i)
            self.update_answers()


class AnswerProcessor(object):
    def __init__(self, answer):
        self.stop = False
        self.answer = answer
        self.database = ZhihuDatabase('zhihu.db')
        self.answer_id = self.answer.id
        self.question_id = self.answer.question.id
        self.author_id = self.answer.author.id
        self.url = aid_to_url(self.question_id, self.answer_id)
        self.excerpt = self.answer.excerpt
        self.content = self.answer.content
        self.database.insert_answer(
            self.answer_id, self.question_id, self.author_id, self.url, self.excerpt, self.content
        )
        author = self.answer.author
        self.database.insert_user(author.id, author.name, uid_to_url(author.id))

    def get_archived_visible_comment_ids(self):
        ids = self.database.get_visible_comment_ids(self.answer_id)
        return set(ids)

    def get_current_visible_comment_ids(self):
        try:
            ids = [c.id for c in self.answer.comments]
            return ids
        except Exception as e:
            return self.meta_info['visible_comment_ids']

    def append_added_comments(self, comment_ids):
        for c in self.answer.comments:
            if not self.stop:
                if c.id in comment_ids:
                    self.database.insert_comment(
                        c.created_time, c.content,
                        c.id, self.answer_id, self.author_id, self.question_id,
                        reply_to_id=c.reply_to.id if c.reply_to else None
                    )
                    author = c.author
                    if self.database.get_user(author.id) is None:
                        self.database.insert_user(author.id, author.name, uid_to_url(author.id))

    def update(self):
        new_ids = set(self.get_current_visible_comment_ids())
        archived_ids = self.get_archived_visible_comment_ids()
        deleted_ids = archived_ids.difference(new_ids)
        added_ids = new_ids.difference(archived_ids)
        for i in deleted_ids:
            self.database.mark_comment_deleted(self.question_id, self.answer_id, i)
        self.append_added_comments(added_ids)
