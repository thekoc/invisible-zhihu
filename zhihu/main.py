import os

from zhihu_oauth import ZhihuClient
from questions import QuestionSpider
from questions import QuestionProcesser
from dispatch import QuestionDispatcher
from fake_zhihu import ZhihuClient as FakeClient
import requests
import queue


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
    # question = client.question(20691441)
    # print(dir(question))
    # print(question.status)
    # for a in question.answers:
    #     print(a.author.id)
    # topic = client.topic(19551424)
    # i = 0
    # print(topic.avatar_url)
    # for q in topic.unanswered_questions:
    #     i += 1
    #     if i < 3:
    #         print(q.answer_count)
    #     else:
    #         break
    # q = queue.Queue()
    # qs = QuestionSpider(q)
    # qs.update()
    # while not q.empty():
    #     print(q.get())
    # t = QuestionProcesser(client, 'https://www.zhihu.com/question/52212165')

    # t.monitor(5)
    t = QuestionDispatcher(client)
    t.run()

def test():
    c = FakeClient()
    c.login()
    c.test()


if __name__ == '__main__':
    main()
