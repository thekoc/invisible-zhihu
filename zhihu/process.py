import shutil
import time
from tools import qid_to_url
from tools import aid_to_url
from tools import tid_to_url
from tools import uid_to_url
from archive import ZhihuDatabase


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
            if not self.stop:
                ap = AnswerProcessor(a)
                self.answer_processor_set.add(ap)
                try:
                    ap.update()
                finally:
                    self.answer_processor_set.remove(ap)

    def get_current_visible_answer_ids(self):
        try:
            ids = [a.id for a in self.question.answers]
            return ids
        except Exception as e:
            print(e)
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
                print('get new answer failed')
                new_ids = self.get_archived_visible_answer_ids()
                raise e
            deleted_ids = self.get_archived_visible_answer_ids().difference(new_ids)
            for i in deleted_ids:
                print('new deleted answer')
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
        self.excerpt = self.answer.excerpt
        self.content = self.answer.content
        self.database.insert_answer(
            self.answer_id, self.question_id, self.author_id, self.url, self.excerpt, self.content
        )
        author = self.answer.author
        self.database.insert_user(author.id, author.name, uid_to_url(author.id))

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
            if not self.stop:
                if c.id in comment_ids:
                    self.database.insert_comment(
                        c.created_time, c.content,
                        c.id, self.answer_id, self.author_id, self.question_id,
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
            print('new deleted comment')
            self.database.mark_comment_deleted(self.question_id, self.answer_id, i)
        self.append_added_comments(added_ids)
