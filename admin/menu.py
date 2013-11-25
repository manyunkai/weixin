# -*-coding:utf-8 -*-
'''
Created on 2013-11-20

@author: Danny
DannyWork Project
'''

from django.contrib import admin, messages
from django.http.response import HttpResponseRedirect
from django.core.urlresolvers import reverse

from weixin.models import Button
from weixin.mixins import PullMenu, PushMenu


class ButtonAdmin(admin.ModelAdmin):
    list_display = ['name', 'type', 'parent', 'key', 'url', 'position']
    change_list_template = 'menu/admin/change_list.html'

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

    def pull_menu(self, request, from_url=''):
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
                        sub_button.name = sub['name']
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

        return HttpResponseRedirect(reverse('admin:weixin_button_changelist'))

    def push_menu(self, request, from_url=''):
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
                sub_buttons = []
                for sub in top.button_set.all().order_by('position'):
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

        handle = PushMenu({'button': buttons})
        result = handle.push()
        if result:
            messages.error(request, u'操作失败：{0}。'.format(result))
        else:
            messages.success(request, u'自定义菜单已成功推至微信服务器。')

        return HttpResponseRedirect(reverse('admin:weixin_button_changelist'))


admin.site.register(Button, ButtonAdmin)
