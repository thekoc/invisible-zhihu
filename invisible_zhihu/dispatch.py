import queue
import os
import time
import threading
import logging
from multiprocessing.dummy import Pool as ThreadPool

from .archive import ZhihuDatabase
from .process import QuestionProcessor
from .produce import QuestionProducer

log = logging.getLogger(__name__)
log.addHandler(logging.NullHandler())


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
        self.stop = False
        data_path = 'data'
        if not os.path.isdir(data_path):
            os.makedirs(data_path)
        os.chdir(data_path)
        self.database = ZhihuDatabase('zhihu.db')
        self.client = client
        self.producer = QuestionProducer(self.database, self.client)
        self.question_set = set(self.database.get_question_urls())

        self.processor_set = _safe_set()

    @property
    def process_count(self):
        return len(self.processor_set)

    def monitor_question_loop(self, interval):
        pool = ThreadPool(self.processes_max_num + 1)

        while not self.stop:
            start_time = time.time()
            if self.process_count < self.processes_max_num and not self.stop:
                log.debug("now: " + str(self.process_count) + " max: " + str(self.processes_max_num))
                url = self.producer.next_question_url()
                log.debug('new url %s', url)
                pool.apply_async(self.handle_question, args=(url,))
            while time.time() - start_time < interval and not self.stop:
                time.sleep(0.1)
        pool.close()
        pool.join()
        log.debug('monitor_question_loop stopped')

    def handle_question(self, url):
        try:
            q = self.client.from_url(url)
            if not self.stop:
                p = QuestionProcessor(q)
                self.processor_set.add(p)
                try:
                    p.update()
                    if self.stop:
                        log.info('question {qid}: {title} aborted'.format(qid=q.id, title=q.title))
                        log.info(str(len(self.processor_set)) + ' left')
                    else:
                        log.info('question {qid}: {title} finished'.format(qid=q.id, title=q.title))
                except Exception as e:
                    log.error(str(e))
                finally:
                    self.processor_set.remove(p)
        except Exception as e:
            log.error(str(e))
            raise e


    def run_single(self):
        while True:
            for url in self.question_set:
                self.handle_question(self.producer.next_question_url())
            time.sleep(1)

    def run(self):
        try:
            t = threading.Thread(target=self.monitor_question_loop, args=(0.5,))
            t.start()
            t.join()
        except KeyboardInterrupt:
            log.info('cleaning up...')
            self.stop = True
            for qp in self.processor_set:
                qp.stop = True
                for ap in qp.answer_processor_set:
                    ap.stop = True
