#!/usr/bin/env python3
# _*_ coding: utf-8 _*_
import sys
import json
import getopt
from termcolor import colored
import requests
from stormwords.config import *
from stormwords.model import Word, db
from stormwords.spider import YouDaoSpider

__all__ = ['show_help', 'query', 'show_result', 'del_word', 'show_db_list', 'main']


def show_help():
    print("""
    控制台下的storm-words 版本{ver}
    查询结果会保存到SQLite数据库中,
    使用方法 sw [-f] [-a] [-l, --list] [-c] [-d word] [--help] word
    [-f] 强制重新获取, 不管数据库中是否已经保存
    [-a] 使用有道智云API
    [-l] 按单词查询时间，列出数据库中保存的所有单词
        [--list t] 按单词查询时间，列出数据库中保存的所有单词
        [--list c] 按查询次数降序，列出数据库中保存的所有单词
        [--list a] 按单词字母排序，列出数据库中保存的所有单词
    [-c] 清空数据库
    [-d word] 删除数据库中某个单词
    [--help] 显示帮助信息
    """.format(ver=VERSION))


def show_result(result):
    """
    show translate result in a readable way.
    :param result: dict with the same json format as YouDao API had returned.
    """
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


def query(keyword, use_db=True, use_api=False):
    update_word = [True]   # need update words by default
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
                result.update(spider.get_result(use_api))
            except requests.Timeout as e:
                print(colored('Timeout:', 'red'), e,
                      colored('\nPlease check your network condition and try again ...', 'yellow'))
                sys.exit()
        # Update database
        new_word = word if word else Word()
        new_word.keyword = keyword
        new_word.json_data = json.dumps(result)
        new_word.save()
    show_result(result)


def show_db_list(model='t'):
    if model == 't':
        print(colored('保存在数据库中的单词及查询次数:', 'blue'))
        for word in Word.select():
            print(colored(word.keyword, 'cyan'), colored(str(word.count), 'green'))
    elif model == 'c':
        print(colored('保存在数据库中的单词及查询次数:', 'blue'))
        for word in Word.select().order_by(Word.count.desc()):
            print(colored(word.keyword, 'cyan'), colored(str(word.count), 'green'))
    elif model == 'a':
        print(colored('保存在数据库中的单词及查询次数:', 'blue'))
        for word in Word.select().order_by(Word.keyword):
            print(colored(word.keyword, 'cyan'), colored(str(word.count), 'green'))
    else:
        show_help()


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
    # create table of word
    if not db.get_tables():
        Word.create_table()
    if not db.get_tables()[0] == 'word':
        Word.create_table()

    try:
        options, args = getopt.getopt(sys.argv[1:], 'afld:c', ['help', 'list='])
    except getopt.GetoptError:
        options = [('--help', '')]
    if ('--help', '') in options:
        show_help()
        return

    use_db = True
    use_api = False

    for opt in options:
        if opt[0] == '-f':
            use_db = False
        elif opt[0] == '-a':
            use_api = True
        elif opt[0] == '-l':
            show_db_list()
            sys.exit()
        elif opt[0] == '--list':
            show_db_list(opt[1])
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
        query(keyword, use_db, use_api)

    db.close()

if __name__ == '__main__':
    main()


