# -*-coding:utf-8 -*-
"""
Created on 2013-11-20

@author: Danny
DannyWork Project
"""

from django.contrib import admin, messages
from django.http.response import HttpResponseRedirect
from django.core.urlresolvers import reverse

from ..models import Button, Config
from ..mixins import PullMenu, PushMenu


class ButtonAdmin(admin.ModelAdmin):
    change_list_template = 'menu/admin/change_list.html'
    list_display = ['name', 'type', 'parent', 'key', 'url', 'position']

    def get_urls(self):
        from django.conf.urls import patterns, url

        info = self.model._meta.app_label, self.model._meta.module_name
        return patterns('',
                        url(r'^pull_menu/$',
                            self.admin_site.admin_view(self.pull_menu),
                            name='%s_%s_pull_menu' % info),
                        url(r'^push_menu/$',
                            self.admin_site.admin_view(self.push_menu),
                            name='%s_%s_push_menu' % info),
        ) + super(ButtonAdmin, self).get_urls()

    def get_form(self, request, obj=None, **kwargs):
        form = super(ButtonAdmin, self).get_form(request, obj, **kwargs)
        form.base_fields['parent'].queryset = form.base_fields['parent'].queryset.filter(parent=None)
        return form

    def get_config(self):
        config = Config.objects.all()
        return config[0] if config else None

    def pull_menu(self, request, from_url=''):
        if Config.objects.exists():
            handle = PullMenu()
            status, data = handle.pull()
            if status:
                if data.get('button'):
                    Button.objects.all().delete()

                top_i = 1
                for top in data.get('button', []):
                    button = Button.objects.create(name=top['name'], position=top_i)
                    if top.get('sub_button'):
                        sub_i = 1
                        for sub in top.get('sub_button'):
                            sub_button = Button()
                            sub_button.name = sub.get('name')
                            if not sub_button.name:
                                messages.info(request, u'您的菜单因部分格式不正确，未能成功获取。')
                                continue
                            sub_button.type = sub['type']
                            if sub_button.type == 'click':
                                sub_button.key = sub.get('key', '')
                            else:
                                sub_button.url = sub.get('url', '')
                            sub_button.parent = button
                            sub_button.position = sub_i
                            sub_button.save()
                            sub_i += 1
                    else:
                        button.type = top['type']
                        if button.type == 'view':
                            button.key = top.get('key', '')
                        else:
                            button.url = top.get('url', '')
                        button.save()
                    top_i += 1

                messages.success(request, u'自定义菜单拉取成功。')
            else:
                messages.error(request, u'操作失败：{0}。'.format(data))
        else:
            messages.error(request, u'您还没有填写微信配置，不能进行此操作')

        return HttpResponseRedirect(reverse('admin:weixin_button_changelist'))

    def push_menu(self, request, from_url=''):
        if Config.objects.exists():
            buttons = []
            for top in Button.objects.filter(parent=None).order_by('position'):
                top_dict = {
                    'name': top.name
                }
                if top.type:
                    top_dict['type'] = top.type
                    if top.type == 'click':
                        top_dict['key'] = top.key
                    else:
                        top_dict['url'] = top.url
                else:
                    subs = top.button_set.all().order_by('position')
                    if not subs:
                        messages.info(request, u'您的菜单<{0}>动作类型设定为父级菜单，但并不包含任何子菜单，本次上传将会忽略')

                    sub_buttons = []
                    for sub in subs:
                        sub_dict = {
                            'name': sub.name,
                            'type': sub.type,
                        }
                        if sub.type == 'click':
                            sub_dict['key'] = sub.key
                        else:
                            sub_dict['url'] = sub.url
                        sub_buttons.append(sub_dict)
                    top_dict['sub_button'] = sub_buttons
                buttons.append(top_dict)

            handler = PushMenu({'button': buttons})
            result = handler.push()
            if result:
                messages.error(request, u'操作失败：{0}。'.format(result))
            else:
                messages.success(request, u'自定义菜单已成功推至微信服务器。')
        else:
            messages.error(request, u'您还没有填写微信配置，不能进行此操作')

        return HttpResponseRedirect(reverse('admin:weixin_button_changelist'))


admin.site.register(Button, ButtonAdmin)
