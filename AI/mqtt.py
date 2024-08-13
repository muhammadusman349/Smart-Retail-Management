import paho.mqtt.client as mqtt
from .models import IoTDevice, SensorData


def on_connect(client, userdata, flags, rc):
    client.subscribe("sensor/data")


def on_message(client, userdata, msg):
    device_id = msg.topic.split('/')[-1]
    device = IoTDevice.objects.filter(device_id=device_id).first()
    if device:
        SensorData.objects.create(device=device, data=msg.payload.decode())


client = mqtt.Client()
client.on_connect = on_connect
client.on_message = on_message
client.connect("mqtt.broker.address", 1883, 60)
# client.subscribe("devices/+/data")
client.loop_start()
