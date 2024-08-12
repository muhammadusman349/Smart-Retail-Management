from django.contrib import admin
from .models import User, OtpVerify
# Register your models here.

admin.site.register(User)
admin.site.register(OtpVerify)
