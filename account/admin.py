from django.contrib import admin
from .models import User, OtpVerify
# Register your models here.


class UserAdmin(admin.ModelAdmin):
    search_fields = ['id', 'email']
    list_display = ['id', 'email', 'name', 'is_superuser', 'is_owner', 'created_at', 'updated_at']


class OtpVerifyAdmin(admin.ModelAdmin):
    search_fields = ['id']
    list_display = ['id', 'user', ]


admin.site.register(User, UserAdmin)
admin.site.register(OtpVerify, OtpVerifyAdmin)
