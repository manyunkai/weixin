# -*-coding:utf-8 -*-
'''
Created on 2013-11-20

@author: Danny
DannyWork Project
'''

from django.contrib import admin
from django.core.urlresolvers import reverse

from weixin.models import MsgReply, TextMsg, NewsMsg, NewsMsgItem, EventReply
from weixin.forms import NewsMsgItemForm, TextMsgForm
from weixin.models.message import NewsMsgItemMapping


class MsgReplyAdmin(admin.ModelAdmin):
    fields = ['name', 'rcvd_msg_type', 'rcvd_msg_content',
              'msg_object_content_type', 'msg_object_object_id']
    list_display = ['name', 'rcvd_msg_type', 'rcvd_msg_content',
                    'res_msg_type', 'related_object']
    related_lookup_fields = {
        'generic': [['msg_object_content_type', 'msg_object_object_id']],
    }

    def save_model(self, request, obj, form, change):
        print form.cleaned_data.get('items')
        obj.res_msg_type = obj.msg_object_content_type.model[:-3]
        obj.save()

    def related_object(self, obj):
        info = obj.msg_object._meta.app_label, obj.msg_object._meta.module_name
        url = reverse('admin:{0}_{1}_change'.format(*info), args=[obj.msg_object.id])
        return u'<a href="{0}">{1}</a>'.format(url, obj.msg_object.name)
    related_object.short_description = u'关联消息'
    related_object.allow_tags = True


class TextMsgAdmin(admin.ModelAdmin):
    list_display = ['name', 'content']
    form = TextMsgForm


class MsgItemsInline(admin.TabularInline):
    model = NewsMsgItemMapping


class NewsMsgAdmin(admin.ModelAdmin):
    list_display = ['name', 'news']
    inlines = [MsgItemsInline]

    def news(self, obj):
        return u', '.join([item.title for item in obj.items.all()])
    news.short_description = u'关联的消息实体'


class NewsMsgItemAdmin(admin.ModelAdmin):
    fields = ['title', 'pic_large', 'pic_small', 'url', 'description']
    form = NewsMsgItemForm
    list_display = ['title', 'description']


class EventReplyAdmin(admin.ModelAdmin):
    fields = ['name', 'event_type', 'event_key',
              'msg_object_content_type', 'msg_object_object_id']
    list_display = ['name', 'event_type', 'event_key',
                    'msg_object_content_type', 'related_object']
    related_lookup_fields = {
        'generic': [['msg_object_content_type', 'msg_object_object_id']],
    }

    def save_model(self, request, obj, form, change):
        obj.res_msg_type = obj.msg_object_content_type.model[:-3]
        obj.save()

    def related_object(self, obj):
        info = obj.msg_object._meta.app_label, obj.msg_object._meta.module_name
        url = reverse('admin:{0}_{1}_change'.format(*info), args=[obj.msg_object.id])
        return u'<a href="{0}">{1}</a>'.format(url, obj.msg_object.name)
    related_object.short_description = u'关联消息'
    related_object.allow_tags = True


admin.site.register(MsgReply, MsgReplyAdmin)
admin.site.register(TextMsg, TextMsgAdmin)
admin.site.register(NewsMsg, NewsMsgAdmin)
admin.site.register(NewsMsgItem, NewsMsgItemAdmin)
admin.site.register(EventReply, EventReplyAdmin)
