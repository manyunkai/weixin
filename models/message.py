# -*-coding:utf-8 -*-
'''
Created on 2013-11-20

@author: Danny
DannyWork Project
'''

import uuid
import os

from django.db import models
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes import generic
from django.conf import settings


RCVD_MSG_TYPE = (
    ('text', '文本消息'),
#     ('image', '图片消息'),
#     ('voice', '语音消息'),
#     ('video', '视频消息'),
#     ('location', '地理位置消息'),
    ('all', '所有消息')
)

RES_MSG_TYPE = (
    ('text', '文本消息'),
#     ('image', '图片消息'),
#     ('voice', '语音消息'),
#     ('video', '视频消息'),
#     ('music', '音乐消息'),
    ('news', '图文消息'),
)


def str_uuid1():
    return str(uuid.uuid1())


def news_large_pic_rename(instance, filename):
    path = os.path.join(getattr(settings, 'WEIXIN_IMAGES_ROOT', 'weixin/'), 'news/large/')
    return os.path.join(path, str_uuid1() + os.path.splitext(filename)[1])


def news_small_pic_rename(instance, filename):
    path = os.path.join(getattr(settings, 'WEIXIN_IMAGES_ROOT', 'weixin/'), 'news/small/')
    return os.path.join(path, str_uuid1() + os.path.splitext(filename)[1])


class NewsMsgItem(models.Model):
    title = models.CharField(u'标题', max_length=100)
    description = models.CharField(u'描述', max_length=2000)
    pic_large = models.ImageField(upload_to=news_large_pic_rename, verbose_name=u'大图',
                                  help_text=u'为保证显示效果，请上传大小为360*200（或同比例）的图片')
    pic_small = models.ImageField(upload_to=news_small_pic_rename, verbose_name=u'小图', blank=True,
                                  help_text=u'为保证显示效果，请上传大小为200*200（或同比例）的图片')
    url = models.URLField(u'跳转链接')

    def __unicode__(self):
        return self.title

    class Meta:
        app_label = 'weixin'
        verbose_name = u'图文消息主体'
        verbose_name_plural = u'图文消息主体'


class NewsMsg(models.Model):
    name = models.CharField(u'显示名称', max_length=30,
                            help_text=u'该名称仅用于列表显示')
    items = models.ManyToManyField(NewsMsgItem, verbose_name=u'图文消息',
                                   through='NewsMsgItemMapping',
                                   help_text=u'消息主体，最多支持10个。')

    def __unicode__(self):
        return self.name

    class Meta:
        app_label = 'weixin'
        verbose_name = u'图文消息'
        verbose_name_plural = u'图文消息'


class NewsMsgItemMapping(models.Model):
    newsmsg = models.ForeignKey(NewsMsg)
    newsmsgitem = models.ForeignKey(NewsMsgItem, verbose_name=u'消息')
    position = models.IntegerField(default=1, verbose_name=u'排序')

    def __unicode__(self):
        return '{0} --> {1}'.format(self.newsmsg, self.newsmsgitem)

    class Meta:
        app_label = 'weixin'
        db_table = 'weixin_newsmsg_items'
        ordering = ['position']
        verbose_name = u'图文消息关联'
        verbose_name_plural = u'图文消息关联'


class TextMsg(models.Model):
    name = models.CharField(u'显示名称', max_length=30,
                            help_text=u'该名称仅用于列表显示')
    content = models.CharField(u'内容', max_length=2000,
                               help_text=u'消息内容')

    def __unicode__(self):
        return self.name

    class Meta:
        app_label = 'weixin'
        verbose_name = u'文字消息'
        verbose_name_plural = u'文字消息'


msg_limit = models.Q(app_label='weixin', model='textmsg') | models.Q(app_label='weixin', model='newsmsg')


class MsgReply(models.Model):
    name = models.CharField(u'显示名称', max_length=30, help_text=u'该名称仅用于列表显示')
    rcvd_msg_type = models.CharField(u'接收消息类型', choices=RCVD_MSG_TYPE, max_length=10,
                                     help_text=u'指定可匹配哪种类型的消息')
    rcvd_msg_content = models.CharField(u'识别内容', max_length=100, blank=True,
                                        help_text=u'指定匹配的消息内容（完全匹配），注：英文请全部使用小写。')
    res_msg_type = models.CharField(u'响应消息类型', max_length=10, choices=RES_MSG_TYPE)

    msg_object_content_type = models.ForeignKey(ContentType,
                                                related_name='msg_obj',
                                                limit_choices_to=msg_limit,
                                                verbose_name=u'响应消息类型',
                                                help_text=u'指定返回的消息类型')
    msg_object_object_id = models.CharField(max_length=255,
                                            verbose_name=u'关联消息',
                                            help_text=u'要返回的消息主体')
    msg_object = generic.GenericForeignKey('msg_object_content_type',
                                           'msg_object_object_id')

    is_valid = models.BooleanField(u'是否生效', default=True)

    def __unicode__(self):
        return self.name

    class Meta:
        app_label = 'weixin'
        verbose_name = u'被动消息响应'
        verbose_name_plural = u'被动消息响应'


EVENT_TYPE = (
    ('subscribe', '订阅'),
    ('unsubscribe', '取消订阅'),
    ('CLICK', '菜单点击'),
)


class EventReply(models.Model):
    name = models.CharField(u'显示名称', max_length=30, help_text=u'该名称仅用于列表显示')
    event_type = models.CharField(u'事件类型', choices=EVENT_TYPE, max_length=15)
    event_key = models.CharField(u'事件KEY值', max_length=50, blank=True)
    res_msg_type = models.CharField(u'响应消息类型', max_length=10, choices=RES_MSG_TYPE)

    msg_object_content_type = models.ForeignKey(ContentType,
                                                related_name='event_msg_obj',
                                                limit_choices_to=msg_limit,
                                                verbose_name=u'响应消息类型',
                                                help_text=u'指定返回的消息类型')
    msg_object_object_id = models.CharField(max_length=255,
                                            verbose_name=u'关联消息',
                                            help_text=u'要返回的消息主体')
    msg_object = generic.GenericForeignKey('msg_object_content_type',
                                           'msg_object_object_id')

    is_valid = models.BooleanField(u'是否生效', default=True)

    def __unicode__(self):
        return self.name

    class Meta:
        app_label = 'weixin'
        verbose_name = u'事件推送响应'
        verbose_name_plural = u'事件推送响应'
