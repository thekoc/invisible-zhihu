import os

from zhihu_oauth import ZhihuClient
from process import QuestionSpider
from process import QuestionProcessor
from process import AnswerProcessor
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

    q = client.from_url('https://www.zhihu.com/question/36391193')
    # p = QuestionProcessor(q)
    print(q.status)
    for a in q.answers:
        print(a.id)


def test1():
    def inf():
        i = 0
        while True:
            i += 1
            yield i
    import sqlite3
    conn = sqlite3.connect('fuck.db')
    coursor = conn.cursor()
    coursor.execute('create table if not exists user (id int, name text, age int,  primary key(id, age))')
    for i in [1, 4, 2, 3, 5]:
        coursor.execute('insert or replace into user (id, name, age) values (:id, :name, :age)', {'id': i, 'name': 'shit\'', 'age': None})
    # print(coursor.execute("""select * from user""").fetchall())
    # coursor.execute('insert into user (id, name) values (\'aa\', \'bb\')')
    coursor.close()
    conn.commit()
    conn.close()

if __name__ == '__main__':
    main()
