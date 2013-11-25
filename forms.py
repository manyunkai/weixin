# -*-coding:utf-8 -*-
'''
Created on 2013-11-21

@author: Danny
DannyWork Project
'''

from django import forms

from models import NewsMsgItem, TextMsg


class NewsMsgItemForm(forms.ModelForm):

    class Meta:
        model = NewsMsgItem
        widgets = {
            'description': forms.Textarea
        }


class TextMsgForm(forms.ModelForm):

    class Meta:
        model = TextMsg
        widgets = {
            'content': forms.Textarea
        }
