#!/usr/bin/env python
# -*- coding: utf-8 -*-

import urllib.parse
import random
import hashlib
import http.client
import json


class YouDaoSpider(object):

    """
    Use YouDao dictionary API.
    API url : http://openapi.youdao.com/api
    API doc url：http://ai.youdao.com/docs/doc-trans-api.s
    Language support : 中文zh-CHS、日文ja、英文En、韩文ko、法文fr、俄文ru、葡萄牙文pt、西班牙文es
    """
    params = {
        'appKey': '566392cad5fa8829',
        'secretKey': 'RF2jySGxOKDYO2WT1H78vu7JeKq6KvL9',
        'fromLang': 'En',
        'toLang': 'zh-CHS',
        'salt': str(random.randint(1, 65536)),
    }

    def __init__(self, word):
        self.word = word
        self.result = None
        self.api_url = None

    def get_result(self):
        """
        Get translation result via YouDao API
        :return: dict translation results
        """
        http_client = None

        # Construct  api url
        sign = self.params['appKey'] + self.word + self.params['salt'] + self.params['secretKey']
        m1 = hashlib.md5()
        m1.update(sign.encode('utf-8'))
        sign = m1.hexdigest()
        api_url = '/api?appKey=' + self.params['appKey'] + '&q=' + urllib.parse.quote(self.word) + '&from=' + self.params['fromLang'] + '&to=' + self.params['toLang'] + '&salt=' + self.params['salt'] + '&sign=' + sign
        try:
            # Http request
            http_client = http.client.HTTPConnection('openapi.youdao.com')
            http_client.request('GET', api_url)

            # response是HTTPResponse对象
            response = http_client.getresponse()
            # response.read().decode()[type:str] ----> result[type:dict]
            self.result = json.JSONDecoder().decode(response.read().decode())
            return self.result
        except Exception as e:
            print('error:', e)
        finally:
            if http_client:
                http_client.close()


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



