import process
import produce
import queue
import os
import time
import threading
import archive
import logging
from multiprocessing.dummy import Pool as ThreadPool

log = logging.getLogger(__name__)


class _safe_set(set):
    def __init__(self, *args, **kwargs):
        super(_safe_set, self).__init__(*args, **kwargs)
        self.lock = threading.Lock()

    def add(self, element):
        with self.lock:
            super(_safe_set, self).add(element)

    def remove(self, element):
        with self.lock:
            super(_safe_set, self).remove(element)


class QuestionDispatcher(object):

    def __init__(self, client, process_num=100):
        self.processes_max_num = process_num
        self.max_task_size = 3 * self.processes_max_num
        self.stop = False
        data_path = 'data'
        if not os.path.isdir(data_path):
            os.makedirs(data_path)
        os.chdir(data_path)
        self.database = archive.ZhihuDatabase('zhihu.db')
        self.client = client
        self.spider = produce.QuestionSpider()
        self.question_set = set(self.database.get_question_urls())

        self.task_queue = queue.Queue(maxsize=self.max_task_size)
        self.process_counter = queue.Queue(maxsize=self.processes_max_num)
        self.processor_set = _safe_set()

    def task_update_loop(self, interval):
        while not self.stop:
            start_time = time.time()
            new_urls = self.spider.get_new_question_urls()
            for url in new_urls:
                self.question_set.add(url)
            for url in self.question_set:
                if not self.stop:
                    self.task_queue.put(url)
            while time.time() - start_time < interval and not self.stop:
                time.sleep(0.1)
        log.debug('task_update_loop stopped')

    def monitor_question_loop(self, interval):
        pool = ThreadPool(self.processes_max_num + 1)

        while not self.stop:
            start_time = time.time()
            if not self.task_queue.full() and not self.stop:
                pool.apply_async(self.handle_question)
            while time.time() - start_time < interval and not self.stop:
                time.sleep(0.1)
        while not self.task_queue.empty():
            self.task_queue.get()
        pool.close()
        pool.join()
        log.debug('monitor_question_loop stopped')

    def handle_question(self):
        url = self.task_queue.get()
        q = self.client.from_url(url)
        if self.stop:
            log.info('question {qid}: {title} aborted'.format(qid=q.id, title=q.title))
            log.info(len(self.processor_set), 'left')
        else:

            p = process.QuestionProcessor(q)
            self.processor_set.add(p)
            try:
                p.update()
                log.info('question {qid}: {title} finished'.format(qid=q.id, title=q.title))
            except:
                log.debug('except in handle_question')
            finally:
                self.processor_set.remove(p)

    def run_single(self):
        while True:
            urls = self.spider.get_new_question_urls()
            for url in urls:
                log.debug(url)
                self.question_set.add(url)
                self.task_queue.put(url)
            for url in self.question_set:
                self.handle_question()
            time.sleep(1)

    def run(self):
        try:
            task_update_thread = threading.Thread(target=self.task_update_loop, args=(240,))
            task_update_thread.start()
            monitor_thread = threading.Thread(target=self.monitor_question_loop, args=(1,))
            monitor_thread.start()
            task_update_thread.join()
            monitor_thread.join()
        except KeyboardInterrupt:
            log.info('cleaning up...')
            self.stop = True
            for qp in self.processor_set:
                qp.stop = True
                for ap in qp.answer_processor_set:
                    ap.stop = True
