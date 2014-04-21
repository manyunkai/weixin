# -*-coding:utf-8 -*-
"""
Created on 2013-11-18

@author: Danny
DannyWork Project
"""

import hashlib
import time
from bs4 import BeautifulSoup

from django.views.generic.base import View
from django.http.response import HttpResponse
from django.core.exceptions import PermissionDenied
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.template.loader import render_to_string

from .models import EventReplyRule, Keyword, Config


class Weixin(View):
    @property
    def token(self):
        return Config.get_token()

    @method_decorator(csrf_exempt)
    def dispatch(self, request, *args, **kwargs):
        return super(Weixin, self).dispatch(request, *args, **kwargs)

    def validate(self, request):
        signature = request.REQUEST.get('signature', '')
        timestamp = request.REQUEST.get('timestamp', '')
        nonce = request.REQUEST.get('nonce',  '')

        tmp_str = hashlib.sha1(''.join(sorted([self.token, timestamp, nonce]))).hexdigest()
        if tmp_str == signature:
            return True

        return False

    def _get_reply(self, txt):
        txt, obj = txt.lower(), None
        for k in Keyword.get_exact_keywords():
            k = unicode(k, encoding='utf8')
            if k == txt:
                obj = Keyword.objects.filter(name=k)
                obj = obj[0] if obj else None
        if not obj:
            for k in Keyword.get_iexact_keywords():
                k = unicode(k, encoding='utf8')
                if k in txt:
                    obj = Keyword.objects.filter(name=k)
                    obj = obj[0] if obj else None
        return obj.rule if obj and obj.rule.is_valid else None

    def handle_msg(self, soup):
        if soup.MsgType.text == 'text':
            txt = soup.Content.text or ''
            reply = self._get_reply(txt.lower())

        if reply:
            context = {
                'to_user': soup.FromUserName.text,
                'from_user': soup.ToUserName.text,
                'create_time': int(time.time()),
                'reply': reply,
            }
            print context
            rendered = render_to_string('xml/message.xml', context)
            return HttpResponse(rendered)

        return HttpResponse('')

    def handle_event(self, soup):
        all = EventReplyRule.objects.filter(is_valid=True)
        reply = all.filter(event_type=soup.Event.text,
                           event_key=soup.EventKey and soup.EventKey.text and not soup.Event.text == 'subscribe' or '')

        if reply.exists():
            reply = reply[0]
            context = {
                'to_user': soup.FromUserName.text,
                'from_user': soup.ToUserName.text,
                'create_time': int(time.time()),
                'reply': reply,
            }
            rendered = render_to_string('xml/message.xml', context)
            return HttpResponse(rendered)

        return HttpResponse('')

    def get(self, request):
        if self.validate(request):
            return HttpResponse(request.REQUEST.get('echostr', ''))

        raise PermissionDenied

    def post(self, request):
#         if not self.validate(request):
#             raise PermissionDenied

        soup = BeautifulSoup(request.body, features='xml')
        if soup.MsgType:
            if soup.MsgType.text in ['text', 'image', 'voice', 'video', 'location', 'link']:
                return self.handle_msg(soup)
            elif soup.MsgType.text == 'event':
                return self.handle_event(soup)

        return HttpResponse('')
