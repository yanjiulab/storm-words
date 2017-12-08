#!/usr/bin/env python
# -*- coding: utf-8 -*-
import random
import hashlib
import requests
import json
import re
from bs4 import BeautifulSoup
from stormwords.config import APP_KEY, SECRET_KEY


class YouDaoSpider(object):
    """
    Use YouDao dictionary API.
    API url : http://openapi.youdao.com/api
    API doc url：http://ai.youdao.com/docs/doc-trans-api.s
    Web_url : http://dict.youdao.com/search?keyfrom=dict.top&q=
    Translation_url : http://fanyi.youdao.com/translate?keyfrom=dict.top&i=
    Language support : 中文zh-CHS、日文ja、英文En、韩文ko、法文fr、俄文ru、葡萄牙文pt、西班牙文es

    Query information:
        timeout: 3.1s (TCP packet retransmission window default value is 3)
        default language: zh-CHS to En | En to zh-CHS
    Query methods:
        YouDaoAI (optional)
        Web YouDao (default)
    Output structure:
        当FROM和TO的值都在{zh-CHS, EN}范围内时
        {
          "errorCode":"0",
          "query":"good", //查询正确时，一定存在
          "translation": [ //查询正确时一定存在
              "好"
          ],
          "basic":{ // 有道词典-基本词典,查词时才有
              "phonetic":"gʊd"
              "uk-phonetic":"gʊd" //英式发音
              "us-phonetic":"ɡʊd" //美式发音
              "explains":[
                  "好处",
                  "好的"
                  "好"
              ]
          },
          "web":[ // 有道词典-网络释义，该结果不一定存在
              {
                  "key":"good",
                  "value":["良好","善","美好"]
              },
              {...}
          ]
          ],
          "dict":{
              "url":"yddict://m.youdao.com/dict?le=eng&q=good"
          },
          "webdict":{
              "url":"http://m.youdao.com/dict?le=eng&q=good"
          },
          "l":"EN2zh-CHS"
        }

        当FROM和TO的值有在{zh-CHS, EN}范围外的时候
        {
           "errorCode": "0",
           "translation": ["大丈夫です"] //小语种翻译，一定存在
           "dict":{
               "url":"yddict://m.youdao.com/dict?le=jap&q=%E6%B2%A1%E5%85%B3%E7%B3%BB%E3%80%82"
           },
           "webdict":{
               "url":"http://m.youdao.com/dict?le=jap&q=%E6%B2%A1%E5%85%B3%E7%B3%BB%E3%80%82"
           },
           "l":"zh-CHS2ja"
        }

        Example:
            use `sw happy` to query word via web page crawler
            use `sw -a happy` to query word via official api
            use `sw -d happy` to delete word
            use `sw -f happy` to get a word with no database used
            use `sw -l` to list all the word in database
            use `sw -c` to clear database
            use `sw` or `sw --help` or `sw anything else` to get help
    """
    api_url = 'http://openapi.youdao.com/api'
    web_url = 'http://dict.youdao.com/search?keyfrom=dict.top&q='
    translation_url = 'http://fanyi.youdao.com/translate?keyfrom=dict.top&i='

    origin_api_params = {
        'appKey': APP_KEY,
        'secretKey': SECRET_KEY,
        'from': 'En',
        'to': 'zh-CHS',
        'salt': str(random.randint(1, 65536)),
    }

    def __init__(self, word):
        self.word = word
        self.result = {
            "query": "",
            "errorCode": '0'
        }
        self.api_params = {}

    def gen_api_params(self, api_params):
        """
        Generating api parameters
        :param api_params: original parameters
        :return: api_params: real parameters
        """
        sign = api_params['appKey'] + self.word + api_params['salt'] + api_params['secretKey']
        m1 = hashlib.md5()
        m1.update(sign.encode('utf-8'))
        sign = m1.hexdigest()

        api_params['sign'] = sign
        api_params['q'] = self.word
        del api_params['secretKey']

        return api_params

    def get_result(self, use_api=False, api_url=api_url):
        """
        Get translation result via YouDao API or YouDao web by default
        :return: translation results -- dict
        """

        if use_api:
            self.api_params = self.gen_api_params(self.origin_api_params)
            r = requests.get(api_url, params=self.api_params, timeout=3.1)
            r.raise_for_status()
            self.result = r.json()
        else:
            r = requests.get(self.web_url + self.word, timeout=3.1)
            r.raise_for_status()
            self.parse_html(r.text)
        return self.result

    def parse_html(self, html):
        """
        to parse the contents of the YouDao dict web version
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
        r = requests.get(self.translation_url + word)
        if r.status_code != requests.codes.ok:
            return None
        pattern = re.compile(r'"translateResult":\[(\[.+\])\]')
        m = pattern.search(r.text)
        result = json.loads(m.group(1))
        return [item['tgt'] for item in result]


if __name__ == '__main__':
    test = YouDaoSpider('value')
    print(test.get_result(False))



