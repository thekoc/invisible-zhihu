import re


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
