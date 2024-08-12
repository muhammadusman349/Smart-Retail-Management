from django.urls import path, include
from .views import (
        SignupView, LoginView,
        LogoutView, ChangePasswordView,
        ForgetPasswordView, ResetPasswordView
        )
from rest_framework_simplejwt import views as jwt_views
from rest_framework.routers import DefaultRouter

router = DefaultRouter()
router.register(r'signup', SignupView, basename='signup')
router.register(r'login', LoginView, basename='login')
router.register(r'logout', LogoutView, basename='logout')
router.register(r'changepassword', ChangePasswordView, basename='change-password')
router.register(r'forget_password', ForgetPasswordView, basename='forget-password')
router.register(r'reset_password', ResetPasswordView, basename='reset-password')

urlpatterns = [
    path('token-refresh/', jwt_views.TokenRefreshView.as_view(), name='token_refresh'),
    path('', include(router.urls)),
]