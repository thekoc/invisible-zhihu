from archive import ZhihuDatabase
from bs4 import BeautifulSoup
import os


class ZhihuReader():
    def __init__(self, database_name):
        self.database = ZhihuDatabase(database_name)

    def people_to_tag(self, people_id):
        soup = BeautifulSoup('', 'html.parser')
        info = self.database.get_user(people_id)
        if info:
            uid, name, url = info
            people_tag = soup.new_tag('a', href=url)
            people_tag.string = name
            return people_tag
        else:
            return soup

    def comment_to_tag(self, question_id, answer_id, comment_id):
        soup = BeautifulSoup('', 'html.parser')
        info = self.database.get_comment(question_id, answer_id, comment_id)
        if info:
            *args, author_id, reply_id, content, created_time, added_time, deleted = info
            comment_tag = soup.new_tag('div', **{'class': 'comment', 'id': comment_id})
            comment_author = soup.new_tag('div', **{'class': 'comment_author'})
            comment_author.append(self.people_to_tag(author_id))
            comment_tag.append(comment_author)

            if reply_id:
                reply = soup.new_tag('div', **{'class': 'reply'})
                reply.string = '回复: '
                reply.append(self.people_to_tag(reply_id))
                comment_tag.append(reply)
            comment_content = soup.new_tag('div', **{'class': 'comment_content'})
            comment_content.append(BeautifulSoup(content, 'html.parser'))
            if deleted:
                comment_content.string.wrap(soup.new_tag('del'))
            comment_tag.append(comment_content)
            return comment_tag
        else:
            return soup

    def answer_to_tag(self, question_id, answer_id):
        soup = BeautifulSoup('', 'html.parser')
        info = self.database.get_answer(question_id, answer_id)
        print(info)
        if info:
            *args, answer_author_id, answer_url, answer_excerpt, answer_content, voteup_count, thanks_count, created_time, updated_time, added_time, suggest_edit, answer_deleted = info
            qinfo = self.database.get_question(question_id)
            *args, question_title, question_url, question_excerpt, question_deleted = qinfo
            title = soup.new_tag('div', **{'class': 'title'})
            title.string = '问题: '
            title_url = soup.new_tag('a', href=question_url)
            title_url.string = question_title
            title.append(title_url)
            soup.append(title)

            author = soup.new_tag('div', **{'class': 'author'})
            author.string = '作者: '
            author.append(self.people_to_tag(answer_author_id))
            soup.append(author)

            content = soup.new_tag('div', **{'class': 'content'})
            content.string = '答案: '
            voteup_tag = soup.new_tag('div', **{'class': 'voteup'})
            voteup_tag.string = str(voteup_count)
            content.append(voteup_tag)
            content.append(BeautifulSoup(answer_content, 'html.parser'))
            soup.append(content)

            comments = soup.new_tag('div', **{'class': 'comments'})
            comments.string = '评论: '
            for c in self.database.get_comments(question_id, answer_id):
                print(c)
                cid, *args = c
                comments.append(self.comment_to_tag(question_id, answer_id, cid))
            soup.append(comments)
        return soup


def main():
    reeder = ZhihuReader('data/zhihu.db')
    print(reeder.answer_to_tag(31650313, 52820083))

if __name__ == '__main__':
    main()
