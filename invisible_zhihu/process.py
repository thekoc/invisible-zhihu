import shutil
import time
import logging
from tools import qid_to_url
from tools import aid_to_url
from tools import tid_to_url
from tools import uid_to_url
from archive import ZhihuDatabase

log = logging.getLogger(__name__)


class QuestionProcessor(object):
    def __init__(self, question):
        self.answer_processor_set = set()
        self.database = ZhihuDatabase('zhihu.db')
        self.stop = False
        self.question = question
        self.question_id = self.question.id
        self.url = qid_to_url(self.question.id)
        self.title = self.question.title
        self.excerpt = self.question.excerpt
        self.database.insert_question(self.question_id, self.title, self.url, self.excerpt)
        for topic in self.question.topics:
            tid = topic.id
            self.database.insert_topic(tid, topic.name, tid_to_url(tid))
            self.database.insert_relationship_topic_question_id(tid, self.question_id)

    def update_answers(self):
        for a in self.question.answers:
            if self.stop:
                break
            ap = AnswerProcessor(a)
            self.answer_processor_set.add(ap)
            try:
                log.debug('updating answer %d in question %d', a.id, self.question_id)
                ap.update()
            finally:
                self.answer_processor_set.remove(ap)

    def get_current_visible_answer_ids(self):
        try:
            ids = [a.id for a in self.question.answers]
            return ids
        except Exception as e:
            log.error(e)
            return self.get_archived_visible_answer_ids()

    def get_archived_visible_answer_ids(self):
        return set(self.database.get_visible_answer_ids(self.question_id))

    def update(self):
        if False:
            pass
        else:
            try:
                new_ids = set(self.get_current_visible_answer_ids())
            except Exception as e:
                log.error('get new answer failed')
                new_ids = self.get_archived_visible_answer_ids()
                raise e
            deleted_ids = self.get_archived_visible_answer_ids().difference(new_ids)
            for i in deleted_ids:
                log.info('new deleted answer')
                self.database.mark_answer_deleted(self.question_id, i)
            self.update_answers()


class AnswerProcessor(object):
    def __init__(self, answer):
        self.stop = False
        self.answer = answer
        self.database = ZhihuDatabase('zhihu.db')
        self.answer_id = self.answer.id
        self.question_id = self.answer.question.id
        self.author_id = self.answer.author.id
        self.url = aid_to_url(self.question_id, self.answer_id)
        self.voteup_count = self.answer.voteup_count
        self.thanks_count = self.answer.thanks_count
        self.created_time = self.answer.created_time
        self.updated_time = self.answer.updated_time
        self.suggest_edit = self.answer.suggest_edit.status
        if self.should_insert():
            self.insert()
        author = self.answer.author
        self.database.insert_user(author.id, author.name, uid_to_url(author.id))

    @property
    def content(self):
        return self.answer.content

    @property
    def excerpt(self):
        return self.answer.excerpt

    def insert(self):
        log.debug('inserting answer %d in question %d', self.answer_id, self.question_id)
        self.database.insert_answer(
            self.answer_id, self.question_id, self.author_id,
            self.url, self.excerpt, self.content,
            self.voteup_count, self.thanks_count,
            self.created_time, self.updated_time, int(time.time()),
            self.suggest_edit)

    def should_insert(self):
        db = self.database
        if db.get_answer(self.question_id, self.answer_id, updated_time=self.updated_time):
            return False
        else:
            return True

    def get_archived_visible_comment_ids(self):
        ids = self.database.get_visible_comment_ids(self.answer_id)
        return set(ids)

    def get_current_visible_comment_ids(self):
        try:
            ids = [c.id for c in self.answer.comments]
            return ids
        except Exception as e:
            return self.get_archived_visible_comment_ids()

    def append_added_comments(self, comment_ids):
        for c in self.answer.comments:
            if self.stop:
                break
            if c.id in comment_ids:
                comment_author = c.author
                comment_author_id = comment_author.id
                log.debug('inserting comment %d in answer %d in question %d', c.id, self.answer_id, self.question_id)
                self.database.insert_comment(
                    c.created_time, int(time.time()), c.content,
                    c.id, self.answer_id, comment_author_id, self.question_id,
                    reply_to_id=c.reply_to.id if c.reply_to else None
                )
                author = c.author
                if self.database.get_user(author.id) is None:
                    self.database.insert_user(author.id, author.name, uid_to_url(author.id))

    def update(self):
        new_ids = set(self.get_current_visible_comment_ids())
        archived_ids = self.get_archived_visible_comment_ids()
        deleted_ids = archived_ids.difference(new_ids)
        added_ids = new_ids.difference(archived_ids)
        for i in deleted_ids:
            log.info('new deleted comment')
            self.database.mark_comment_deleted(self.question_id, self.answer_id, i)
        self.append_added_comments(added_ids)
