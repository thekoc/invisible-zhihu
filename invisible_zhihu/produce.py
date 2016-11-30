import requests
import json
import os
import logging
from zhihu import ZhihuClient as WebClient
from bs4 import BeautifulSoup
from .tools import url_to_qid
from .fake_zhihu import headers

log = logging.getLogger(__name__)
log.addHandler(logging.NullHandler())


class QuestionAdder(object):
    def __init__(self, topic_ids):
        self.web_client = WebClient()
        self.cookies_path = 'cookies.json'
        self.topic_ids = topic_ids
        self.cookies = json.load(open(self.cookies_path))
        if os.path.isfile(self.cookies_path):
            self.web_client.login_with_cookies(self.cookies_path)
        else:
            self.web_client.create_cookies(self.cookies_path)

    def get_newest_topic_question_urls(self, topic_id):
        question_urls = []
        s = requests.Session()
        try:
            req = s.get('https://www.zhihu.com/topic/{topic_id}/newest'.format(topic_id=topic_id), headers=headers, cookies=self.cookies)
        except ConnectionError as e:
            log.error('Connect Failed\n' + str(e))
            return []
        else:
            soup = BeautifulSoup(req.text, 'html.parser')
            host = 'https://www.zhihu.com'
            for t in soup.find_all('a', class_='question_link'):
                question_urls.append(host + t['href'])
            return question_urls

    def get_new_question_urls(self):
        topic_ids = self.topic_ids
        if not isinstance(topic_ids, list):
            raise TypeError('topic_ids must be a list.')
        if not all(isinstance(i, int) for i in topic_ids):
            raise TypeError('The element in topic_ids must be int.')
        urls = []
        for i in topic_ids:
            urls += self.get_newest_topic_question_urls(i)
        return urls


class QuestionProducer(object):
    def __init__(self, database, client):
        self._database = database
        self._client = client
        root_topic_id = 19776749
        self._adder = QuestionAdder([root_topic_id])
        self.get_new_question_urls = self._adder.get_new_question_urls
        self._gen = self._question_generator()

    def _question_generator(self):
        while True:
            archived_urls = self._database.get_question_urls()
            new_urls = self.get_new_question_urls()
            url_set = set(archived_urls + new_urls)
            for url in url_set:
                yield url

    def next_question_url(self):
        return next(self._gen)

    def set_topics(self, topic_id_list):
        """Use this function to change the topic(s).

        The producer will kept generate questions from root topic by default.

        Args:
            topic_id_list(list(int)):
                The topic id is the number in the topic's url. For example,
                the politics topic has url 'https://www.zhihu.com/topic/19551424/hot',
                and 19551424 is it's topic id.
        """
        self._adder.topic_ids = topic_id_list

    def set_add_url_function(self, func):
        """Set the function that add the new urls in producer.

        Args:
            func: This function has no parameter and will return list of
            question urls everytime it is called. Each url will be added into
            the task pool so that the program will kept examing whether it is
            deleted or not automatically.
        """
        self.get_new_question_urls = func
