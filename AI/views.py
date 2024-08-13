from rest_framework import viewsets, status
from rest_framework.response import Response
from .models import IoTDevice, SensorData
from .serializers import IoTDeviceSerializer, SensorDataSerializer
from rest_framework.decorators import action
from .utils import DEVICE_TYPES, STATUS_CHOICES
from django.utils import timezone

# Create your views here.


class IoTDeviceView(viewsets.ModelViewSet):
    queryset = IoTDevice.objects.all()
    serializer_class = IoTDeviceSerializer
    authentication_classes = []
    permission_classes = []

    @action(detail=True, methods=['post'])
    def update_device_status(self, request, pk=None):

        device = self.get_object()
        new_status = request.data.get('status')
        if new_status not in dict(STATUS_CHOICES).keys():
            return Response({'error': 'Invalid Status'}, status=status.HTTP_400_BAD_REQUEST)

        device.update_status(new_status)
        return Response({'status': 'Status updated successfully'}, status=status.HTTP_200_OK)


class SensorDataView(viewsets.ModelViewSet):
    queryset = SensorData.objects.all()
    serializer_class = SensorDataSerializer
    authentication_classes = []
    permission_classes = []

    def create(self, request, *args, **kwargs):
        device_id = request.data.get('device_id')
        device = IoTDevice.objects.filter(device_id=device_id).first()
        if not device:
            return Response({'error': 'Device not found'}, status=status.HTTP_400_BAD_REQUEST)        
        data = request.data.get('data')
        sensor_data = SensorData.objects.create(device=device, data=data)
        return Response(SensorDataSerializer(sensor_data).data, status=status.HTTP_200_OK)