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
        req = s.get('https://www.zhihu.com/topic/19551424/newest')
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
                    'visible_answer_ids': self.get_visible_answer_ids(),
                }
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
            if not a.suggest_edit.status:
                print('newfile')
                a = AnswerProcessor(a, self.answer_directory)
                a.update()


    def get_visible_answer_ids(self):
        ids = [a.id for a in self.question.answers if not a.suggest_edit.status]
        return ids

    def update(self):
        if False:
            self.status['deleted'] = True
        else:
            try:
                new_ids = set(self.get_visible_answer_ids())
            except:
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
        self.answer = answer
        self.work_directory = os.path.join(directory, str(answer.id) + '.answer')
        self.deleted_comment_directory = os.path.join(self.work_directory, 'deleted_comments')
        self.answer_path = os.path.join(self.work_directory, 'answer.html')
        for d in [self.work_directory, self.deleted_comment_directory]:
            if not os.path.isdir(d):
                os.mkdir(d)

    def html(self):
        def people_to_tag(people):
            info = BeautifulSoup('', 'html.parser').new_tag('a', href='https://www.zhihu.com/people/' + str(people.id))
            info.string = people.name
            return info
        soup = BeautifulSoup('', 'html.parser')
        title = soup.new_tag('div', class_='title')
        title.string = '问题: '
        title_url = soup.new_tag('a', href=qid_to_url(self.answer.question.id))
        title_url.string = self.answer.question.title
        title.append(title_url)
        soup.append(title)

        author = soup.new_tag('div', class_='author')
        author.string = '作者: '
        author.append(people_to_tag(self.answer.author))
        soup.append(author)

        content = soup.new_tag('div', class_='content')
        content.string = '答案: '
        content.append(BeautifulSoup(self.answer.content, 'html.parser'))
        soup.append(content)

        comments = soup.new_tag('div', class_='comments')
        comments.string = '评论: '
        for c in self.answer.comments:
            comment = soup.new_tag('div', class_='comment', id=str(c.id))
            if c.reply_to:
                reply = soup.new_tag('div', class_='reply')
                reply.string = '回复: '
                reply.append(people_to_tag(c.reply_to))

            comment_author = soup.new_tag('div', class_='comment_author')
            comment_author.append(people_to_tag(c.author))
            comment.append(comment_author)

            comment_content = soup.new_tag('div', class_='comment_content')
            comment_content.append(BeautifulSoup(c.content, 'html.parser'))
            comment.append(comment_content)

            comments.append(comment)
        soup.append(comments)
        return soup.prettify()

    def update(self):
        if not os.path.isfile(self.answer_path):
            with open(self.answer_path, 'w') as f:
                f.write(self.html())
