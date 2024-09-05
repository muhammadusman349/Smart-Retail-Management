from rest_framework import status, viewsets, permissions, mixins
from rest_framework.response import Response
from .serializers import (
                UserSerializer, UserRoleUpdateSerializer,
                SignupSerializer, LoginSerializer,
                ChangePasswordSerializer, ForgetPasswordSerializer,
                ResetPasswordSerializer
                )
from django.contrib.auth import logout
from django.core.exceptions import PermissionDenied
from rest_framework.permissions import IsAuthenticated, AllowAny
from .models import User
from .tasks import send_role_update_email


class UserView(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_permissions(self):
        """
        Allow only admins to create, update, or delete users.
        """
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            self.permission_classes = [permissions.IsAdminUser]
        return super().get_permissions()


class UserRoleUpdateView(mixins.UpdateModelMixin, viewsets.GenericViewSet):
    queryset = User.objects.all()
    serializer_class = UserRoleUpdateSerializer
    permission_classes = [permissions.IsAdminUser]

    def perform_update(self, serializer):
        instance = serializer.save()
        # Send an email notification role is updated to 'staff' or 'manager'
        if instance.role in ['staff', 'manager']:
            send_role_update_email.delay(instance.email, instance.role)

    def get_object(self):
        user = super().get_object()
        request = self.request
        # only an admin can change the user role
        if not request.user.is_superuser:
            raise PermissionDenied("Only an admin can change the user role.")
        return user


class SignupView(viewsets.ModelViewSet):
    queryset = User.objects.all()
    permission_classes = [AllowAny]
    serializer_class = SignupSerializer
    authentication_classes = []

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class LoginView(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = LoginSerializer
    permission_classes = [AllowAny]
    authentication_classes = []

    def create(self, request):
        serializer = self.serializer_class(
            data=request.data, context={"request": self.request})
        if serializer.is_valid():
            return Response(serializer.validated_data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class LogoutView(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        logout(request)
        return Response({"msg":"Successfully Logged out"},status=status.HTTP_200_OK)


class ChangePasswordView(viewsets.GenericViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = ChangePasswordSerializer
    authentication_classes = []

    def create(self, request):
        serializer = self.serializer_class(data=request.data, context={
                                           'user': self.request.user})
        if serializer.is_valid():
            serializer.save()
            return Response({'password': ' password changed successfully'}, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ForgetPasswordView(viewsets.ModelViewSet):
    permission_classes = [AllowAny]
    serializer_class = ForgetPasswordSerializer
    authentication_classes = []

    def create(self, request):
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():
            return Response({'opt': 'successfully send OTP '}, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ResetPasswordView(viewsets.ModelViewSet):
    permission_classes = [AllowAny]
    serializer_class = ResetPasswordSerializer
    authentication_classes = []

    def create(self, request):
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():
            return Response({'password': 'successfully set New Password'}, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
