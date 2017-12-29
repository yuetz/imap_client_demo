#!/usr/bin/env python
# -*- coding: utf-8 -*-
# 参考文档： http://james.apache.org/server/rfclist/imap4/rfc2060.txt
# Created by yuetiezhu on 17/12/29
from __future__ import print_function
from __future__ import division
from __future__ import absolute_import


from imapclient import IMAPClient
import email
from email.header import decode_header
from email.utils import parseaddr
from email.utils import parsedate
import logging
import sys
import re

logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s %(filename)s[line:%(lineno)d] %(levelname)s: %(message)s',
                    datefmt='%a, %d %b %Y %H:%M:%S'
                    )

hostname = 'imap.exmail.qq.com'
user = raw_input('Email: ')
password = raw_input('Password: ')


def reader():
    c = log_in()

    folders = list_folder(c)
    logging.info(u'包含文件夹如下:')
    for folder in folders:
        logging.info(folder[-1])

    msg_dict = fetch(c, u'其他文件夹/nlp-article', 'UNSEEN')

    for msg_id, message in msg_dict.items():
        subject, mail_from, mail_to, mail_time, mail_content = parse(message)
        logging.info(u'新邮件来啦')
        logging.info(u'主题: {0}'.format(subject))
        logging.info(u'发信人: {0}'.format(mail_from))
        logging.info(u'时间: {0}'.format(mail_time))
        logging.info(u'内容: {0}'.format(mail_content))
        logging.info(u'filter: {0}'.format(filter_content(mail_content)))
        logging.info('\n' * 2)

    log_out(c)


def filter_content(content):
    # if 'org.hibernate' in content:
    lesson = re.findall(r'(?<=lessonId=).+(?=&&)', content)
    return lesson[0] if lesson else None
    # m = re.match(r'^(.*)lessonId=(.+)&&(.*)$', content)
    # return m.group(2) if m else None


def log_in():
    c = IMAPClient(hostname, port=993, ssl=True)
    try:
        c.login(user, password)
        logging.info(u'登录成功')
    except c.Error:
        logging.error(u'用户名或密码错误')
        sys.exit(1)
    return c


def log_out(c):
    c.logout()


def list_folder(c):
    return c.list_folders()


def fetch(c, folder='INBOX', search_type='ALL'):
    c.select_folder(folder, readonly=True)
    # search_type = 'UNSEEN'
    result = c.search(search_type)
    return c.fetch(result, ['BODY.PEEK[]'])


def parse(message):
    e = email.message_from_string(message['BODY[]'])  # 生成Message类型
    subject = decode_str(e['Subject'])

    # from datetime import datetime
    # t = datetime.strptime(e['Date'].replace(' +0800 (CST)', ''), '%a, %d %b %Y %H:%M:%S')
    # t = datetime.strftime(t, '%Y-%m-%d %H:%M:%S')
    mail_time = parsedate(e['Date'])
    mail_time = '{0}-{1}-{2} {3}:{4}:{5}'.format(*mail_time[:6])
    mail_from = map(decode_str, parseaddr(e['From']))
    mail_to = map(decode_str, parseaddr(e['To']))
    mail_contents = parse_part(e)
    mail_content = '\n'.join(mail_contents)
    return subject, mail_from, mail_to, mail_time, mail_content


def parse_part(msg):
    contents = []
    if msg.is_multipart():
        # 如果邮件对象是一个MIMEMultipart, get_payload()返回list，包含所有的子对象:
        parts = msg.get_payload()
        for n, part in enumerate(parts):
            # 递归获取每一个子对象:
            contents += (parse_part(part))
    else:
        # 邮件对象不是一个MIMEMultipart, 就根据content_type判断:
        content_type = msg.get_content_type()
        # content_maintype = msg.get_content_maintype()
        if content_type == 'text/plain' or content_type == 'text/html':
            # 纯文本或HTML内容:
            content = msg.get_payload(decode=True).strip()
            # 要检测文本编码:
            charset = guess_charset(msg)
            if charset:
                contents.append(content.decode(charset))
            else:
                contents.append(content.decode('gbk'))
        else:
            # TODO 不是文本,作为附件处理，要获取文件名称
            content = msg.get_payload(decode=True)
            with open('', 'w') as f:
                f.write(content)

    return contents


def decode_str(s):
    value, charset = decode_header(s)[0]
    if charset:
        value = value.decode(charset)
    return value


def guess_charset(msg):
    # 先从msg对象获取编码:
    charset = msg.get_charset()
    if charset is None:
        # 如果获取不到，再从Content-Type字段获取:
        content_type = msg.get('Content-Type', '').lower()
        pos = content_type.find('charset=')
        if pos >= 0:
            charset = content_type[pos + 8:].strip()
    return charset


if __name__ == '__main__':
    reader()
