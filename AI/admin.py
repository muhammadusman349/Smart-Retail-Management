from django.contrib import admin
from .models import IoTDevice, SensorData
# Register your models here.


class IOTDeviceAdmin(admin.ModelAdmin):
    search_fields = ['id', 'device_type', 'status', 'device_id']
    list_display = ['id', 'device_id', 'device_type',
                    'status', 'last_seen', 'created_at', 'updated_at']


class SensorDataAdmin(admin.ModelAdmin):
    list_display = ['id', 'device']


admin.site.register(IoTDevice, IOTDeviceAdmin)
admin.site.register(SensorData, SensorDataAdmin)
