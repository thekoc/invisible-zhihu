import os

from zhihu_oauth import ZhihuClient
from questions import QuestionSpider
from questions import QuestionProcessor
from questions import AnswerProcessor
from dispatch import QuestionDispatcher
from fake_zhihu import ZhihuClient as FakeClient
import requests
import queue
import time
import shutil


def login():
    TOKEN_FILE = 'token.pkl'

    client = ZhihuClient()

    if os.path.isfile(TOKEN_FILE):
        client.load_token(TOKEN_FILE)
    else:
        client.login_in_terminal()
        client.save_token(TOKEN_FILE)

    return client


def main():
    client = login()
    t = QuestionDispatcher(client)
    t.run()

def test():
    client = login()
    # q = client.from_url('https://www.zhihu.com/question/47542623')
    # p = QuestionProcessor(q)
    # a = client.from_url('https://www.zhihu.com/question/27182871/answer/35663127')
    # p = AnswerProcessor(a, 'test')

    q = client.from_url('https://www.zhihu.com/question/47542623')
    p = QuestionProcessor(q)
    while True:
        p.update()
        time.sleep(5)

def test1():
    client = login()
    q = QuestionSpider(client)
    while True:
        print(q.get_new_quetion_urls())
        time.sleep(30)

if __name__ == '__main__':
    main()
