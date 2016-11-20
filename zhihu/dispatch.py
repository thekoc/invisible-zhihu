import process
import queue
import os
import time
import threading
import archive
from multiprocessing.dummy import Pool as ThreadPool


class QuestionDispatcher(object):
    def __init__(self, client):
        self.processes_max_num = 20
        self.max_task_size = 3 * self.processes_max_num
        self.stop = False
        data_path = 'data'
        if not os.path.isdir(data_path):
            os.makedirs(data_path)
        os.chdir(data_path)
        self.database = archive.ZhihuDatabase('zhihu.db')
        self.client = client
        self.spider = process.QuestionSpider()
        self.question_set = set(self.database.get_question_urls)

        self.task_queue = queue.Queue(maxsize=self.max_task_size)

    def task_update_loop(self, interval):
        while not self.stop:
            new_urls = self.spider.get_new_question_urls()
            for url in new_urls:
                self.question_set.add(url)
            for url in self.question_set:
                self.task_queue.put(url)
            time.sleep(interval)

    def monitor_question_loop(self, interval):
        pool = ThreadPool(self.processes_max_num)
        while not self.stop:
            url = self.task_queue.get()
            thread = pool.apply_async(self.update, args=(url,))
            self.process_in_pool.put(thread)
            time.sleep(interval)
        pool.close()
        pool.join()
        print('stopped')

    def update(self, question_url):
        if not self.stop:
            q = self.client.from_url(question_url)
            p = process.QuestionProcessor(q)
            p.update()
        self.process_in_pool.get()
        print('question {qid}: {title} finished'.format(qid=q.id, title=q.title))

    def run_single(self):
        while True:
            urls = self.spider.get_new_question_urls()
            for url in urls:
                self.question_set.add(url)
            for url in self.question_set:
                self.update(url)
            time.sleep(1)

    def run(self):
        try:
            task_update_thread = threading.Thread(target=self.task_update_loop, args=(240,))
            task_update_thread.start()
            monitor_thread = threading.Thread(target=self.monitor_question_loop, args=(1,))
            # monitor_thread.start()
            task_update_thread.join()
            monitor_thread.join()
        except KeyboardInterrupt:
            print('cleaning up...')
            self.stop = True
