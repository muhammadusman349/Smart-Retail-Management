from django.contrib import admin
from .models import APILog

# Register your models here.


class APILogAdmin(admin.ModelAdmin):
    list_display = (
        'id', 'api', 'view_name', 'namespace', 'method', 'status_code', 
        'execution_time', 'client_ip_address', 'user', 'added_on'
    )
    list_filter = (
        'method', 'status_code', 'user', 'added_on'
    )
    search_fields = (
        'api', 'view_name', 'namespace', 'client_ip_address', 'user__username'
    )
    readonly_fields = ('added_on',)
    ordering = ('-added_on',)

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        return queryset

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)


admin.site.register(APILog, APILogAdmin)
