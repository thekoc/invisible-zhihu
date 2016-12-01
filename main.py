import os

from zhihu_oauth import ZhihuClient
from invisible_zhihu.process import QuestionProcessor
from invisible_zhihu.process import AnswerProcessor
from invisible_zhihu.dispatch import QuestionDispatcher
from invisible_zhihu.fake_zhihu import ZhihuClient as FakeClient
import requests
import queue
import time
import shutil
import logging
import logging.config

data_path = 'data'
log_config_file = os.path.join(data_path, 'log.ini')
if os.path.isfile(log_config_file):
    logging.config.fileConfig(log_config_file)
else:
    logging.basicConfig(level=logging.DEBUG)


def login():
    if not os.path.isdir(data_path):
        os.makedirs(data_path)
    TOKEN_FILE = os.path.join(data_path, 'token.pkl')

    client = ZhihuClient()

    if os.path.isfile(TOKEN_FILE):
        client.load_token(TOKEN_FILE)
    else:
        client.login_in_terminal()
        client.save_token(TOKEN_FILE)

    return client


def main():
    client = login()
    t = QuestionDispatcher(client, 100)
    # t.producer.set_topics(topic_id_list)
    t.run()

if __name__ == '__main__':
    main()
