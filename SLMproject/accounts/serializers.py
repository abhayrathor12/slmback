from django.contrib.auth import authenticate
from .models import CustomUser
from SLMapp.models import Topic
from rest_framework import serializers
from django.contrib.auth import authenticate
from .models import CustomUser, StudentProfile, ProfessionalProfile,UserCertificate

from rest_framework import serializers
from .models import SupportConversation, SupportMessage

class UserRegisterSerializer(serializers.ModelSerializer):

    password = serializers.CharField(write_only=True)

    # student
    current_year = serializers.CharField(required=False)
    stream = serializers.CharField(required=False)
    passing_year = serializers.CharField(required=False) 
    interest = serializers.CharField(required=False)

    # professional
    company = serializers.CharField(required=False)
    city = serializers.CharField(required=False)
    company_email = serializers.EmailField(
        required=False,
        allow_null=True,
        allow_blank=True
    )

    class Meta:
        model = CustomUser
        fields = [
            "email",
            "passing_year",
            "password",
            "role",
            "phone",
            "first_name",
            "last_name",
            "current_year",
            "stream",
            "interest",
            "company",
            "city",
            "company_email",
        ]

    def create(self, validated_data):

        password = validated_data.pop("password")
        role = validated_data.pop("role")

        student_data = {}
        professional_data = {}

        if role == "student":
            student_data = {
                "current_year": validated_data.pop("current_year", None),
                "stream": validated_data.pop("stream", None),
                "passing_year": validated_data.pop("passing_year", None),
                "interest": validated_data.pop("interest", None),
                "city": validated_data.pop("city", None),
            }

        elif role == "professional":
            company_email = validated_data.pop("company_email", None)
            professional_data = {
                "company": validated_data.pop("company", None),
                "city": validated_data.pop("city", None),
                "interest": validated_data.pop("interest", None),
                "company_email": company_email if company_email else None,
            }

        # ✅ Create user
        user = CustomUser.objects.create(
            role=role,
            is_active=False,
            **validated_data
        )

        user.set_password(password)
        user.save()

        # ✅ Assign default topic (id = 10)
        default_topic = Topic.objects.filter(id=10).first()
        if default_topic:
            user.topics.add(default_topic)

        # ✅ Create profile
        if role == "student":
            StudentProfile.objects.create(user=user, **student_data)

        elif role == "professional":
            ProfessionalProfile.objects.create(user=user, **professional_data)

        return user



class UserLoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)

    def validate(self, data):

        user = authenticate(
            email=data["email"],
            password=data["password"]
        )

        if not user:
            raise serializers.ValidationError("Invalid email or password")

        if not user.is_active:
            raise serializers.ValidationError("Account not active")

        data["user"] = user
        return data



class StudentProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = StudentProfile
        fields = "__all__"


class ProfessionalProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProfessionalProfile
        fields = "__all__"
        
class UserSerializer(serializers.ModelSerializer):

    student_profile = StudentProfileSerializer(read_only=True)
    professional_profile = ProfessionalProfileSerializer(read_only=True)

    class Meta:
        model = CustomUser
        fields = "__all__"


class ToggleActiveSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = ['id', 'is_active']
        read_only_fields = ['id']

    def update(self, instance, validated_data):
        instance.is_active = not instance.is_active
        instance.save()
        return instance




class SupportMessageSerializer(serializers.ModelSerializer):
    screenshot = serializers.SerializerMethodField()

    class Meta:
        model = SupportMessage
        fields = ["id", "sender", "message", "screenshot", "created_at"]

    def get_screenshot(self, obj):
        request = self.context.get("request")
        if obj.screenshot:
            if request:
                return request.build_absolute_uri(obj.screenshot.url)
            return obj.screenshot.url
        return None



class SupportConversationSerializer(serializers.ModelSerializer):
    messages = serializers.SerializerMethodField()

    class Meta:
        model = SupportConversation
        fields = ["id", "created_at", "messages"]

    def get_messages(self, obj):
        request = self.context.get("request")
        return SupportMessageSerializer(
            obj.messages.all().order_by("created_at"),
            many=True,
            context={"request": request},
        ).data

        
from rest_framework import serializers
from .models import Feedback

class FeedbackSerializer(serializers.ModelSerializer):
    class Meta:
        model = Feedback
        fields = ["id", "rating", "message", "created_at"]


class UserCertificateSerializer(serializers.ModelSerializer):
    certificate_file = serializers.SerializerMethodField()

    class Meta:
        model = UserCertificate
        fields = ["id", "certificate_file", "uploaded_at"]

    def get_certificate_file(self, obj):
        request = self.context.get("request")
        if obj.certificate_file:
            if request:
                return request.build_absolute_uri(obj.certificate_file.url)
            return obj.certificate_file.url
        return None