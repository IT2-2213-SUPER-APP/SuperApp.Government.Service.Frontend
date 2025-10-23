from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers
from .models import User, Profile


class ProfileSerializer(serializers.ModelSerializer):
    """
    Serializer for the user Profile model.
    """
    class Meta:
        model = Profile
        fields = ['bio', 'avatar']


class UserSerializer(serializers.ModelSerializer):
    """
    Serializer for the User model, including the nested profile.
    """
    profile = ProfileSerializer()

    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'profile']


class RegisterSerializer(serializers.ModelSerializer):
    """
    Serializer for user registration.

    Includes password confirmation and validation. The password fields are
    write-only for security, and the create method handles hashing the password.
    """
    # Add a password confirmation field.
    password2 = serializers.CharField(style={'input_type': 'password'}, write_only=True)

    class Meta:
        model = User
        fields = ['username', 'email', 'password', 'password2']
        extra_kwargs = {
            'password': {'write_only': True}
        }

    def validate(self, attrs):
        """
        Check that the two password entries match.
        """
        if attrs['password'] != attrs['password2']:
            raise serializers.ValidationError({"password": "Password fields didn't match."})

        # You can also run Django's built-in password validators
        validate_password(attrs['password'])

        return attrs

    def create(self, validated_data):
        """
        Create and return a new user with a hashed password and a profile.
        """
        # Remove the confirmation password from the data to be saved.
        validated_data.pop('password2')

        # Use the custom User model's create_user method to handle hashing.
        user = User.objects.create_user(**validated_data)

        # Create a blank profile for the new user.
        Profile.objects.create(user=user)

        return user
