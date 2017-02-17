# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from django import forms
from django.forms import ModelForm, widgets as w
from django.utils.translation import ugettext as _
#from pagedown.widgets import PagedownWidget
from lbe.models import Comment, UserProfile, Chat
from django.contrib.auth.models import User




class CommentForm(ModelForm):

    class Meta():
        model = Comment
        exclude = ['is_approved', 'created']
        widgets = {
            'article': w.HiddenInput, 'parent': w.HiddenInput,
            #'content': PagedownWidget,
            'user_email': w.TextInput(attrs={'placeholder':
                                             _('for gravatar service only')})
                                             
                                           
        }
class UserForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput())

    class Meta:
        model = User
        fields = ('username', 'email', 'password')

class UserProfileForm(forms.ModelForm):
    class Meta:
        model = UserProfile
        fields = ('website',)
        
class ChatForm(forms.ModelForm):

    class Meta:
        model = Chat
        fields = ('Author', 'Text',)
        
        
# Модель формы обратной связи
class ContactForm(forms.Form):
    subject = forms.CharField(max_length=100, widget=forms.TextInput(attrs={'size':'40','class': 'form-control'}))
    sender = forms.EmailField(widget=forms.TextInput(attrs={'size':'40','class': 'form-control'}))
    message = forms.CharField(widget=forms.Textarea(attrs={'class': 'form-control'}))
    copy = forms.BooleanField(required=False)
    