from django.db import models
from django.utils import timezone
from django.dispatch import receiver
from django.db.models.signals import pre_save
from .utils import DEVICE_TYPES, STATUS_CHOICES
# Create your models here.


class IoTDevice(models.Model):
    device_id = models.CharField(max_length=100, unique=True)
    device_type = models.CharField(max_length=50, choices=DEVICE_TYPES)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='inactive')
    location = models.CharField(max_length=255, blank=True, null=True)
    ip_address = models.GenericIPAddressField(blank=True, null=True)
    mac_address = models.CharField(max_length=17, blank=True, null=True)
    firmware_version = models.CharField(max_length=50, blank=True, null=True)
    last_seen = models.DateTimeField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def update_status(self, new_status):
        """ Update the status of the device and last seen time."""
        self.status = new_status
        self.last_seen = timezone.now()
        self.save()

    def __str__(self):
        return f"{self.device_id}({self.device_type})"


class SensorData(models.Model):
    device = models.ForeignKey(IoTDevice, on_delete=models.CASCADE, related_name='sensor_data')
    data = models.JSONField(blank=True, null=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Data from {self.device.device_id} at {self.timestamp}"


@receiver(pre_save, sender=SensorData)
def auto_fill_sensor_data(sender, instance, **kwargs):
    if not instance.data:
        if instance.device.device_type == 'sensor':
            instance.data = {
                "sensor_reading": 100
            }
        elif instance.device.device_type == 'actuator':
            instance.data = {
                "actuator_state": "off"
            }
        elif instance.device.device_type == 'gateway':
            instance.data = {
                "connected_devices": 5
            }
        elif instance.device.device_type == 'camera':
            instance.data = {
                "image_capture": "base64_image_data"
            }
        elif instance.device.device_type == 'thermostat':
            instance.data = {
                "current_temperature": 22.5,
                "target_temperature": 24.0
            }
        else:
            instance.data = {"default": "no specific data"}
