#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os
import errno
import pickle

# Basic
VERSION = '0.0.3'
HOME = os.path.expanduser("~")
BASE_DIR = os.path.join(HOME, '.storm_words')   # 用户数据根目录

DATABASE = 'storm_words.db'
PK_FILE = 'storm_words.pk'
DB_DIR = os.path.join(BASE_DIR, DATABASE)
PK_DIR = os.path.join(BASE_DIR, PK_FILE)

config = {'version': '0'}

# YouDao AICloud config
APP_KEY = '566392cad5fa8829'  # this is my app key
SECRET_KEY = 'RF2jySGxOKDYO2WT1H78vu7JeKq6KvL9'  # this is my secret key


def silent_remove(filename):
    try:
        os.remove(filename)
    except OSError as e:
        if e.errno != errno.ENOENT:
            raise


def save_config():
    with open(PK_DIR, 'wb') as f:
        pickle.dump(config, f)


def prepare():
    if not os.path.exists(BASE_DIR):
        os.mkdir(BASE_DIR)

    if os.path.isfile(PK_DIR):
        with open(PK_DIR, 'rb') as f:
            global config
            config = pickle.load(f)

    if config.get('version', '0') < VERSION:
        config['version'] = VERSION
        save_config()




