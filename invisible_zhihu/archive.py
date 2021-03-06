import sqlite3
from . import tools
import logging
import time
from threading import Lock
from threading import Thread
from .tools import Actor
from .tools import singleton

log = logging.getLogger(__name__)


class SQLActor(Actor):
    import sqlite3
    def __init__(self, *args, **kwargs):
        super(SQLActor, self).__init__()
        kwargs.update({'check_same_thread': False})
        self.conn = sqlite3.connect(*args, **kwargs)
        self.cursor = self.conn.cursor()

    def run(self):
        while True:
            try:
                msg = self.recv()
                if msg == ('commit',):
                    pass
                else:
                    cursor = self.conn.cursor()
                    args, kwargs = msg
                    cursor.execute(*args, **kwargs)
            except Exception as e:
                raise e


    def send(self, msg: tuple):
        super(SQLActor, self).send(msg)

    def __del__(self):
        self.cursor.close()
        self.conn.close()


@singleton
class TestSQL(object):
    import sqlite3
    def __init__(self, *args, **kwargs):
        self.args = args
        self.kwargs = kwargs
        self.actor = SQLActor(*args, **kwargs)
        self.actor.start()

    def execute(self, *args, **kwargs):
        sql = args[0]
        if sql.strip().lower().startswith('select'):
            conn = sqlite3.connect(*self.args, **self.kwargs)
            c = conn.cursor()
            return c.execute(*args, **kwargs)
        else:
            self.actor.send((args, kwargs))

    def commit(self):
        self.actor.send(('commit',))



class ZhihuDatabase(object):
    """A database use sqlite.

    Placeholder
    """

    def __init__(self, dbname):
        self._connect = TestSQL(dbname, check_same_thread=False, timeout=5)
        self._cursor = cursor = self._connect
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS USER
            (ID TEXT PRIMARY KEY, NAME TEXT, URL TEXT)
            """
        )

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS TOPIC
            (ID INT PRIMARY KEY, NAME TEXT, URL TEXT)
            """
        )

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS QUESTION
            (ID INT PRIMARY KEY, TITLE TEXT, URL TEXT,
            EXCERPT TEXT, DELETED INT)
            """
        )

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS ANSWER
            (ID INT, QUESTION_ID INT, AUTHOR_ID TEXT,
            URL TEXT, EXCERPT TEXT, CONTENT TEXT, VOTEUP_COUNT INT, THANKS_COUNT INT,
            CREATED_TIME INT, UPDATED_TIME INT, ADDED_TIME INT,
            SUGGEST_EDIT INT, DELETED INT,
            FOREIGN KEY(QUESTION_ID) REFERENCES QUESTION(ID) ON DELETE CASCADE,
            FOREIGN KEY(AUTHOR_ID) REFERENCES USER(ID) ON DELETE CASCADE,
            PRIMARY KEY (QUESTION_ID, ID, UPDATED_TIME))
            """
        )

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS COMMENT
            (ID INT, ANSWER_ID INT, QUESTION_ID INT,
            AUTHOR_ID TEXT, REPLY_TO_AUTHOR_ID TEXT,
            CONTENT TEXT, CREATED_TIME INT, ADDED_TIME INT, DELETED INT,
            FOREIGN KEY(ANSWER_ID) REFERENCES ANSWER(ID) ON DELETE CASCADE,
            FOREIGN KEY(AUTHOR_ID) REFERENCES USER(ID) ON DELETE CASCADE,
            FOREIGN KEY(REPLY_TO_AUTHOR_ID) REFERENCES USER(ID) ON DELETE CASCADE,
            PRIMARY KEY(QUESTION_ID, ANSWER_ID, ID))
            """
        )

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS RELATIONSHIP_TOPIC_QUESTION_ID
            (TOPIC_ID INT, QUESTION_ID INT,
            PRIMARY KEY (TOPIC_ID, QUESTION_ID))
            """
        )

    def __del__(self):
        """Save data on close."""

    def insert_topic(self, topic_id, name, url, auto_commit=True):
        cursor = self._cursor
        try:
            cursor.execute(
                """
                INSERT OR IGNORE INTO TOPIC
                (ID, NAME, URL)
                VALUES (:tid, :name, :url);
                """,
                {'tid': topic_id, 'name': name, 'url': url}
            )
        except Exception as e:
            log.error('In insert_topic: ' + str(e))
            raise e
        finally:
            if auto_commit:
                self._connect.commit()

    def insert_user(self, user_id: str, name, url, auto_commit=True):
        cursor = self._cursor
        try:
            cursor.execute(
                """
                INSERT OR IGNORE INTO USER
                (ID, NAME, URL)
                VALUES (:uid, :name, :url);
                """,
                {'uid': user_id, 'name': name, 'url': url}
            )
        except Exception as e:
            log.error('In insert_user: ' + str(e))
            raise e
        finally:
            if auto_commit:
                self._connect.commit()

    def insert_question(self, question_id, title, url, excerpt, deleted=False, auto_commit=True):
        cursor = self._cursor
        try:
            cursor.execute(
                """
                INSERT OR IGNORE INTO QUESTION
                (ID, TITLE, URL, EXCERPT, DELETED)
                VALUES (:qid, :title, :url, :excerpt, :deleted);
                """,
                {
                    'qid': question_id, 'title': title, 'url': url,
                    'excerpt': excerpt, 'deleted': 1 if deleted else 0
                }
            )
        except Exception as e:
            log.error('In insert_question: ' + str(e))
            raise e
        finally:
            if auto_commit:
                self._connect.commit()

    def insert_answer(
            self, answer_id, question_id, author_id,
            url, excerpt, content, voteup_count, thanks_count,
            created_time, updated_time, added_time, suggest_edit,
            deleted=False, auto_commit=True, ):
        try:
            self._cursor.execute(
                """
                INSERT OR IGNORE INTO ANSWER
                (ID, QUESTION_ID, AUTHOR_ID,
                URL, EXCERPT, CONTENT, VOTEUP_COUNT, THANKS_COUNT,
                CREATED_TIME, UPDATED_TIME, ADDED_TIME, SUGGEST_EDIT, DELETED)
                VALUES (:answer_id, :question_id, :author_id,
                        :url, :excerpt, :content, :voteup_count, :thanks_count,
                        :created_time, :updated_time, :added_time,
                        :suggest_edit, :deleted);
                """,
                {
                    'answer_id': answer_id,
                    'question_id': question_id,
                    'author_id': author_id,
                    'url': url, 'excerpt': excerpt, 'content': content,
                    'voteup_count': voteup_count, 'thanks_count': thanks_count,
                    'created_time': created_time,
                    'updated_time': updated_time,
                    'added_time': added_time,
                    'suggest_edit': 1 if suggest_edit else 0,
                    'deleted': 1 if deleted else 0
                }
            )
        except Exception as e:
            log.error('In insert_answer: {}, id is {}'.format(str(e), answer_id))
            raise e
        finally:
            if auto_commit:
                self._connect.commit()

    def insert_comment(
            self, created_time, added_time, content,
            comment_id, answer_id, author_id, question_id, reply_to_id=None,
            deleted=False, auto_commit=True):
        cursor = self._cursor
        try:
            cursor.execute(
                """
                INSERT OR IGNORE INTO COMMENT
                (ID, ANSWER_ID, QUESTION_ID, AUTHOR_ID, REPLY_TO_AUTHOR_ID,
                CONTENT, CREATED_TIME, ADDED_TIME, DELETED)
                VALUES (:cid, :answer_id, :qid, :author_id,
                        :reply, :content, :c_time, :added_time, :deleted);
                """,
                {
                    'cid': comment_id, 'answer_id': answer_id, 'qid': question_id,
                    'author_id': author_id, 'reply': reply_to_id,
                    'content': content, 'c_time': created_time, 'added_time': added_time,
                    'deleted': 1 if deleted else 0
                }
            )
        except Exception as e:
            log.error('In insert_comment: ' + str(e))
            raise e
        finally:
            if auto_commit:
                self._connect.commit()

    def insert_relationship_topic_question_id(self, topic_id, question_id, auto_commit=True):
        try:
            self._cursor.execute(
                """
                INSERT OR IGNORE INTO RELATIONSHIP_TOPIC_QUESTION_ID
                (TOPIC_ID, QUESTION_ID)
                VALUES (:tid, :qid);
                """,
                {'tid': topic_id, 'qid': question_id}
            )
        except Exception as e:
            log.error('In insert_relationship_topic_question_id: ' + str(e))
            raise e
        finally:
            if auto_commit:
                self._connect.commit()

    def mark_answer_deleted(self, question_id, answer_id, deleted=True, auto_commit=True):
        try:
            self._cursor.execute(
                """
                UPDATE ANSWER SET DELETED = :deleted
                WHERE ID = :answer_id AND QUESTION_ID = :question_id;
                """,
                {
                    'question_id': question_id, 'answer_id': answer_id,
                    'deleted': 1 if deleted else 0
                }
            )
        except Exception as e:
            log.error('In mark_answer_deleted: ' + str(e))
            raise e
        finally:
            if auto_commit:
                self._connect.commit()

    def mark_comment_deleted(self, question_id, answer_id, comment_id, auto_commit=True):
        try:
            self._cursor.execute(
                """
                UPDATE COMMENT SET DELETED = 1
                WHERE ID = :comment_id AND QUESTION_ID = :question_id AND ANSWER_ID = :answer_id;
                """,
                {
                    'question_id': question_id, 'answer_id': answer_id,
                    'comment_id': comment_id
                }
            )
        except Exception as e:
            log.error('In mark_comment_deleted: ' + str(e))
            raise e
        finally:
            if auto_commit:
                self._connect.commit()

    def get_visible_answer_ids(self, question_id):
        ids = self._cursor.execute(
            """
            SELECT ID FROM ANSWER WHERE QUESTION_ID = :question_id AND DELETED = 0
            """,
            {'question_id': question_id}
        ).fetchall()
        return [i[0] for i in ids]

    def get_visible_comment_ids(self, answer_id):
        ids = self._cursor.execute(
            """
            SELECT ID FROM COMMENT WHERE ANSWER_ID = :answer_id AND DELETED = 0
            """,
            {'answer_id': answer_id}
        ).fetchall()
        return [i[0] for i in ids]

    def get_question_urls(self):
        urls = self._cursor.execute(
            """
            SELECT URL FROM QUESTION
            """
        )
        return [u[0] for u in urls]

    def get_user(self, user_id, default=None):
        """Get a user row in the USER table.

        Args:
            user_id (int): The id of the user.
            default (object, optional): Return this value if not found.
                Defaults to None.

        Returns:
            tuple: If found, the return value will be like: (ID, NAME, URL)
            None: If the default argument was not given.
        """
        results = self._cursor.execute(
            """
            SELECT * FROM USER WHERE ID = :uid
            """,
            {'uid': user_id}
        ).fetchall()
        return results[0] if results else default

    def get_comment(self, question_id, answer_id, comment_id, default=None):
        """Get a comment row in the COMMENT table.

        Returns:
            tuple: If found, the return value will be like:
                (ID, ANSWER_ID, QUESTION_ID, AUTHOR_ID, REPLY_TO_AUTHOR_ID,
                CONTENT, CREATED_TIME, ADDED_TIME, DELETED)
            None: If the default argument was not given.
        """
        results = self._cursor.execute(
            """
            SELECT * FROM COMMENT
            WHERE ID = :cid AND QUESTION_ID = :qid AND ANSWER_ID = :aid
            """,
            {'cid': comment_id, 'aid': answer_id, 'qid': question_id}
        ).fetchall()
        if results:
            result = results[0]
            return result[:-1] + (True if result[-1] == 1 else False,)
        else:
            return default

    def get_comments(self, question_id, answer_id, default=None):
        """Get comments under the answer.

        Returns:
            A list that contains tuple like folloing:
                (ID, ANSWER_ID, QUESTION_ID, AUTHOR_ID, REPLY_TO_AUTHOR_ID,
                CONTENT, CREATED_TIME, ADDED_TIME, DELETED)
        """
        results = self._cursor.execute(
            """
            SELECT * FROM COMMENT
            WHERE QUESTION_ID = :qid AND ANSWER_ID = :aid
            """,
            {'aid': answer_id, 'qid': question_id}
        ).fetchall()
        return results if default is None else default

    def get_answer(self, question_id, answer_id, default=None, updated_time=None):
        """Get an answer row in the ANSWER table.

        Args:
            question_id (int), answer_id (int), default (int, optional)
            updated_time (int, optional): If not given, it will return the newest answer.

        Returns:
            tuple: If found, looks like:
                (ID, QUESTION_ID, AUTHOR_ID,
                URL, EXCERPT, CONTENT, VOTEUP_COUNT, THANKS_COUNT,
                CREATED_TIME, UPDATED_TIME, ADDED_TIME,
                SUGGEST_EDIT, DELETED)
        """
        results = self.get_answer_history(question_id, answer_id)
        if updated_time:
            results = [i for i in results if i[-3] == updated_time]
        if results:
            result = list(results[0])
            return result[:-2] + [True if i == 1 else False for i in result[-2:]]
        else:
            return default

    def get_answer_history(self, question_id, answer_id):
        """Get a list that contain all the version of this answer.

        Returns:
            list(tuple): Each tuple will be like:
                (ID, QUESTION_ID, AUTHOR_ID,
                URL, EXCERPT, CONTENT, VOTEUP_COUNT, THANKS_COUNT,
                CREATED_TIME, UPDATED_TIME, ADDED_TIME,
                SUGGEST_EDIT, DELETED)
        """
        results = self._cursor.execute(
            """
            SELECT * FROM ANSWER
            WHERE ID = :aid AND QUESTION_ID = :qid
            ORDER BY UPDATED_TIME DESC
            """,
            {'aid': answer_id, 'qid': question_id}
        ).fetchall()
        return results

    def get_deleted_answers(self):
        """Get the answers marked as deleted.

        Returns:
            list(tuple): Each tuple will be like:
                (ID, QUESTION_ID, AUTHOR_ID,
                URL, EXCERPT, CONTENT, VOTEUP_COUNT, THANKS_COUNT,
                CREATED_TIME, UPDATED_TIME, ADDED_TIME,
                SUGGEST_EDIT, DELETED)
        """
        cursor = self._connect.cursor()
        flag = True
        cursor.execute(
            """
            SELECT * FROM ANSWER
            WHERE DELETED = 1
            """
        )
        while flag:
            a = cursor.fetchone()
            if a is None:
                flag = False
            else:
                yield a
        cursor.close()

    def get_question(self, question_id, default=None):
        """Get a question row in the QUESTION table.

        Returns:
            tuple: If found, looks line:
                (ID, TITLE, URL, EXCERPT, DELETED)
        """
        results = self._cursor.execute(
            """
            SELECT * FROM QUESTION WHERE ID = :qid
            """,
            {'qid': question_id}
        ).fetchall()
        if results:
            result = results[0]
            return result[:-1] + (True if result[-1] == 1 else False,)
        else:
            return default

    def commit(self):
        self._connect.commit()

    def update_answer_content(self, answer_id, content):
        pass
