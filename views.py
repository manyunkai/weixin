# -*-coding:utf-8 -*-
'''
Created on 2013-11-18

@author: Danny
DannyWork Project
'''

import hashlib
import time
from bs4 import BeautifulSoup

from django.views.generic.base import View
from django.http.response import HttpResponse
from django.core.exceptions import PermissionDenied
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.template.loader import render_to_string

from models import MsgReply, EventReply
from models import Config


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

    def handle_msg(self, soup):
        all = MsgReply.objects.filter(is_valid=True)
        if soup.msgtype.text == 'text':
            reply = all.filter(rcvd_msg_type=soup.msgtype.text, rcvd_msg_content=soup.content.text.strip().lower()) or all.filter(rcvd_msg_type='all')
        else:
            reply = all.filter(rcvd_msg_type='all')

        if reply.exists():
            reply = reply[0]
            context = {
                'to_user': soup.fromusername.text,
                'from_user': soup.tousername.text,
                'create_time': int(time.time()),
                'reply': reply,
            }
            rendered = render_to_string('xml/message.xml', context)
            return HttpResponse(rendered)

        return HttpResponse('')

    def handle_event(self, soup):
        all = EventReply.objects.filter(is_valid=True)
        reply = all.filter(event_type=soup.event.text,
                           event_key=soup.eventkey and soup.eventkey.text or '')

        if reply.exists():
            reply = reply[0]
            context = {
                'to_user': soup.fromusername.text,
                'from_user': soup.tousername.text,
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
        if not self.validate(request):
            raise PermissionDenied

        soup = BeautifulSoup(request.body)
        if soup.msgtype:
            if soup.msgtype.text in ['text', 'image', 'voice', 'video', 'location', 'link']:
                return self.handle_msg(soup)
            elif soup.msgtype.text == 'event':
                return self.handle_event(soup)

        return HttpResponse('')
