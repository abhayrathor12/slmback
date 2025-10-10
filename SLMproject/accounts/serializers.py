from rest_framework import serializers
from django.contrib.auth import authenticate
from .models import CustomUser
from SLMapp.models import Topic

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = ["id", "username", "email", "role"]

class UserRegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)
    topics = serializers.PrimaryKeyRelatedField(
        queryset=Topic.objects.all(), many=True, required=False
    )

    class Meta:
        model = CustomUser
        fields = ["id", "username", "email", "password", "role", "phone", "dob", "topics"]

    def create(self, validated_data):
        topics = validated_data.pop("topics", [])
        user = CustomUser(
            username=validated_data["username"],
            email=validated_data.get("email"),
            role=validated_data.get("role", "student"),
            phone=validated_data.get("phone"),
            dob=validated_data.get("dob"),
        )
        user.set_password(validated_data["password"])
        user.save()
        user.topics.set(topics)
        return user


class UserLoginSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField(write_only=True)

    def validate(self, data):
        user = authenticate(username=data["username"], password=data["password"])
        if not user:
            raise serializers.ValidationError("Invalid username or password")
        data["user"] = user
        return data
