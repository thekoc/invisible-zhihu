from zhihu_oauth import ZhihuClient as OauthClient
from zhihu import ZhihuClient as WebClient
import os

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/45.0.2454.101 Safari/537.36',
}


class ZhihuClient(object):
    """A class that encapsulates true client for purposes of unification interface."""

    def __init__(self):
        self.cookie_path = 'cookies.json'
        self.token_path = 'token.pkl'
        self.oauth_client = OauthClient()
        self.web_client = WebClient()

    def login(self):
        if os.path.isfile(self.token_path):
            self.oauth_client.load_token(self.token_path)
        else:
            self.oauth_client.login_in_terminal()
            self.oauth_client.save_token(self.token_path)

        if os.path.isfile(self.cookie_path):
            self.web_client.login_with_cookies(self.cookie_path)
        else:
            self.web_client.create_cookies(self.cookie_path)

    def test(self):
        question = self.web_client.topic('https://www.zhihu.com/topic/20059699')
        for answer in question.answers:
            answer.save()
