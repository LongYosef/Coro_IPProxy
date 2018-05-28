# coding:utf-8
import logging
import sys

proxy_log_path='D:\\Anaconda3\\Lib\\DIYIPProxy\\proxylog.log'
logformat='%(asctime)s-%(filename)s[line:%(lineno)d]-%(levelname)s:%(message)s'

Formatter=logging.Formatter(logformat)

proxylog=logging.getLogger()
proxylog.setLevel(logging.DEBUG)

filehandler=logging.FileHandler(proxy_log_path)
filehandler.setFormatter(Formatter)
filehandler.setLevel(logging.INFO)

consolehandler=logging.StreamHandler(sys.stdout)
consolehandler.setFormatter(Formatter)
consolehandler.setLevel(logging.DEBUG)

proxylog.addHandler(filehandler)
proxylog.addHandler(consolehandler)

proxylog.debug('hello world,debug')
proxylog.info('hello world,info')
proxylog.warning('hello world,warning')

def handler_remove():
    proxylog.removeHandler(filehandler)
    proxylog.removeHandler(consolehandler)