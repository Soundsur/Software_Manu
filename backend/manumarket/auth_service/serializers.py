# /backend/auth_service/serializers.py

from rest_framework import serializers
from django.contrib.auth import get_user_model
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

User = get_user_model()

# ------------------------------
# Serializador para crear un nuevo usuario
# ------------------------------

class UserCreateSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=6)
    password_confirm = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ['username', 'email', 'first_name', 'last_name', 'role', 'password', 'password_confirm']

    def validate(self, attrs):
        # Validar que las contraseñas coincidan
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError("Las contraseñas no coinciden")
        return attrs

    def create(self, validated_data):
        validated_data.pop('password_confirm')  # Eliminar la confirmación de contraseña
        password = validated_data.pop('password')  # Obtener la contraseña
        user = User.objects.create_user(**validated_data)  # Crear el usuario
        user.set_password(password)  # Establecer la contraseña cifrada
        user.save()
        return user


# ------------------------------
# Serializador para obtener el token JWT
# ------------------------------

class MyTokenObtainPairSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        # Agregar información extra al token
        token['username'] = user.username
        token['first_name'] = user.first_name
        token['last_name'] = user.last_name
        token['role'] = getattr(user, 'role', '')
        token['full_name'] = f"{user.first_name} {user.last_name}".strip() or user.username
        return token


# ------------------------------
# Serializador para mostrar los datos del usuario
# ------------------------------

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'role', 'first_name', 'last_name', 'is_active', 'date_joined']


# ------------------------------
# Serializador para actualizar datos del usuario
# ------------------------------

class UserUpdateSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=False, min_length=6)

    class Meta:
        model = User
        fields = ['username', 'email', 'first_name', 'last_name', 'role', 'is_active', 'password']

    def update(self, instance, validated_data):
        password = validated_data.pop('password', None)
        
        # Actualizar campos normales
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        
        # Actualizar la contraseña si es proporcionada
        if password:
            instance.set_password(password)
        
        instance.save()
        return instance
