import questions
import queue
import json
import os
import time
import threading
from multiprocessing.dummy import Pool as ThreadPool

class QuestionDispatcher(object):
    def __init__(self, client):
        self.processes_max_num = 20
        self.max_task_size = 3 * self.processes_max_num
        self.stop = False
        self.client = client
        self.spider = questions.QuestionSpider()
        self.root_path = 'questions'
        if not os.path.isdir(self.root_path):
            os.mkdir(self.root_path)
        os.chdir(self.root_path)
        self.questions_path = 'questions.json'
        self.question_set = set()
        if os.path.isfile(self.questions_path):
            with open('questions.json') as f:
                self.question_set = set(json.load(f))

        self.task_queue = queue.Queue(maxsize=self.max_task_size)
        self.process_in_pool = queue.Queue(maxsize=self.processes_max_num)

    def __del__(self):
        with open(self.questions_path, 'w') as f:
            json.dump(list(self.question_set), f)

    def task_update_loop(self, interval):
        while not self.stop:
            new_urls = self.spider.get_new_quetion_urls()
            for url in new_urls:
                self.question_set.add(url)
            for url in self.question_set:
                self.task_queue.put(url)
            with open('questions.json', 'w') as f:
                json.dump(list(self.question_set), f)
            time.sleep(interval)

    def monitor_question_loop(self, interval):
        pool = ThreadPool(self.processes_max_num)
        while not self.stop:
            url = self.task_queue.get()
            thread = pool.apply_async(self.monitor, args=(url,))
            self.process_in_pool.put(thread)
            time.sleep(interval)
        pool.close()
        pool.join()
        print('stopped')

    def monitor(self, question_url):
        if not self.stop:
            q = self.client.from_url(question_url)
            p = questions.QuestionProcessor(q)
            p.update()
        self.process_in_pool.get()
        print('question %d: %s finished' % (q.id, q.title))

    def run(self):
        try:
            task_update_thread = threading.Thread(target=self.task_update_loop, args=(240,))
            task_update_thread.start()
            monitor_thread = threading.Thread(target=self.monitor_question_loop, args=(1,))
            monitor_thread.start()
            task_update_thread.join()
            monitor_thread.join()
        except KeyboardInterrupt:
            print('cleaning up...')
            self.stop = True
