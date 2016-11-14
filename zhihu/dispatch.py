import questions
import queue
import json
import os
import time
import threading
from multiprocessing.dummy import Pool as ThreadPool

class QuestionDispatcher(object):
    def __init__(self, client):
        self.stop = False
        self.client = client
        self.root_path = 'questions'
        if not os.path.isdir(self.root_path):
            os.mkdir(self.root_path)
        os.chdir(self.root_path)
        self.questions_path = 'questions.json'
        self.question_set = set()
        self.monitor_url_set = set()
        if os.path.isfile(self.questions_path):
            with open('questions.json') as f:
                self.question_set = set(json.load(f))

        self.queue = queue.Queue()
        self.spider = questions.QuestionSpider(client)

    def __del__(self):
        with open(self.questions_path, 'w') as f:
            json.dump(list(self.question_set), f)

    def question_update_loop(self, interval):
        while not self.stop:
            new_urls = self.spider.get_new_quetion_urls()
            for url in new_urls:
                self.queue.put(url)
            time.sleep(interval)

    def monitor_question_loop(self, interval):
        while not self.stop:
            while not self.queue.empty():
                url = self.queue.get()
                self.question_set.add(url)
            with open(self.questions_path, 'w') as f:
                json.dump(list(self.question_set), f)

            questions = list(self.question_set)
            size = 10
            for i in range(0, len(questions), size):
                if not self.stop:
                    pool = ThreadPool(size)
                    if i + size < len(questions):
                        results = pool.map(self.monitor, questions[i: i + size])
                    else:
                        results = pool.map(self.monitor, questions[i: -1])
                    pool.close()
                    pool.join()
                    time.sleep(interval)
        print('stopped')

    def monitor(self, question_url):
        if not self.stop:
            p = questions.QuestionProcesser(self.client.from_url(question_url))
            p.update()

    def run(self):
        try:
            update_thread = threading.Thread(target=self.question_update_loop, args=(5,))
            update_thread.start()
            monitor_thread = threading.Thread(target=self.monitor_question_loop, args=(5,))
            monitor_thread.start()
            update_thread.join()
            monitor_thread.join()
        except KeyboardInterrupt:
            print('cleaning up...')
            self.stop = True
