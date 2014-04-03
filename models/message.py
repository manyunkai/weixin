# -*-coding:utf-8 -*-
'''
Created on 2013-11-20

@author: Danny
DannyWork Project
'''

import uuid
import os
import redis

from django.db import models
from django.contrib.contenttypes.models import ContentType
from django.db.models.signals import pre_delete, post_save, pre_save
from django.contrib.contenttypes import generic

connection = redis.Redis()


RCVD_MSG_TYPE = (
    ('text', u'文本消息'),
#     ('image', u'图片消息'),
#     ('voice', u'语音消息'),
#     ('video', u'视频消息'),
#     ('location', u'地理位置消息'),
    ('all', u'所有消息')
)

RES_MSG_TYPE = (
    ('text', u'文本消息'),
#     ('image', u'图片消息'),
    ('voice', u'语音消息'),
#     ('video', u'视频消息'),
#     ('music', u'音乐消息'),
    ('news', u'图文消息'),
)


def str_uuid1():
    return str(uuid.uuid1())


def news_large_pic_rename(instance, filename):
    return os.path.join('images/news/large/', str_uuid1() + os.path.splitext(filename)[1])


def news_small_pic_rename(instance, filename):
    return os.path.join('images/news/small/', str_uuid1() + os.path.splitext(filename)[1])


def media_file_rename(instance, filename):
    return '/'.join(['files', 'media', str_uuid1() + os.path.splitext(filename)[1]])


class BaseModel(models.Model):
    name = models.CharField(u'显示名称', max_length=100,
                            help_text=u'该名称仅用于列表显示')
    created = models.DateTimeField(u'创建时间', auto_now_add=True)

    def __unicode__(self):
        return self.name

    class Meta:
        abstract = True


class NewsMsgItem(BaseModel):
    """
           图文消息内容，一个图文消息可以关系10条消息内容
    """

    title = models.CharField(u'标题', max_length=100)
    description = models.CharField(u'描述', max_length=2000)
    pic_large = models.ImageField(upload_to=news_large_pic_rename, verbose_name=u'大图', blank=True,
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


class MediaItem(BaseModel):
    """
           媒体文件
    """

    title = models.CharField(u'标题', max_length=100)
    description = models.CharField(u'描述', max_length=2000)
    file = models.FileField(upload_to=media_file_rename, verbose_name=u'文件',
                            help_text=u'上传的文件不大于5M')

    def __unicode__(self):
        return self.name

    class Meta:
        app_label = 'weixin'
        verbose_name = u'媒体文件'
        verbose_name_plural = u'媒体文件'


class MediaMsg(BaseModel):
    """
           媒体消息，目前针对音乐/语音消息
    """

    item = models.ForeignKey(MediaItem, verbose_name=u'文件')

    def __unicode__(self):
        return self.name

    class Meta:
        app_label = 'weixin'
        verbose_name = u'媒体消息'
        verbose_name_plural = u'媒体消息'


class NewsMsg(BaseModel):
    """
           图文消息
    """

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
    """
           图文消息与内容关联表
    """

    newsmsg = models.ForeignKey(NewsMsg)
    newsmsgitem = models.ForeignKey(NewsMsgItem, verbose_name=u'消息')
    position = models.IntegerField(default=1, verbose_name=u'排序')

    def __unicode__(self):
        return u'{0} --> {1}'.format(self.newsmsg, self.newsmsgitem)

    class Meta:
        app_label = 'weixin'
        db_table = 'msg_newsmsg_items'
        ordering = ['position']
        verbose_name = u'图文消息关联'
        verbose_name_plural = u'图文消息关联'


class TextMsg(BaseModel):
    """
           文字消息
    """

    content = models.CharField(u'内容', max_length=2000,
                               help_text=u'消息内容')

    def __unicode__(self):
        return self.name

    class Meta:
        app_label = 'weixin'
        verbose_name = u'文字消息'
        verbose_name_plural = u'文字消息'


msg_limit = models.Q(app_label='weixin', model='textmsg') |\
            models.Q(app_label='weixin', model='newsmsg') |\
            models.Q(app_label='weixin', model='mediamsg')


class MsgReplyRule(BaseModel):
    """
           消息响应规则
    """

    # 冗余响应消息类型方便查询
    res_msg_type = models.CharField(u'响应消息类型', max_length=10, choices=RES_MSG_TYPE)

    # 消息主体
    msg_object_content_type = models.ForeignKey(ContentType, related_name='msg_obj', limit_choices_to=msg_limit, verbose_name=u'响应消息类型',
                                                help_text=u'指定返回的消息类型')
    msg_object_object_id = models.CharField(max_length=255, verbose_name=u'关联消息',
                                            help_text=u'要返回的消息主体')
    msg_object = generic.GenericForeignKey('msg_object_content_type', 'msg_object_object_id')

    is_valid = models.BooleanField(u'是否生效', default=True)

    def __unicode__(self):
        return self.name

    class Meta:
        app_label = 'weixin'
        verbose_name = u'消息响应规则'
        verbose_name_plural = u'消息响应规则'


class Keyword(BaseModel):
    """
           关键字，每个关键字都会对应一个消息响应规则
    """

    rule = models.ForeignKey(MsgReplyRule, verbose_name=u'关联规则')
    exact_match = models.BooleanField(u'完全匹配')

    def __unicode__(self):
        return self.name

    @classmethod
    def get_exact_keywords(cls):
        cache_key = 'keywords:exact'
        if not connection.exists(cache_key):
            keywords = cls._default_manager.values_list('name', flat=True).filter(exact_match=True)
            keywords = [name.lower() for name in keywords]
            if keywords:
                connection.sadd(cache_key, *keywords)
            # TODO ... 设置过期
        return connection.smembers(cache_key)

    @classmethod
    def get_iexact_keywords(cls):
        cache_key = 'keywords:iexact'
        if not connection.exists(cache_key):
            keywords = cls._default_manager.values_list('name', flat=True).filter(exact_match=False)
            keywords = [name.lower() for name in keywords]
            if keywords:
                connection.sadd(cache_key, *keywords)
            # TODO ... 设置过期
        return connection.smembers(cache_key)

    class Meta:
        app_label = 'weixin'
        verbose_name = u'关键字'
        verbose_name_plural = u'关键字'


def _get_cache_key(instance):
    return 'keywords:exact' if instance.exact_match else 'keywords:iexact'


def keyword_pre_save(sender, **kwargs):
    instance = kwargs.get('instance')
    try:
        prev = Keyword.objects.get(id=instance.id)
    except Keyword.DoesNotExist:
        pass
    else:
        connection.srem(_get_cache_key(prev), prev.name)


def keyword_post_save(sender, **kwargs):
    instance = kwargs.get('instance')
    connection.sadd(_get_cache_key(instance), instance.name)


def keyword_pre_delete(sender, **kwargs):
    instance = kwargs.get('instance')
    if not Keyword.objects.filter(name=instance.name, exact_match=instance.exact_match).exclude(id=instance.id).exists():
        connection.srem(_get_cache_key(instance), instance.name)

pre_save.connect(keyword_pre_save, sender=Keyword)
post_save.connect(keyword_post_save, sender=Keyword)
pre_delete.connect(keyword_pre_delete, sender=Keyword)


EVENT_TYPE = (
    ('subscribe', u'订阅'),
    ('unsubscribe', u'取消订阅'),
    ('CLICK', u'菜单点击'),
)


class EventReplyRule(BaseModel):
    """
           事件响应规则
    """

    event_type = models.CharField(u'事件类型', choices=EVENT_TYPE, max_length=15)
    event_key = models.CharField(u'事件KEY值', max_length=50, blank=True)

    # 冗余响应消息类型方便查询
    res_msg_type = models.CharField(u'响应消息类型', max_length=10, choices=RES_MSG_TYPE)

    # 消息主体
    msg_object_content_type = models.ForeignKey(ContentType, related_name='event_msg_obj', limit_choices_to=msg_limit, verbose_name=u'响应消息类型',
                                                help_text=u'指定返回的消息类型')
    msg_object_object_id = models.CharField(max_length=255, verbose_name=u'关联消息',
                                            help_text=u'要返回的消息主体')
    msg_object = generic.GenericForeignKey('msg_object_content_type', 'msg_object_object_id')

    is_valid = models.BooleanField(u'是否生效', default=True)

    def __unicode__(self):
        return self.name

    class Meta:
        app_label = 'weixin'
        verbose_name = u'事件响应规则'
        verbose_name_plural = u'事件响应规则'
