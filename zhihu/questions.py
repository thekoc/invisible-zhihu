import requests
import os
import shutil
import json
import time
from bs4 import BeautifulSoup
from tools import qid_to_url
from tools import aid_to_url
from tools import tid_to_url
from zhihu import ZhihuClient as WebClient
from archive import ZhihuDatabase


class QuestionSpider(object):
    def __init__(self):
        self.web_client = WebClient()
        self.cookies_path = 'cookies.json'
        self.cookies = json.load(open(self.cookies_path))
        if os.path.isfile(self.cookies_path):
            self.web_client.login_with_cookies(self.cookies_path)
        else:
            self.web_client.create_cookies(self.cookies_path)

    def get_new_quetion_urls(self):
        question_urls = []
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/45.0.2454.101 Safari/537.36',
        }
        s = requests.Session()
        req = s.get('https://www.zhihu.com/topic/19673476/newest', headers=headers, cookies=self.cookies)
        soup = BeautifulSoup(req.text, 'html.parser')
        host = 'https://www.zhihu.com'
        for t in soup.find_all('a', class_='question_link'):
            question_urls.append(host + t['href'])
        return question_urls
    # def get_new_quetion_urls(self):
    #     question_urls = []
    #     base_url = 'https://www.zhihu.com/question/'
    #     i = 0
    #     for q in self.web_client.topic('https://www.zhihu.com/topic/19673476/').hot_questions:
    #         i += 1
    #         if i < 60:
    #             question_urls.append(base_url + str(q.id))
    #         else:
    #             break
    #     return question_urls


class QuestionProcessor(object):
    def __init__(self, question):
        self.database = ZhihuDatabase('zhihu.db')
        self.meta_info = None
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
            ap = AnswerProcessor(a)
            ap.update()

    def get_current_visible_answer_ids(self):
        try:
            ids = [a.id for a in self.question.answers]
            return ids
        except Exception as e:
            print(e)
            return self.meta_info['visible_answer_ids']

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
                self.database.mark_answer_deleted(i)
            self.update_answers()


class AnswerProcessor(object):
    def __init__(self, answer):
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

    def get_archived_visible_comment_ids(self):
        ids = self.database.get_visible_comment_ids(self.answer_id)
        return set(ids)

    def get_current_visible_comment_ids(self):
        try:
            ids = [c.id for c in self.answer.comments]
            return ids
        except Exception as e:
            return self.meta_info['visible_comment_ids']

    def people_to_tag(self, people):
        people_tag = BeautifulSoup('', 'html.parser').new_tag('a', href='https://www.zhihu.com/people/' + str(people.id))
        people_tag.string = people.name
        return people_tag

    def comment_to_tag(self, comment):
        soup = BeautifulSoup('', 'html.parser')

        comment_tag = soup.new_tag('div', **{'class': 'comment', 'id': str(comment.id)})
        comment_author = soup.new_tag('div', **{'class': 'comment_author'})
        comment_author.append(self.people_to_tag(comment.author))
        comment_tag.append(comment_author)

        if comment.reply_to:
            reply = soup.new_tag('div', **{'class': 'reply'})
            reply.string = '回复: '
            reply.append(self.people_to_tag(comment.reply_to))
            comment_tag.append(reply)

        comment_content = soup.new_tag('div', **{'class': 'comment_content'})
        comment_content.append(BeautifulSoup(comment.content, 'html.parser'))
        comment_tag.append(comment_content)
        return comment_tag

    def html(self):
        soup = BeautifulSoup('', 'html.parser')
        title = soup.new_tag('div', **{'class': 'title'})
        title.string = '问题: '
        title_url = soup.new_tag('a', href=qid_to_url(self.answer.question.id))
        title_url.string = self.answer.question.title
        title.append(title_url)
        soup.append(title)

        author = soup.new_tag('div', **{'class': 'author'})
        author.string = '作者: '
        author.append(self.people_to_tag(self.answer.author))
        soup.append(author)

        content = soup.new_tag('div', **{'class': 'content'})
        content.string = '答案: '
        content.append(BeautifulSoup(self.answer.content, 'html.parser'))
        soup.append(content)

        comments = soup.new_tag('div', **{'class': 'comments'})
        comments.string = '评论: '
        for c in self.answer.comments:
            comments.append(self.comment_to_tag(c))
        soup.append(comments)
        return str(soup)

    def copy_comment_to_delete(self, comment_id):
        print('new_deleted_comment')
        with open(self.answer_path) as f:
            soup = BeautifulSoup(f.read(), 'html.parser')

        comment = soup.find('div', class_='comment', id=str(comment_id))
        content = comment.find('div', class_='comment_content')
        content.string.wrap(soup.new_tag('del'))
        path = os.path.join(self.deleted_comment_directory, str(comment_id) + '.html')
        with open(path, 'w') as f:
            f.write(comment.prettify())
        with open(self.answer_path, 'w') as f:
            f.write(soup.prettify())

    def append_added_comments_to_html(self, comment_ids):
        comment_tags = []
        for c in self.answer.comments:
            if c.id in comment_ids:
                comment_tags.append(self.comment_to_tag(c))

        with open(self.answer_path) as f:
            soup = BeautifulSoup(f.read(), 'html.parser')
        comments = soup.find('div', class_='comments')
        for t in comment_tags:
            comments.append(t)
        with open(self.answer_path, 'w') as f:
            f.write(soup.prettify())

    def append_added_comments(self, comment_ids):
        for c in self.answer.comments:
            if c.id in comment_ids:
                self.database.insert_comment(
                    c.created_time, c.content,
                    c.id, self.answer_id, self.author_id, self.question_id
                )

    def update(self):
        print('new answer')
        new_ids = set(self.get_current_visible_comment_ids())
        archived_ids = self.get_archived_visible_comment_ids()
        deleted_ids = archived_ids.difference(new_ids)
        added_ids = new_ids.difference(archived_ids)
        for i in deleted_ids:
            self.database.mark_comment_deleted(self.question_id, self.answer_id, i)
        self.append_added_comments(added_ids)
