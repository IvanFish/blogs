# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from django.conf.urls import url
from lbe.views import ArticleList, ArticleDetail, CategoryList, CommentAdd, \
    CommentReply, RSS, CategoryRSS, ArticleCommentsRSS
from lbe import views



urlpatterns = [
    url(r'^$', ArticleList.as_view(), name='article_list'),
    url(r'^feed/$', RSS(), name='rss'),
    url(r'^category/(?P<slug>[-_\w]+)/$', CategoryList.as_view(), name='category'),
    url(r'^category/(?P<slug>[-_\w]+)/feed/$', CategoryRSS(), name='category_rss'),
    url(r'^comment/add/$', CommentAdd.as_view(), name='comment_add'),
    url(r'^comment/reply/(?P<article>\d+)/(?P<pk>\d+)$', CommentReply.as_view(), name='comment_reply'),
    url(r'^(?P<slug>[-_\w]+)/$', ArticleDetail.as_view(), name='article'),
    url(r'^(?P<slug>[-_\w]+)/comments/feed/$', ArticleCommentsRSS(), name='article_comments_rss'),
    url(r'^lbe/contact/$', views.contactform, name='contact'),
    url(r'^lbe/thanks/$', views.thanks, name='thanks'),
    url(r'^lbe/register/$', views.register, name='register'),
    url(r'^lbe/login/$', views.user_login, name='login'),
    url(r'^lbe/logout/$', views.user_logout, name='logout'),
    url(r'^lbe/chat/$', views.chat, name='chat'),
    #url(r'^lbe/chats/$', views.chats, name='chats'),
    
    ] 


