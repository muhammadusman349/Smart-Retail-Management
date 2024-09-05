import logging
from django.db import models
from django.utils import timezone
from .utils import DEVICE_TYPES, STATUS_CHOICES
from .ai_service import predict_device_status, predict_sensor_anomaly
from account.models import User
from django.dispatch import receiver
from django.db.models.signals import pre_save, post_save
from django.core.mail import send_mail
from django.conf import settings
# Create your models here.
logger = logging.getLogger(__name__)


class IoTDevice(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
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

    def predict_and_update_status(self):
        """Predict and update the device's status using AI."""
        # Extract features
        firmware_version_major = self.extract_firmware_version_major()
        mac_address_colon_count = self.mac_address.count(':') if self.mac_address else 0

        device_features = [firmware_version_major, mac_address_colon_count]
        predicted_status = predict_device_status(device_features)

        # Map predicted status to STATUS_CHOICES
        status_mapping = {
            1: 'active',
            2: 'faulty',
            3: 'maintenance',
            4: 'disconnected'
        }
        self.status = status_mapping.get(predicted_status, 'inactive')
        self.save()

    def extract_firmware_version_major(self):
        """Extract major version number from firmware_version."""
        try:
            return int(self.firmware_version.split('.')[0].replace('v', ''))
        except (ValueError, IndexError):
            return 0

    def __str__(self):
        return f"{self.device_id} ({self.device_type})"


class SensorData(models.Model):
    device = models.ForeignKey(IoTDevice, on_delete=models.CASCADE, related_name='sensor_data')
    data = models.JSONField(blank=True, null=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Data from {self.device.device_id} at {self.timestamp.date()}"


@receiver(pre_save, sender=SensorData)
def auto_fill_sensor_data(sender, instance, **kwargs):
    """Automatically fill sensor data based on device type."""
    if not instance.data:
        default_data = {
            'sensor': {"sensor_reading": 100},
            'actuator': {"actuator_state": "off"},
            'gateway': {"connected_devices": 5},
            'camera': {"image_capture": "base64_image_data"},
            'thermostat': {"current_temperature": 22.5, "target_temperature": 24.0}
        }
        instance.data = default_data.get(instance.device.device_type, {"default": "no specific data"})


@receiver(post_save, sender=SensorData)
def analyze_sensor_data(sender, instance, **kwargs):
    """Analyze sensor data using AI and send notifications if necessary."""
    user_email = instance.device.user.email
    device_type = instance.device.device_type
    data = instance.data

    if device_type == 'sensor':
        sensor_reading = data.get('sensor_reading')
        if sensor_reading is not None:
            if predict_sensor_anomaly(sensor_reading):
                logger.warning(f"Anomaly detected in device {instance.device.device_id} (Sensor) with reading {sensor_reading}")
                send_mail(
                    subject='Anomaly Detected in IoT Device',
                    message=f'An anomaly was detected in Sensor device {instance.device.device_id} with reading {sensor_reading}.',
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[user_email],
                    fail_silently=False,
                )

    elif device_type == 'actuator':
        actuator_state = data.get('actuator_state')
        if actuator_state == 'error':
            logger.warning(f"Error state detected in Actuator {instance.device.device_id}")
            instance.device.update_status('inactive')
            logger.info(f"Actuator {instance.device.device_id} was shut down due to an error state.")

    elif device_type == 'gateway':
        connected_devices = data.get('connected_devices', 0)
        if connected_devices > 50:
            logger.warning(f"High number of connected devices in Gateway {instance.device.device_id}: {connected_devices}")
            send_mail(
                subject='High Number of Connections in Gateway',
                message=f'Gateway device {instance.device.device_id} has {connected_devices} connected devices.',
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[user_email],
                fail_silently=False,
            )

    elif device_type == 'camera':
        image_capture = data.get('image_capture')
        if image_capture:
            logger.warning(f"Suspicious image captured by Camera {instance.device.device_id}")
            send_mail(
                subject='Suspicious Image Detected',
                message=f'A suspicious image was captured by Camera {instance.device.device_id}.',
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[user_email],
                fail_silently=False,
            )

    elif device_type == 'thermostat':
        current_temperature = data.get('current_temperature')
        target_temperature = data.get('target_temperature')

        if (current_temperature or target_temperature) and (current_temperature > 30.0 or target_temperature > 30.0):
            logger.warning(f"High temperature detected by Thermostat {instance.device.device_id}: {current_temperature}°C")
            send_mail(
                subject='High Temperature Alert',
                message=f'A high temperature of {current_temperature}°C was detected by Thermostat {instance.device.device_id}.',
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[user_email],
                fail_silently=False,
            )

@receiver(post_save, sender=IoTDevice)
def update_device_status(sender, instance, **kwargs):
    """
    Signal to predict and update the device status using AI after it is saved.
    """
    # Avoid recursion by checking if the status has actually changed
    if kwargs.get('created', False) or not hasattr(instance, '_status_updated'):
        instance._status_updated = True
        instance.predict_and_update_status()
