from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.urls import reverse
from django.db.models import Count

User = get_user_model()



class Category(models.Model):
    title = models.CharField(
        'Заголовок',
        max_length=256,
        help_text='Максимум 256 символов'
    )
    description = models.TextField('Описание')
    slug = models.SlugField(
        'Идентификатор',
        unique=True,
        help_text=(
            'Идентификатор страницы для URL; разрешены символы латиницы, '
            'цифры, дефис и подчёркивание.'
        )
    )
    is_published = models.BooleanField(
        'Опубликовано',
        default=True,
        help_text='Снимите галочку, чтобы скрыть публикацию.'
    )
    created_at = models.DateTimeField('Добавлено', auto_now_add=True)

    class Meta:
        verbose_name = 'категория'
        verbose_name_plural = 'Категории'
        constraints = [
            models.UniqueConstraint(
                fields=['slug'],
                name='unique_slug_category'
            )
        ]

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse(
            'blog:category_posts',
            kwargs={'category_slug': self.slug}
        )


class Location(models.Model):
    name = models.CharField(
        'Название места',
        max_length=256,
        help_text='Максимум 256 символов'
    )
    is_published = models.BooleanField(
        'Опубликовано',
        default=True,
        help_text='Снимите галочку, чтобы скрыть публикацию.'
    )
    created_at = models.DateTimeField('Добавлено', auto_now_add=True)

    class Meta:
        verbose_name = 'местоположение'
        verbose_name_plural = 'Местоположения'

    def __str__(self):
        return self.name


class PostQuerySet(models.QuerySet):
    def with_comment_count(self):
        return self.annotate(comment_count=Count('comments'))
    
    def published(self):
        return self.filter(
            is_published=True,
            pub_date__lte=timezone.now(),
            category__is_published=True
        )

class PublishedManager(models.Manager.from_queryset(PostQuerySet)):
    def get_queryset(self):
        return super().get_queryset().published()


class Post(models.Model):
    title = models.CharField(
        'Заголовок',
        max_length=256,
        help_text='Максимум 256 символов'
    )
    text = models.TextField('Текст')
    pub_date = models.DateTimeField(
        'Дата и время публикации',
        help_text=(
            'Если установить дату и время в будущем — можно делать '
            'отложенные публикации.'
        )
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name='Автор публикации',
        related_name='posts'
    )
    location = models.ForeignKey(
        Location,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name='Местоположение',
        related_name='posts'
    )
    category = models.ForeignKey(
        Category,
        on_delete=models.SET_NULL,
        null=True,
        verbose_name='Категория',
        related_name='posts'
    )
    image = models.ImageField(
        'Изображение',
        upload_to='posts_images/',
        blank=True
    )
    is_published = models.BooleanField(
        'Опубликовано',
        default=True,
        help_text='Снимите галочку, чтобы скрыть публикацию.'
    )
    created_at = models.DateTimeField('Добавлено', auto_now_add=True)

    objects = PostQuerySet.as_manager()
    published = PublishedManager()

    class Meta:
        verbose_name = 'публикация'
        verbose_name_plural = 'Публикации'
        ordering = ('-pub_date',)
        default_related_name = 'posts'
        constraints = [
            models.UniqueConstraint(
                fields=['title', 'author'],
                name='unique_title_author'
            )
        ]

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse('blog:post_detail', kwargs={'post_id': self.id})


class Comment(models.Model):
    post = models.ForeignKey(
        Post,
        on_delete=models.CASCADE,
        related_name='comments',
    )
    author = models.ForeignKey(User, on_delete=models.CASCADE)
    text = models.TextField('Текст комментария')
    created_at = models.DateTimeField(auto_now_add=True)
    is_published = models.BooleanField(
        'Опубликовано',
        default=True,
        help_text='Снимите галочку, чтобы скрыть комментарий.'
    )

    class Meta:
        verbose_name = 'комментарий'
        verbose_name_plural = 'Комментарии'
        ordering = ('created_at',)
        default_related_name = 'comments'

    def __str__(self):
        return f'Комментарий {self.author} к {self.post}'
