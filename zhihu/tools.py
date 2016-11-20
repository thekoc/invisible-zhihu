def qid_to_url(qid):
    return 'https://www.zhihu.com/question/{qid}'.format(qid=qid)


def aid_to_url(qid, aid):
    return 'https://www.zhihu.com/question/{qid}/answer/{aid}'.format(qid=qid, aid=aid)


def uid_to_url(uid):
    return 'https://www.zhihu.com/people/{uid}'.format(uid=uid)


def tid_to_url(tid):
    return 'https://www.zhihu.com/topic/{tid}'.format(tid=tid)
