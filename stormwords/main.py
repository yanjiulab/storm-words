#!/usr/bin/env python3
# _*_ coding: utf-8 _*_

import os
import sys
import json
import getopt
from collections import deque
from .spider import YouDaoSpider
from termcolor import colored
import urllib.request as requests


def show_help():
    print("""
    控制台下的storm-words 版本{ver}
    新增对StarDict 的支持，默认优先使用StarDict
    没有词典结果时自动使用有道翻译,
    查询结果会保存到sqlite数据库中,
    使用方法 yd [-y] [-n] [-l] [--clear] [-d word] [-s path] [--help] word
    [-y] 使用YouDaoAPI
    [-n] 强制重新获取, 不管数据库中是否已经保存
    [-l] 列出数据库中保存的所有单词
    [--clear] 清空数据库
    [-d word] 删除数据库中某个单词
    [-s path] 设置stardict词典路径
    [--help] 显示帮助信息
    """)


def show_result(result):
    """
    show translate result in a readable way.
    :param result: dict with the same json format as YouDao API had returned.
    """
    if 'stardict' in result:
        print(colored('StarDict:', 'blue'))
        print(result['stardict'])
        return

    if result['errorCode'] != '0':
        print(colored(result['errorCode'], 'red'))
    else:
        print(colored('[%s]' % result['query'], 'magenta'))
        if 'basic' in result:
            if 'us-phonetic' in result['basic']:
                print(colored('美音:', 'blue'), colored('[%s]' % result['basic']['us-phonetic'], 'green'),)
            if 'uk-phonetic' in result['basic']:
                print(colored('英音:', 'blue'), colored('[%s]' % result['basic']['uk-phonetic'], 'green'))
            if 'phonetic' in result['basic']:
                print(colored('拼音:', 'blue'), colored('[%s]' % result['basic']['phonetic'], 'green'))

            print(colored('基本词典:', 'blue'))
            print(colored('\t'+'\n\t'.join(result['basic']['explains']), 'yellow'))

        if 'translation' in result:
            print(colored('有道翻译:', 'blue'))
            print(colored('\t'+'\n\t'.join(result['translation']), 'cyan'))

        if 'web' in result:
            print(colored('网络释义:', 'blue'))
            for item in result['web']:
                print('\t' + colored(item['key'], 'cyan') + ': ' + '; '.join(item['value']))


def query(keyword):

    test = YouDaoSpider(keyword)
    result = test.get_result()
    show_result(result)


def main():
    try:
        options, args = getopt.getopt(sys.argv[1:], 'anld:cvs:y', ['help'])
    except getopt.GetoptError:
        options = [('--help', '')]
    if ('--help', '') in options:
        show_help()
        return

    keyword = ' '.join(args)

    if not keyword:
        show_help()
    else:
        query(keyword)

if __name__ == '__main__':
    # query('happy')
    # for p in sys.path:
    #     print(p, ',')
    main()

