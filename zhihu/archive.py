import sqlite3
import tools


class ZhihuDatabase(object):
    """
    A database use sqlite.
    """

    def __init__(self, dbname):
        self.connect = sqlite3.connect(dbname)
        self.cursor = cursor = self.connect.cursor()
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS USER
            (ID INT PRIMARY KEY, NAME TEXT, URL TEXT)
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
            (ID INT, QUESTION_ID INT, AUTHOR_ID INT,
            URL TEXT, EXCERPT TEXT, CONTENT TEXT, DELETED INT,
            FOREIGN KEY(QUESTION_ID) REFERENCES QUESTION(ID) ON DELETE CASCADE,
            FOREIGN KEY(AUTHOR_ID) REFERENCES USER(ID) ON DELETE CASCADE,
            PRIMARY KEY (QUESTION_ID, ID))
            """
        )

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS COMMENT
            (ID INT, ANSWER_ID INT, QUESTION_ID INT,
            AUTHOR_ID INT,REPLY_TO_AUTHOR_ID INT,
            CONTENT TEXT, CREATED_TIME INT, DELETED INT,
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
        self.cursor.close()
        self.connect.commit()
        self.connect.close()

    def insert_topic(self, topic_id, name, url):
        cursor = self.cursor
        cursor.execute(
            """
            INSERT OR IGNORE INTO TOPIC
            (ID, NAME, URL)
            VALUES (:tid, :name, :url)
            """,
            {'tid': topic_id, 'name': name, 'url': url}
        )
        self.connect.commit()

    def insert_question(self, question_id, title, url, excerpt, deleted=False):
        cursor = self.cursor
        cursor.execute(
            """
            INSERT OR IGNORE INTO QUESTION
            (ID, TITLE, URL, EXCERPT, DELETED)
            VALUES (:qid, :title, :url, :excerpt, :deleted)
            """,
            {
                'qid': question_id, 'title': title, 'url': url,
                'excerpt': excerpt, 'deleted': 1 if deleted else 0
            }
        )
        self.connect.commit()

    def insert_answer(self, answer_id, question_id, author_id, url, excerpt, content, deleted=False):
        self.cursor.execute(
            """
            INSERT OR IGNORE INTO ANSWER
            (ID, QUESTION_ID, AUTHOR_ID, URL, EXCERPT, CONTENT, DELETED)
            VALUES (:answer_id, :question_id, :author_id, :url, :excerpt, :content, :deleted)
            """,
            {
                'answer_id': answer_id, 'question_id': question_id, 'author_id': author_id,
                'url': url, 'excerpt': excerpt, 'content': content, 'deleted': 1 if deleted else 0
            }
        )
        self.connect.commit()

    def insert_comment(
            self, created_time, content,
            comment_id, answer_id, author_id, question_id, reply_to_id=None,
            deleted=False):
        cursor = self.cursor
        cursor.execute(
            """
            INSERT OR IGNORE INTO COMMENT
            (ID, ANSWER_ID, QUESTION_ID, AUTHOR_ID, REPLY_TO_AUTHOR_ID,
            CONTENT, CREATED_TIME, DELETED)
            VALUES (:cid, :answer_id, :qid, :author_id, :reply, :content, :c_time, :deleted)
            """,
            {
                'cid': comment_id, 'answer_id': answer_id, 'qid': question_id,
                'author_id': author_id, 'reply': reply_to_id,
                'content': content, 'c_time': created_time,
                'deleted': 1 if deleted else 0
            }
        )
        self.connect.commit()

    def insert_relationship_topic_question_id(self, topic_id, question_id):
        self.cursor.execute(
            """
            INSERT OR IGNORE INTO RELATIONSHIP_TOPIC_QUESTION_ID
            (TOPIC_ID, QUESTION_ID)
            VALUES (:tid, :qid)
            """,
            {'tid': topic_id, 'qid': question_id}
        )
        self.connect.commit()

    def get_visible_answer_ids(self, question_id):
        ids = self.cursor.execute(
            """
            SELECT ID FROM ANSWER WHERE QUESTION_ID = :question_id AND DELETED = 0
            """,
            {'question_id': question_id}
        ).fetchall()
        return [i[0] for i in ids]

    def get_visible_comment_ids(self, answer_id):
        ids = self.cursor.execute(
            """
            SELECT ID FROM COMMENT WHERE ANSWER_ID = :answer_id AND DELETED = 0
            """,
            {'answer_id': answer_id}
        ).fetchall()
        return [i[0] for i in ids]

    def mark_answer_deleted(self, question_id, answer_id):
        self.cursor.execute(
            """
            UPDATE ANSWER SET DELETED = 1
            WHERE ID = :answer_id AND QUESTION_ID = :question_id
            """,
            {'question_id': question_id, 'answer_id': answer_id}
        )
        self.connect.commit()

    def mark_comment_deleted(self, question_id, answer_id, comment_id):
        self.cursor.execute(
            """
            UPDATE COMMENT SET DELETED = 1
            WHERE ID = :comment_id AND QUESTION_ID = :question_id AND ANSWER_ID = :answer_id
            """,
            {
                'question_id': question_id, 'answer_id': answer_id,
                'comment_id': comment_id
            }
        )
        self.connect.commit()

    def update_answer_content(self, answer_id, content):
        pass
