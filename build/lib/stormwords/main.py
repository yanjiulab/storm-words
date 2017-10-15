#!/usr/bin/env python3
# _*_ coding: utf-8 _*_

import os
import sys
import json
import getopt
from collections import deque
from termcolor import colored
import urllib.request as requests
from stormwords.config_me import *
from stormwords.model import Word, db
from stormwords.spider import YouDaoSpider


def show_help():
    print("""
    控制台下的storm-words 版本{ver}
    查询结果会保存到SQLite数据库中,
    使用方法 yd [-n] [-l] [-c] [-d word] [--help] word
    [-n] 强制重新获取, 不管数据库中是否已经保存
    [-l] 列出数据库中保存的所有单词
    [-c] 清空数据库
    [-d word] 删除数据库中某个单词
    [--help] 显示帮助信息
    """.format(ver=VERSION))


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


def query(keyword, use_db=True):
    update_word = [True]    # need update words by default

    word = Word.get_word(keyword)
    result = {'query': keyword, 'errorCode': '60'}
    if use_db and word:
        result.update(json.loads(word.json_data))
        update_word[0] = False  # word exists in db already.
    elif update_word[0]:
        # 从database中没有匹配单词
        if not result['errorCode'] == '0':
            spider = YouDaoSpider(keyword)
            try:
                result.update(spider.get_result())
            except requests.HTTPError as e:
                print(colored('Network Error: %s' % e.message, 'red'))
                sys.exit()
        # Update database
        new_word = word if word else Word()
        new_word.keyword = keyword
        new_word.json_data = json.dumps(result)
        new_word.save()
    show_result(result)


def show_db_list():
    print(colored('保存在数据库中的单词及查询次数:', 'blue'))
    for word in Word.select():
        print(colored(word.keyword, 'cyan'), colored(str(word.count), 'green'))


def del_word(keyword):
    if keyword:
        try:
            word = Word.select().where(Word.keyword == keyword).get()
            word.delete_instance()
            print(colored('已删除{0}'.format(keyword), 'blue'))
        except Word.DoesNotExist:
            print(colored('没有找到{0}'.format(keyword), 'red'))
    else:
        count = Word.delete().execute()
        print(colored('共删除{0}个单词'.format(count), 'blue'))


def main():
    prepare()
    db.connect()
    # create table of of word
    if db.get_tables()[0] == 'word':
        pass
    else:
        Word.create_table()

    try:
        options, args = getopt.getopt(sys.argv[1:], 'anld:cvs:y', ['help'])
    except getopt.GetoptError:
        options = [('--help', '')]
    if ('--help', '') in options:
        show_help()
        return

    use_db = True

    for opt in options:
        if opt[0] == '-n':
            use_db = False
        elif opt[0] == '-l':
            show_db_list()
            sys.exit()
        elif opt[0] == '-d':
            del_word(opt[1])
            sys.exit()
        elif opt[0] == '-c':
            sub_opt = input('clear your database, y or n?\n')
            if sub_opt == 'y':
                del_word(None)
                sys.exit()
            else:
                sys.exit()

    keyword = ' '.join(args)

    if not keyword:
        show_help()
    else:
        query(keyword, use_db)

    db.close()

if __name__ == '__main__':
    # test = YouDaoSpider('test')
    # result = test.get_result()
    # show_result(result)
    main()


