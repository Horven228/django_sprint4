from django.contrib import admin
from .models import Category, Post, Location, Comment

admin.site.register(Category)
admin.site.register(Location)
admin.site.register(Post)
admin.site.register(Comment)


class CategoryAdmin(admin.ModelAdmin):
    list_display = ('title', 'is_published')
    list_editable = ('is_published',)


class LocationAdmin(admin.ModelAdmin):
    list_display = ('name', 'is_published')
    list_editable = ('is_published',)


class CommentAdmin(admin.ModelAdmin):
    list_display = ('author', 'post', 'text', 'created_at')
    list_filter = ('created_at',)


class PostAdmin(admin.ModelAdmin):
    list_display = (
        'title',
        'pub_date',
        'author',
        'is_published',
        'location',
        'category',
        'created_at'
    )
    list_editable = ('is_published',)
    search_fields = ('title', 'text')
    list_filter = ('category', 'location')
    list_display_links = ('title',)
    empty_value_display = 'Не задано'
    readonly_fields = ('created_at',)
