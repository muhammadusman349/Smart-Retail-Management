import pyotp
import base64
from django.core.exceptions import PermissionDenied
from rest_framework import serializers, status
from rest_framework_simplejwt.tokens import RefreshToken
from .models import User, OtpVerify
from datetime import datetime
from django.utils import timezone
from account.tasks import send_email
from account import USER_ROLE_CHOICES


class generateKey:
    @staticmethod
    def returnValue(userObj):
        return str(timezone.now()) + str(datetime.date(datetime.now())) + str(userObj.id)


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = [
            'id',
            'first_name',
            'last_name',
            'email',
            'profile_picture',
            'role',
            'is_verified',
            'is_active',
            'is_approved',
            'is_owner',
            'is_staff',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'role', 'is_verified', 'is_active', 'is_approved', 'is_owner', 'is_staff', 'created_at', 'updated_at']


class UserRoleUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['role']

    def validate(self, attrs):
        valid_roles = [choice[0] for choice in USER_ROLE_CHOICES]
        if attrs not in valid_roles:
            raise serializers.ValidationError("Role is Required!")
        return super().validate(attrs)

    def update(self, instance, validated_data):
        new_role = validated_data.get('role')
        # Check if the new role is the same as the current role
        if instance.role == new_role:
            raise serializers.ValidationError({"error": "This role is already assigned ! Select another role."}, status=status.HTTP_400_BAD_REQUEST)

        instance.role = validated_data['role']
        instance.save()
        return instance


class SignupSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = [
            'id',
            'first_name',
            'last_name',
            'email',
            'profile_picture',
            'password',
        ]
        read_only_field = ['id', 'photo_url',]

    def validate(self, attrs):
        email = attrs.get('email', '')
        request = self.context.get('request', None)
        if request and request.method == "POST":
            if User.objects.filter(email__iexact=email).exists():
                return serializers.ValidationError(
                    'Email already exist! Please, try another email')
        return attrs

    def create(self, validated_data):
        if "profile_picture" in validated_data:
            profile_picture = validated_data["profile_picture"]
        else:
            profile_picture = None

        newuser = User.objects.create(
                        first_name=validated_data['first_name'],
                        last_name=validated_data['last_name'],
                        email=validated_data['email'],
                        profile_picture=profile_picture,
                        role='customer',
                        is_verified=True,
                        is_active=True,
                        is_approved=True,
                        )
        newuser.set_password(validated_data['password'])
        newuser.save()
        return newuser


class LoginSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(max_length=120, required=True, min_length=3)
    password = serializers.CharField(max_length=100, required=True, style={
                                    'input_type': 'password'}, write_only=True)
    access_token = serializers.CharField(max_length=200, min_length=5,
                                         read_only=True)
    refresh_token = serializers.CharField(max_length=200, min_length=5,
                                          read_only=True)

    class Meta:
        model = User
        fields = ['id', 'email', 'password', 'access_token', 'refresh_token',]
        read_only_fields = ['access_token', 'refresh_token']

    def validate(self, attrs):
        email = attrs.get('email')
        password = attrs.get('password')

        try:
            user = User.objects.get(email__iexact=email)
        except User.DoesNotExist:
            raise serializers.ValidationError({"error": "provide credential are not valid/email"}, code=status.HTTP_401_UNAUTHORIZED)
        if user:
            if not user.check_password(password):
                raise serializers.ValidationError({'error': 'provided credentials are not valid/password'}, code=status.HTTP_401_UNAUTHORIZED)

        token = RefreshToken.for_user(user)
        attrs = {}
        attrs["id"] = str(user.id)
        attrs['first_name'] = str(user.first_name)
        attrs['last_name'] = str(user.last_name)
        attrs['email'] = str(user.email)
        attrs['access_token'] = str(token.access_token)
        attrs['refresh_token'] = str(token)
        return attrs


class ChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField(required=True)
    new_password = serializers.CharField(required=True)

    def validate(self, attrs):
        user_email = str(self.context['user'])
        new_password = attrs.get("new_password", None)
        old_password = attrs.get("old_password", None)
        try:
            user = User.objects.get(email=user_email)
        except User.DoesNotExist:
            raise serializers.ValidationError(
                {"error ": "User not found."})
        if not user.check_password(old_password):
            raise serializers.ValidationError(
                {"error": "Incorrect Password"})
        if new_password and len(new_password) > 5:
            if user.check_password(new_password):
                raise serializers.ValidationError(
                    {"error": "New password should not be same as old_password"})
        else:
            raise serializers.ValidationError(
                {"error": "Minimum length of new Password should be greater than 5"})
        return attrs

    def create(self, validated_data):
        user = self.context['user']
        user.set_password(validated_data.get("new_password"))
        user.save()
        return validated_data


class ForgetPasswordSerializer(serializers.Serializer):
    email = serializers.EmailField(max_length=255)

    def validate(self, attrs):
        email = attrs.get("email", None)
        if email is not None:
            try:
                userObj = User.objects.get(email__iexact=email)
                key = base64.b32encode(generateKey.returnValue(userObj).encode())
                otp_key = pyotp.TOTP(key)  
                otp = otp_key.at(6)
                otp_obj = OtpVerify()
                otp_obj.user = userObj
                otp_obj.otp = otp
                otp_obj.save()

                # send mail 
                subject = "Your OTP Code"
                message = f"YOur OTP code is {otp}. Please use this to reset your password."
                recipient_list = [email]
                send_email.delay(subject, message, recipient_list)

            except Exception as e:
                print("Exception", e)
                raise serializers.ValidationError(
                    {"email": "Valid email is Required"})
        else:
            raise serializers.ValidationError({"email": "email is required"})
        return attrs


class ResetPasswordSerializer(serializers.Serializer):
    otp = serializers.CharField(required=True)
    password = serializers.CharField(required=True, write_only=True)

    def validate(self, attrs):
        otp = attrs.get("otp", None)
        password = attrs.get("password", None)
        if otp:
            try:
                otpobj = OtpVerify.objects.filter(otp=otp).first()
                if otpobj:
                    otpobj.user.set_password(password)
                    otpobj.delete()
                    otpobj.user.save()
                else:
                    raise OtpVerify.DoesNotExist
            except OtpVerify.DoesNotExist:
                raise serializers.ValidationError(
                    {"error": "Valid OTP is Required"})
        else:
            raise serializers.ValidationError({"error": "email is required"})
        return attrs
