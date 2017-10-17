#!/usr/bin/env python
# -*- coding: utf-8 -*-

import urllib.parse
import random
import hashlib
import requests
import http.client
import json
import re
from bs4 import BeautifulSoup
from stormwords.config import APP_KEY, SECRET_KEY


class YouDaoSpider(object):

    """
    Use YouDao dictionary API.
    API url : http://openapi.youdao.com/api
    API doc url：http://ai.youdao.com/docs/doc-trans-api.s
    web_url : http://dict.youdao.com/search?keyfrom=dict.top&q=
    translation_url : http://fanyi.youdao.com/translate?keyfrom=dict.top&i=
    Language support : 中文zh-CHS、日文ja、英文En、韩文ko、法文fr、俄文ru、葡萄牙文pt、西班牙文es
    """
    params = {
        'appKey': APP_KEY,
        'secretKey': SECRET_KEY,
        'fromLang': 'En',
        'toLang': 'zh-CHS',
        'salt': str(random.randint(1, 65536)),
    }

    web_url = 'http://dict.youdao.com/search?keyfrom=dict.top&q='
    translation_url = 'http://fanyi.youdao.com/translate?keyfrom=dict.top&i='

    def __init__(self, word):
        self.word = word
        self.result = {
            "query": "",
            "errorCode": '0'
        }
        self.api_url = None

    def make_api_url(self):
        # Construct api url
        sign = self.params['appKey'] + self.word + self.params['salt'] + self.params['secretKey']
        m1 = hashlib.md5()
        m1.update(sign.encode('utf-8'))
        sign = m1.hexdigest()
        api_url = '/api?appKey=' + self.params['appKey'] + '&q=' + urllib.parse.quote(self.word) + '&from=' + \
                  self.params['fromLang'] + '&to=' + self.params['toLang'] + '&salt=' + self.params[
                      'salt'] + '&sign=' + sign
        return api_url

    def get_result(self, use_api=False):
        """
        Get translation result via YouDao API or YouDao web by default
        :return: translation results -- dict
        """
        if use_api:
            http_client = None
            api_url = self.make_api_url()
            try:
                http_client = http.client.HTTPConnection('openapi.youdao.com')  # Http request
                http_client.request('GET', api_url)
                response = http_client.getresponse()  # response是HTTPResponse对象
                self.result = json.JSONDecoder().decode(response.read().decode())  # response.read().decode()[type:str] ----> result[type:dict]
            except Exception as e:
                print('error:', e)
            finally:
                if http_client:
                    http_client.close()
        else:
            r = requests.get(self.web_url + self.word)
            r.raise_for_status()
            self.parse_html(r.text)
        return self.result

    def parse_html(self, html):
        """
        to parse the content of the YouDao dict web
        :param html  -- txt
        :return:result -- dict
        """
        soup = BeautifulSoup(html, "lxml")
        root = soup.find(id='results-contents')

        # query
        keyword = root.find(class_='keyword')
        if not keyword:
            self.result['query'] = self.word
        else:
            self.result['query'] = keyword.string

        # basic
        basic = root.find(id='phrsListTab')
        if basic:
            trans = basic.find(class_='trans-container')
            if trans:
                self.result['basic'] = {}
                self.result['basic']['explains'] = [tran.string for tran in trans.find_all('li')]
                # 中文
                if len(self.result['basic']['explains']) == 0:
                    exp = trans.find(class_='wordGroup').stripped_strings
                    self.result['basic']['explains'].append(' '.join(exp))

                # 音标
                phons = basic(class_='phonetic', limit=2)
                if len(phons) == 2:
                    self.result['basic']['uk-phonetic'], self.result['basic']['us-phonetic'] = \
                        [p.string[1:-1] for p in phons]
                elif len(phons) == 1:
                    self.result['basic']['phonetic'] = phons[0].string[1:-1]

        # translation
        if 'basic' not in self.result:
            self.result['translation'] = self.get_translation(self.word)

        # web
        web = root.find(id='webPhrase')
        if web:
            self.result['web'] = [
                {
                    'key': wordgroup.find(class_='search-js').string.strip(),
                    'value': [v.strip() for v in wordgroup.find('span').next_sibling.split(';')]
                } for wordgroup in web.find_all(class_='wordGroup', limit=4)
                ]

    def get_translation(self, word):
        """
        to translate word by web translator
        :param word -- str
        :return:result -- list
        """
        r = requests.get(self.translation_url+word)
        if r.status_code != requests.codes.ok:
            return None
        pattern = re.compile(r'"translateResult":\[(\[.+\])\]')
        m = pattern.search(r.text)
        result = json.loads(m.group(1))
        return [item['tgt'] for item in result]


if __name__ == '__main__':
    test = YouDaoSpider('test')
    print(test.get_result())


# Output structure
# 当FROM和TO的值都在{zh-CHS, EN}范围内时
# {
#   "errorCode":"0",
#   "query":"good", //查询正确时，一定存在
#   "translation": [ //查询正确时一定存在
#       "好"
#   ],
#   "basic":{ // 有道词典-基本词典,查词时才有
#       "phonetic":"gʊd"
#       "uk-phonetic":"gʊd" //英式发音
#       "us-phonetic":"ɡʊd" //美式发音
#       "explains":[
#           "好处",
#           "好的"
#           "好"
#       ]
#   },
#   "web":[ // 有道词典-网络释义，该结果不一定存在
#       {
#           "key":"good",
#           "value":["良好","善","美好"]
#       },
#       {...}
#   ]
#   ],
#   "dict":{
#       "url":"yddict://m.youdao.com/dict?le=eng&q=good"
#   },
#   "webdict":{
#       "url":"http://m.youdao.com/dict?le=eng&q=good"
#   },
#   "l":"EN2zh-CHS"
# }

# 当FROM和TO的值有在{zh-CHS, EN}范围外的时候
# {
#    "errorCode": "0",
#    "translation": ["大丈夫です"] //小语种翻译，一定存在
#    "dict":{
#        "url":"yddict://m.youdao.com/dict?le=jap&q=%E6%B2%A1%E5%85%B3%E7%B3%BB%E3%80%82"
#    },
#    "webdict":{
#        "url":"http://m.youdao.com/dict?le=jap&q=%E6%B2%A1%E5%85%B3%E7%B3%BB%E3%80%82"
#    },
#    "l":"zh-CHS2ja"
# }



