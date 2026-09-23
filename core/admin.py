from django.contrib import admin

from .models import User


# Register your models here.
@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = (
        "username",
        "email",
        "first_name",
        "last_name",
        "paese",
        "phone_number",
        "profile_picture",
        "steam_url",
    )
    search_fields = ("username", "email", "first_name", "last_name", "paese")
