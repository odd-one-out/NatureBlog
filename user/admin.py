from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth import get_user_model
from blog.admin import CommentTabInline, PostTabInline

User = get_user_model()

# Register your models here.

admin.site.unregister(User)

@admin.register(User)
class UserAdmin(BaseUserAdmin):
    inlines = [CommentTabInline, PostTabInline]
