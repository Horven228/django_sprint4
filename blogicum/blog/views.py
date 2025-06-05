from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_http_methods
from django.http import Http404
from django.views.decorators.csrf import requires_csrf_token
from django.views.generic import CreateView
from django.urls import reverse_lazy
from django.db.models import Count

from .forms import (
    CommentForm, PostForm, CustomUserChangeForm, RegistrationForm
)
from .models import Category, Comment, Post

User = get_user_model()
POSTS_PER_PAGE = 10


def annotate_posts_with_comments(queryset):
    """Аннотирует посты количеством комментариев с обязательной сортировкой"""
    return queryset.annotate(
        comment_count=Count('comments')
    ).order_by('-pub_date')


def get_page_obj(request, post_list, posts_per_page):
    """Создает объект пагинации для списка постов"""
    paginator = Paginator(post_list, posts_per_page)
    page_number = request.GET.get('page')
    return paginator.get_page(page_number)


@requires_csrf_token
def csrf_failure(request, reason=""):
    """Кастомная страница ошибки 403 CSRF"""
    return render(request, 'pages/403.html', status=403)


def index(request):
    """Главная страница с опубликованными постами"""
    post_list = Post.published.select_related(
        'category', 'author', 'location'
    )
    post_list = annotate_posts_with_comments(post_list)
    page_obj = get_page_obj(request, post_list, POSTS_PER_PAGE)
    return render(request, 'blog/index.html', {'page_obj': page_obj})


def post_detail(request, post_id):
    """Детальная страница поста"""
    post = get_object_or_404(
        Post.objects.select_related('category', 'location', 'author'),
        pk=post_id
    )

    user_is_author = post.author == request.user
    post_is_available = (
        post.is_published
        and post.pub_date <= timezone.now()
        and post.category.is_published
    )

    if not (post_is_available or user_is_author):
        raise Http404("Пост не найден")

    if user_is_author:
        comments = post.comments.all().select_related('author')
    else:
        comments = post.comments.filter(
            is_published=True
        ).select_related('author')

    comments = comments.order_by('created_at')
    form = CommentForm()

    return render(
        request,
        'blog/detail.html',
        {
            'post': post,
            'comments': comments,
            'form': form
        }
    )


def category_posts(request, category_slug):
    """Страница постов категории"""
    category = get_object_or_404(
        Category,
        slug=category_slug,
        is_published=True
    )
    post_list = Post.objects.filter(category=category).published()
    post_list = annotate_posts_with_comments(post_list)
    
    page_obj = get_page_obj(request, post_list, 10)
    return render(
        request,
        'blog/category.html',
        {'category': category, 'page_obj': page_obj}
    )


def profile(request, username):
    """Страница профиля пользователя"""
    user = get_object_or_404(User, username=username)
    posts = user.posts.all()
    
    if request.user != user:
        posts = posts.published()
    
    posts = annotate_posts_with_comments(posts)
    page_obj = get_page_obj(request, posts, 10)
    return render(
        request,
        'blog/profile.html',
        {'profile': user, 'page_obj': page_obj}
    )


@login_required
def edit_profile(request):
    """Редактирование профиля пользователя"""
    if request.method == 'POST':
        form = CustomUserChangeForm(
            request.POST,
            instance=request.user,
        )
        if form.is_valid():
            form.save()
            return redirect('blog:profile', username=request.user.username)
    else:
        form = CustomUserChangeForm(instance=request.user)
    return render(request, 'blog/edit_profile.html', {'form': form})


@login_required
def post_create(request):
    """Создание нового поста"""
    form = PostForm(request.POST or None, request.FILES or None)
    if form.is_valid():
        post = form.save(commit=False)
        post.author = request.user
        post.save()
        return redirect('blog:profile', username=request.user.username)
    return render(request, 'blog/create.html', {'form': form})


@login_required
def post_edit(request, post_id):
    """Редактирование существующего поста"""
    post = get_object_or_404(Post, pk=post_id)
    if post.author != request.user:
        return redirect('blog:post_detail', post_id=post_id)

    form = PostForm(
        request.POST or None,
        files=request.FILES or None,
        instance=post
    )

    if form.is_valid():
        form.save()
        return redirect('blog:post_detail', post_id=post_id)

    return render(
        request,
        'blog/create.html',
        {'form': form, 'post': post}
    )


@login_required
@require_http_methods(['POST'])
def add_comment(request, post_id):
    """Добавление комментария к посту"""
    post = get_object_or_404(Post, pk=post_id)
    form = CommentForm(request.POST)

    if form.is_valid():
        comment = form.save(commit=False)
        comment.post = post
        comment.author = request.user
        comment.save()
        return redirect('blog:post_detail', post_id=post_id)

    return render(
        request,
        'blog/detail.html',
        {
            'post': post,
            'comments': post.comments.filter(is_published=True),
            'form': form
        }
    )


@login_required
def edit_comment(request, post_id, comment_id):
    """Редактирование комментария"""
    comment = get_object_or_404(
        Comment,
        pk=comment_id,
        post_id=post_id,
        author=request.user
    )
    form = CommentForm(request.POST or None, instance=comment)

    if form.is_valid():
        form.save()
        return redirect('blog:post_detail', post_id=post_id)

    return render(
        request,
        'blog/comment.html',
        {'form': form, 'comment': comment}
    )


@login_required
def delete_comment(request, post_id, comment_id):
    """Удаление комментария"""
    comment = get_object_or_404(
        Comment,
        pk=comment_id,
        post_id=post_id,
        author=request.user
    )

    if request.method != 'POST':
        return render(
            request,
            'blog/comment.html',
            {'comment': comment}
        )

    comment.delete()
    return redirect('blog:post_detail', post_id=post_id)


@login_required
def profile_redirect(request):
    """Перенаправление на профиль текущего пользователя"""
    return redirect('blog:profile', username=request.user.username)


@login_required
def delete_post(request, post_id):
    """Удаление поста"""
    post = get_object_or_404(Post, pk=post_id)
    
    # Проверка прав доступа
    if post.author != request.user:
        return redirect('blog:post_detail', post_id=post_id)
    
    # Подтверждение удаления (GET запрос)
    if request.method != 'POST':
        # Используем шаблон create.html в режиме удаления
        form = PostForm(instance=post)
        return render(
            request,
            'blog/create.html',
            {
                'form': form,
                'post': post  # Передаем пост для шаблона
            }
        )
    
    # Удаление поста (POST запрос)
    post.delete()
    return redirect('blog:profile', username=request.user.username)


class SignUpView(CreateView):
    """Регистрация нового пользователя"""
    form_class = RegistrationForm
    template_name = 'registration/registration_form.html'
    success_url = reverse_lazy('login')

