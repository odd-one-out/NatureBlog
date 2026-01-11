from django.contrib import admin
from blog.models import Category, Post, Comment
# Register your models here.

#admin.site.register(Category)
#admin.site.register(Post)
#admin.site.register(Comment)

class CommentTabInline(admin.TabularInline):
    model = Comment
    fields = ['text', 'date', 'user', 'post']
    readonly_fields = ['text','date', 'user', 'post']
    extra = 0

    def get_queryset(self, request):
        # Optimizes ForeignKey relationships named 'foreign_key_field_name'
        # and ManyToMany/reverse relationships named 'many_to_many_field_name'
        qs = super().get_queryset(request)
        return qs.select_related('user', 'post')

class PostTabInline(admin.TabularInline):
    model = Post
    fields = ['title', 'date']
    readonly_fields = ['title','date']
    extra = 0

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['id', 'name', 'post_count']
    list_display_links = ['name']
    inlines = [PostTabInline]

    def post_count(self, obj):
        if obj.pk:
            return str(obj.post_set.count())
        return '-'

    post_count.short_description = "posts"



@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    fields = ['title', 'slug', 'description', 'date', 'author', 'category', 'display_likes', 'status', ('image1', 'image2', 'image3'), 'video_file']
    readonly_fields = ['display_likes', 'date', 'author']
    list_display = ['id', 'title', 'status', 'category', 'author', 'date']
    list_editable = ['status']
    list_display_links = ['title', 'author']
    list_filter = ['status', 'category', 'author']
    search_fields = ['title', 'description']
    actions = ['set_published']
    inlines = [CommentTabInline]

    def display_likes(self, obj):
        """Create a comma-separated string of authors for the readonly field."""
        if obj.pk: # Only show for existing objects, to avoid ValueError on new ones # ???what does it mean???
            likes_list = [like.username for like in obj.likes.all()]
            return ", ".join(likes_list)
        return "N/A"
    
    # Optional: Customize the column header in the admin list view
    display_likes.short_description = "Likes"

    def set_published(self, request, queryset):
        # update status of all chosen posts to Published
        queryset.update(status=Post.STATUS[1][0])

@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    fields = ['text', 'date', 'user', 'post']
    readonly_fields = ['date', 'user']
    list_display = ['id', 'text', 'user', 'post', 'date']
    list_display_links = ['text', 'post', 'user']
    list_filter = ['user', 'post']
    search_fields = ['text']