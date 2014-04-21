# -*-coding:utf-8 -*-
"""
Created on 2013-11-20

@author: Danny
DannyWork Project
"""

from django.db import models


class Config(models.Model):
    token = models.CharField(u'Token', max_length=32,
                             help_text=u'填写微信公众号接口配置里的Token，最长32个字符。')
    app_id = models.CharField(u'AppId', max_length=32,
                              help_text=u'开发者账号唯一凭证')
    secret = models.CharField(u'AppSecret', max_length=32,
                              help_text=u'开发者账号唯一凭证密钥')

    class Meta:
        app_label = 'weixin'
        verbose_name = u'全局配置'
        verbose_name_plural = u'全局配置'

    @classmethod
    def get_token(cls):
        c = cls._default_manager.all()
        return c[0].token if c.exists() else ''

    @classmethod
    def get_appid(cls):
        c = cls._default_manager.all()
        return c[0].app_id if c.exists() else ''

    @classmethod
    def get_secret(cls):
        c = cls._default_manager.all()
        return c[0].secret if c.exists() else ''
