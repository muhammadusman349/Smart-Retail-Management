from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import IoTDeviceView, SensorDataView

router = DefaultRouter()
router.register(r'devices', IoTDeviceView)
router.register(r'sensor-data', SensorDataView)

urlpatterns = [
    path('', include(router.urls)),
]
