def qid_to_url(qid):
    return 'https://www.zhihu.com/question/' + str(qid)

def aid_to_url(qid, aid):
    return 'https://www.zhihu.com/question/%s/answer/%s' % (str(qid), str(aid))
