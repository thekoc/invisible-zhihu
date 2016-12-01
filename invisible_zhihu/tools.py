import re
import requests
from .fake_zhihu import headers


class QuestionFormatError(Exception):
    """Raise when the question url is not the proper format."""


def qid_to_url(qid):
    if not isinstance(qid, int):
        raise TypeError('qid must be int.')
    return 'https://www.zhihu.com/question/{qid}'.format(qid=qid)


def aid_to_url(qid, aid):
    return 'https://www.zhihu.com/question/{qid}/answer/{aid}'.format(qid=qid, aid=aid)


def uid_to_url(uid):
    return 'https://www.zhihu.com/people/{uid}'.format(uid=uid)


def tid_to_url(tid):
    return 'https://www.zhihu.com/topic/{tid}'.format(tid=tid)


def url_to_qid(url):
    qid = re.findall(r'https://www\.zhihu\.com/question/\d+$', url)
    if qid:
        return qid[0]
    else:
        raise QuestionFormatError


def is_answer_deleted(question_id, answer_id):
    try:
        r = requests.get(aid_to_url(question_id, answer_id), allow_redirects=False, headers=headers)
    except Exception as e:
        raise e
    else:
        if r.status_code == 302:
            return True
        else:
            return False
