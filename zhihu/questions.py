import requests
import os
import shutil
import json
import time
from bs4 import BeautifulSoup
from tools import qid_to_url

class QuestionSpider(object):
    def __init__(self, client):
        self.client = client

    def get_new_quetion_urls(self):
        question_urls = []
        s = requests.Session()
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/45.0.2454.101 Safari/537.36',
        }
        s.headers.update(headers)
        req = s.get('https://www.zhihu.com/topic/19673476/newest')
        soup = BeautifulSoup(req.text, 'html.parser')
        host = 'https://www.zhihu.com'
        for t in soup.find_all('a', class_='question_link'):
            question_urls.append(host + t['href'])
        return question_urls

class QuestionProcesser(object):
    def __init__(self, question):
            self.meta_info = None
            self.question = question
            self.url = qid_to_url(self.question.id)
            self.work_directory = str(self.question.id) + '.question'
            self.answer_directory = os.path.join(self.work_directory, 'answers')
            self.deleted_answer_directory = os.path.join(self.work_directory, 'deleted')
            self.meta_info_path = os.path.join(self.work_directory, 'meta_info.json')
            for d in [self.work_directory, self.answer_directory, self.deleted_answer_directory]:
                if not os.path.isdir(d):
                    os.mkdir(d)
            if not os.path.isfile(self.meta_info_path):
                self.meta_info = {
                    'question_info': {
                        'url': self.url,
                        'title': self.question.title,
                        'excerpt': self.question.excerpt
                    },
                    'visible_answer_ids': [],
                }
                self.meta_info['visible_answer_ids'] = self.get_visible_answer_ids()
            else:
                with open(self.meta_info_path) as f:
                    self.meta_info = json.load(f)

            self.visible_answer_ids = set(self.meta_info['visible_answer_ids'])

    def __del__(self):
        if self.meta_info:
            with open(self.meta_info_path, 'w') as f:
                json.dump(self.meta_info, f)

    def copy_to_deleted(self, answer_id):
        print('new_deleted_answer')
        path = os.path.join(self.answer_directory, str(answer_id) + '.answer')
        if not os.path.isdir(path):
            raise FileNotFoundError(path)
        else:
            shutil.copy(path, self.deleted_answer_directory)

    def update_answers(self):
        for a in self.question.answers:
            # if not a.suggest_edit.status:
            if True:
                a = AnswerProcessor(a, self.answer_directory)
                a.update()


    def get_visible_answer_ids(self):
        try:
            ids = [a.id for a in self.question.answers]
            return ids
        except Exception as e:
            print(e)
            return self.meta_info['visible_answer_ids']

    def update(self):
        if False:
            self.status['deleted'] = True
        else:
            try:
                new_ids = set(self.get_visible_answer_ids())
            except:
                print('get new answer failed')
                new_ids = self.visible_answer_ids
            deleted_ids = self.visible_answer_ids.difference(new_ids)
            for i in deleted_ids:
                self.copy_to_deleted(i)
            self.visible_answer_ids = new_ids
            self.meta_info['visible_answer_ids'] = list(new_ids)
            self.update_answers()

    def monitor(self, interval):
        while True:
            self.update()
            time.sleep(interval)


class AnswerProcessor(object):
    def __init__(self, answer, directory):
        self.meta_info = None
        self.answer = answer
        self.work_directory = os.path.join(directory, str(answer.id) + '.answer')
        self.deleted_comment_directory = os.path.join(self.work_directory, 'deleted_comments')
        self.answer_path = os.path.join(self.work_directory, 'answer.html')
        self.meta_info_path = os.path.join(self.work_directory, 'meta_info.json')

        for d in [self.work_directory, self.deleted_comment_directory]:
            if not os.path.isdir(d):
                os.makedirs(d)

        if not os.path.isfile(self.meta_info_path):
            self.meta_info = {
                'answer_info': {
                    'excerpt': self.answer.excerpt
                },
                'visible_comment_ids': [],
            }
            self.meta_info['visible_comment_ids'] = self.get_visible_comment_ids()
        else:
            with open(self.meta_info_path) as f:
                self.meta_info = json.load(f)

        self.visible_comment_ids = set(self.meta_info['visible_comment_ids'])

    def __del__(self):
        if self.meta_info:
            with open(self.meta_info_path, 'w') as f:
                json.dump(self.meta_info, f)

    def get_visible_comment_ids(self):
        try:
            ids = [c.id for c in self.answer.comments]
            return ids
        except Exception as e:
            print(e)
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

    def append_added_comments(self, comment_ids):
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

    def update(self):
        if not os.path.isfile(self.answer_path):
            with open(self.answer_path, 'w') as f:
                f.write(self.html())

        new_ids = set(self.get_visible_comment_ids())
        deleted_ids = self.visible_comment_ids.difference(new_ids)
        added_ids = new_ids.difference(self.visible_comment_ids)
        for i in deleted_ids:
            self.copy_comment_to_delete(i)
        self.append_added_comments(added_ids)
        self.visible_comment_ids = new_ids
        self.meta_info['visible_comment_ids'] = list(new_ids)
