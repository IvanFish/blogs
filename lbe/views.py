# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from django.contrib.sites.models import Site
from django.views.generic import DetailView, ListView
from django.views.generic.edit import CreateView
from django.db.models import Count
from django.core.exceptions import ObjectDoesNotExist, PermissionDenied
from django.core.urlresolvers import reverse
from django.shortcuts import render, get_object_or_404, redirect
from django.utils.translation import ugettext as _
from django.utils.six.moves.urllib.parse import urlparse
from django.contrib.syndication.views import Feed
from lbe.models import Setting, Category, Article, Comment, Chat
from lbe.forms import CommentForm, ContactForm, UserForm, UserProfileForm, ChatForm
from lbe.utils import make_tree
from django.contrib import auth
from django.core.mail import send_mail,  BadHeaderError
from django.http import HttpResponse, HttpResponseRedirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required



def add_user_session_data(instance, form_initial):
    request = instance.request
    if request.user.is_authenticated():
        data = {
            'user_name': request.user.username,
            'user_email': request.user.email,
            'user_url': '{}://{}'.format(request.scheme,
                                         Site.objects.get_current().domain)
        }
    else:
        data = request.session.get('user_data', {})
    form_initial.update(data)
    return form_initial


class ArticleDetail(DetailView):
    model = Article

    def get_queryset(self):
        qs = super(ArticleDetail, self).get_queryset()
        if not self.request.user.is_superuser:
            qs = qs.filter(is_published=True)
        return qs

    def get_context_data(self, **kwargs):
        ctx = super(ArticleDetail, self).get_context_data(**kwargs)
        comment_list = (
            Comment.objects.filter(article=self.object).order_by('created')
        )
        for comment in comment_list:
            comment._article_url = self.object.get_absolute_url()
            if not comment.is_approved:
                comment.url = ''
                comment.content = _('Comment is under moderation')
                comment.under_moderation_class = 'comment-under-moderation'
        ctx['comment_tree'] = make_tree(comment_list)
        ctx['comment_form'] = CommentForm(
            initial=add_user_session_data(self, {'article': self.object})
        )
        return ctx


class ArticleList(ListView):
    model = Article
    paginate_by = 10

    def get_queryset(self):
        qs = super(ArticleList, self).get_queryset()
        return qs.annotate(Count('comment')).filter(is_published=True,
                                                    is_standalone=False)


class CategoryList(ArticleList):
    def get_category(self):
        return get_object_or_404(Category, slug=self.kwargs['slug'])

    def get_queryset(self):
        qs = super(CategoryList, self).get_queryset()
        return qs.filter(category=self.get_category())

    def get_context_data(self, **kwargs):
        ctx = super(CategoryList, self).get_context_data(**kwargs)
        ctx['category'] = self.get_category()
        return ctx


class CommentAdd(CreateView):
    model = Comment
    form_class = CommentForm
    http_method_names = ['post']
    template_name = 'lbe/comment_add.html'

    def form_valid(self, form):
        if not self.request.user.is_authenticated():
            self.request.session['user_data'] = {
                field: form.cleaned_data[field]
                for field in ['user_name', 'user_email', 'user_url']
            }
        if self.request.user.is_superuser:
            form.instance.is_approved = True
        return super(CommentAdd, self).form_valid(form)


class CommentReply(CommentAdd):
    http_method_names = ['get', 'post']

    def get_initial(self):
        # GET method is allowed, so we need to have some antispam protection
        article = Article.objects.only('slug').get(id=self.kwargs['article'])
        referer = urlparse(self.request.META.get('HTTP_REFERER', ''))
        if article.slug not in referer.path:  # /slug/
            raise PermissionDenied()
        return add_user_session_data(self, {'article': self.kwargs['article'],
                                            'parent': self.kwargs['pk']})


class RSS(Feed):
    def title(self):
        try:
            return Setting.objects.get(name='site_title').value
        except ObjectDoesNotExist:
            return ''

    def description(self):
        try:
            return Setting.objects.get(name='site_description').value
        except ObjectDoesNotExist:
            return ''

    def link(self):
        return reverse('lbe:rss')

    def items(self):
        return Article.objects.published_regular()[:10]

    def item_title(self, item):
        return item.title

    def item_description(self, item):
        return item.get_content()

    def item_pubdate(self, item):
        return item.created


class CategoryRSS(RSS):
    def __call__(self, request, *args, **kwargs):
        self.category = get_object_or_404(Category, slug=kwargs['slug'])
        return super(CategoryRSS, self).__call__(request, *args, **kwargs)

    def title(self):
        try:
            title = Setting.objects.get(name='site_title').value
            return ''.join([title, ' » ', self.category.name])
        except ObjectDoesNotExist:
            return self.category.name

    def description(self):
        return self.category.description

    def link(self):
        return reverse('lbe:category_rss', args=[self.category.slug])

    def items(self):
        articles = Article.objects.published_regular()
        return articles.filter(category=self.category)[:10]


class ArticleCommentsRSS(Feed):
    def __call__(self, request, *args, **kwargs):
        self.article = get_object_or_404(
            Article, slug=kwargs['slug'], is_published=True
        )
        return super(ArticleCommentsRSS, self).__call__(request,
                                                        *args, **kwargs)

    def title(self):
        return ''.join([self.article.title, ' » ', _('comments')])

    def description(self):
        return _('Comments')

    def link(self):
        return reverse('lbe:article_comments_rss', args=[self.article.slug])

    def items(self):
        qs = Comment.objects.filter(is_approved=True, article=self.article)
        return qs[:25]

    def item_title(self, item):
        return item.user_name

    def item_description(self, item):
        return item.get_content()

    def item_pubdate(self, item):
        return item.created


def e404(request):
    return render(request, 'lbe/404.html', {}, status=404)
    
    
# Функция формы обратной связи
def contactform(reguest):
    if reguest.method == 'POST':
        form = ContactForm(reguest.POST)
        # Если форма заполнена корректно, сохраняем все введённые пользователем значения
        if form.is_valid():
            subject = form.cleaned_data['subject']
            sender = form.cleaned_data['sender']
            message = form.cleaned_data['message']
            copy = form.cleaned_data['copy']

            recepients = ['ivankaraseff@gmail.com',]
            # Если пользователь захотел получить копию себе, добавляем его в список получателей
            if copy:
                recepients.append(sender)
            try:
                send_mail(subject, message, 'ivankaraseff@gmail.com', recepients)
            except BadHeaderError: #Защита от уязвимости
                return HttpResponse('Invalid header found')
            # Переходим на другую страницу, если сообщение отправлено
            return HttpResponseRedirect('/lbe/thanks/')

    else:
        form = ContactForm()
    # Выводим форму в шаблон
    return render(reguest, 'lbe/contact.html', {'form': form, 'username': auth.get_user(reguest).username})
    
    
def thanks(reguest):
    thanks = 'thanks'
    return render(reguest, 'lbe/thanks.html', {'thanks': thanks})
    
def chat(request):
    
    if request.method == "POST":
        form = ChatForm(request.POST)
        if form.is_valid():
            chat = form.save(commit=False)
         
            chat.save()
            return redirect('./')
    else:
        form = ChatForm()
    return render(request, 'lbe/chat.html', {'form': form})
    
#def chats(reguest):
#    chats = 'chats'
#    return render(reguest, 'lbe/chats.html', {'chats': chats})

    

	
    
def register(request):

    # Логическое значение указывающее шаблону прошла ли регистрация успешно.
    # В начале ему присвоено значение False. Код изменяет значение на True, если регистрация прошла успешно.
    registered = False

    # Если это HTTP POST, мы заинтересованы в обработке данных формы.
    if request.method == 'POST':
        # Попытка извлечь необработанную информацию из формы.
        # Заметьте, что мы используем UserForm и UserProfileForm.
        user_form = UserForm(data=request.POST)
        profile_form = UserProfileForm(data=request.POST)

        # Если в две формы введены правильные данные...
        if user_form.is_valid() and profile_form.is_valid():
            # Сохранение данных формы с информацией о пользователе в базу данных.
            user = user_form.save()

            # Теперь мы хэшируем пароль с помощью метода set_password.
            # После хэширования мы можем обновить объект "пользователь".
            user.set_password(user.password)
            user.save()

            # Теперь разберемся с экземпляром UserProfile.
            # Поскольку мы должны сами назначить атрибут пользователя, необходимо приравнять commit=False.
            # Это отложит сохранение модели, чтобы избежать проблем целостности.
            profile = profile_form.save(commit=False)
            profile.user = user

            # Предоставил ли пользователь изображение для профиля?
            # Если да, необходимо извлечь его из формы и поместить в модель UserProfile.
            #if 'picture' in request.FILES:
                #profile.picture = request.FILES['picture']

            # Теперь мы сохраним экземпляр модели UserProfile.
            profile.save()

            # Обновляем нашу переменную, чтобы указать, что регистрация прошла успешно.
            registered = True

        # Неправильная формы или формы - ошибки или ещё какая-нибудь проблема?
        # Вывести проблемы в терминал.
        # Они будут также показаны пользователю.
        else:
            print (user_form.errors, profile_form.errors)

    # Не HTTP POST запрос, следователь мы выводим нашу форму, используя два экземпляра ModelForm.
    # Эти формы будут не заполненными и готовы к вводу данных от пользователя.
    else:
        user_form = UserForm()
        profile_form = UserProfileForm()

    # Выводим шаблон в зависимости от контекста.
    return render(request,
            'lbe/register.html',
            {'user_form': user_form, 'profile_form': profile_form, 'registered': registered} )
            
def user_login(request):

    # Если запрос HTTP POST, пытаемся извлечь нужную информацию.
    if request.method == 'POST':
        # Получаем имя пользователя и пароль, вводимые пользователем.
        # Эта информация извлекается из формы входа в систему.
                # Мы используем request.POST.get('<имя переменной>') вместо request.POST['<имя переменной>'],
                # потому что request.POST.get('<имя переменной>') вернет None, если значения не существует,
                # тогда как request.POST['<variable>'] создаст исключение, связанное с отсутствем значения с таким ключом
        username = request.POST.get('username')
        password = request.POST.get('password')

        # Используйте Django, чтобы проверить является ли правильным
        # сочетание имя пользователя/пароль - если да, то возвращается объект User.
        user = authenticate(username=username, password=password)

        # Если мы получили объект User, то данные верны.
        # Если получено None (так Python представляет отсутствие значения), то пользователь
        # с такими учетными данными не был найден.
        if user:
            # Аккаунт активен? Он может быть отключен.
            if user.is_active:
                # Если учетные данные верны и аккаунт активен, мы можем позволить пользователю войти в систему.
                # Мы возвращаем его обратно на главную страницу.
                login(request, user)
                return HttpResponseRedirect('/')
            else:
                # Использовался не активный аккуант - запретить вход!
                return HttpResponse("Ваш аккаунт отключен.")
        else:
            # Были введены неверные данные для входа. Из-за этого вход в систему не возможен.
            print ("Invalid login details: {0}, {1}".format(username, password))
            
            return render(request, 'lbe/error.html')


    # Запрос не HTTP POST, поэтому выводим форму для входа в систему.
    # В этом случае скорее всего использовался HTTP GET запрос.
    else:
        # Ни одна переменная контекста не передается в систему шаблонов, следовательно, используется
        # объект пустого словаря...
        return render(request, 'lbe/login.html', {})
        
# Используйте декоратор login_required(), чтобы гарантировать, что только авторизированные пользователи смогут получить доступ к этому представлению.
@login_required
def user_logout(request):
    # Поскольку мы знаем, что только вошедшие в систему пользователи имеют доступ к этому представлению, можно осуществить выход из системы
    logout(request)

    # Перенаправляем пользователя обратно на главную страницу.
    return HttpResponseRedirect('/')
        



