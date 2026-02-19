from django.contrib import admin
from django.contrib.auth import get_user_model

User = get_user_model()


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ['id', 'login_id', 'nickname', 'gender', 'date_joined']
    list_filter = ['gender']
    search_fields = ['login_id', 'nickname']
    actions = ['delete_selected']
