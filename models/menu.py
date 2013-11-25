# -*-coding:utf-8 -*-
'''
Created on 2013-11-20

@author: Danny
DannyWork Project
'''

from django.db import models


BUTTON_TYPE = (
    ('click', 'click'),
    ('view', 'view'),
    ('', 'parent')
)


class Button(models.Model):
    name = models.CharField(u'标题', max_length=40)
    type = models.CharField(u'响应动作类型', max_length=10, choices=BUTTON_TYPE, blank=True)
    parent = models.ForeignKey('self', verbose_name='父级菜单', null=True, blank=True)
    key = models.CharField(u'KEY值', max_length=128, blank=True)
    url = models.URLField(u'网页链接', blank=True)
    position = models.IntegerField(u'排序', default=0)

    def __unicode__(self):
        return self.name

    class Meta:
        app_label = 'weixin'
        verbose_name = u'自定义菜单'
        verbose_name_plural = u'自定义菜单'
