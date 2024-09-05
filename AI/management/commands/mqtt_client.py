from django.core.management.base import BaseCommand
import paho.mqtt.client as mqtt
from AI.models import IoTDevice, SensorData
import json


class Command(BaseCommand):
    help = 'Run the MQTT client to process IoT device data'

    def handle(self, *args, **kwargs):
        def on_connect(client, userdata, flags, rc):
            if rc == 0:
                self.stdout.write(self.style.SUCCESS('Connected to MQTT broker successfully'))
                client.subscribe("devices/+/data")
            else:
                self.stdout.write(self.style.ERROR(f'Failed to connect, return code {rc}'))

        def on_message(client, userdata, msg):
            try:
                device_id = msg.topic.split('/')[-2]  # Assuming the device_id is part of the topic
                device, created = IoTDevice.objects.get_or_create(device_id=device_id, defaults={'device_type': 'sensor'})
                
                if created:
                    self.stdout.write(self.style.SUCCESS(f'Device with id {device_id} created'))
                else:
                    self.stdout.write(self.style.SUCCESS(f'Device with id {device_id} found'))

                SensorData.objects.create(device=device, data=msg.payload.decode())
                self.stdout.write(self.style.SUCCESS(f'Data received from {device_id} and saved'))

            except json.JSONDecodeError:
                self.stdout.write(self.style.ERROR('Failed to decode JSON data'))
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'Error processing message: {str(e)}'))

        client = mqtt.Client()
        client.on_connect = on_connect
        client.on_message = on_message

        try:
            client.connect("test.mosquitto.org", 1883, 60)
            client.loop_forever()
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error connecting to MQTT broker: {str(e)}'))
