from rest_framework import generics, permissions
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from .models import CustomUser
from .serializers import UserSerializer, UserRegisterSerializer, UserLoginSerializer,ToggleActiveSerializer
from django.shortcuts import render
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework import status

from SLMapp.views import Topic
class UserRegisterView(generics.CreateAPIView):
    queryset = CustomUser.objects.all()
    serializer_class = UserRegisterSerializer
    permission_classes = [AllowAny]
    
class UserDeleteView(generics.DestroyAPIView):
    queryset = CustomUser.objects.all()
    permission_classes = [IsAuthenticated]
    
class UserLoginView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = UserLoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data["user"]

        refresh = RefreshToken.for_user(user)

        return Response({
            "user": {
                "id": user.id,
                "first_name": user.first_name,
                "email": user.email,
                "role": user.role,
            },
            "refresh": str(refresh),
            "access": str(refresh.access_token),
        })
        
class LogoutView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            refresh_token = request.data.get("refresh")
            if not refresh_token:
                return Response({"error": "Refresh token required"}, status=status.HTTP_400_BAD_REQUEST)

            token = RefreshToken(refresh_token)
            token.blacklist()  # blacklist the refresh token
            return Response({"detail": "Logout successful"}, status=status.HTTP_205_RESET_CONTENT)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
class UserListView(generics.ListAPIView):
    queryset = CustomUser.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]

class UserDetailView(generics.RetrieveAPIView):
    queryset = CustomUser.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]


class ToggleUserActiveView(generics.UpdateAPIView):
    queryset = CustomUser.objects.all()
    serializer_class = ToggleActiveSerializer
    permission_classes = [IsAuthenticated]
    http_method_names = ['patch']  # block PUT, only allow PATCH



from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from .models import SupportConversation, SupportMessage
from .serializers import SupportConversationSerializer,FeedbackSerializer


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def get_or_create_conversation(request):
    conversation, created = SupportConversation.objects.get_or_create(
        user=request.user
    )

    serializer = SupportConversationSerializer(
        conversation,
        context={"request": request}
    )
    return Response(serializer.data)



@api_view(["POST"])
@permission_classes([IsAuthenticated])
def send_message(request):
    conversation, created = SupportConversation.objects.get_or_create(
        user=request.user
    )

    message = request.data.get("message", "")
    screenshot = request.FILES.get("screenshot")

    if not message and not screenshot:
        return Response({"error": "Message or screenshot required"}, status=400)

    SupportMessage.objects.create(
        conversation=conversation,
        sender="user",
        message=message,
        screenshot=screenshot
    )

    serializer = SupportConversationSerializer(
    conversation,
    context={"request": request}
    )
    return Response(serializer.data)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def submit_feedback(request):
    serializer = FeedbackSerializer(data=request.data)

    if serializer.is_valid():
        serializer.save(user=request.user)
        return Response({"message": "Feedback submitted successfully"})
    
    return Response(serializer.errors, status=400)

from .models import UserCertificate
from .serializers import UserCertificateSerializer
from rest_framework.parsers import MultiPartParser, FormParser
from django.shortcuts import get_object_or_404
from rest_framework.permissions import IsAdminUser


class UploadUserCertificateView(APIView):
    permission_classes = [IsAdminUser]
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request, user_id):
        user = get_object_or_404(CustomUser, id=user_id)
        topic = get_object_or_404(Topic, id=10)

        file = request.FILES.get("certificate_file")

        if not file:
            return Response({"error": "Certificate file required"}, status=400)

        certificate, created = UserCertificate.objects.update_or_create(
            user=user,
            topic=topic,
            defaults={"certificate_file": file}
        )

        return Response({"message": "Certificate uploaded successfully"})


class StudentCertificateView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        certificate = UserCertificate.objects.filter(
            user=request.user
        ).first()

        if not certificate:
            return Response({
                "certificate_url": None
            })

        return Response({
            "certificate_url": request.build_absolute_uri(
                certificate.certificate_file.url
            )
        })
    

from rest_framework import generics
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from .models import SupportConversation
from .serializers import SupportConversationSerializer

class AdminConversationListView(generics.ListAPIView):
    serializer_class = SupportConversationSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        if self.request.user.role != "admin":
            return SupportConversation.objects.none()

        return SupportConversation.objects.select_related("user") \
            .all() \
            .order_by("-created_at")

    def list(self, request, *args, **kwargs):
        if request.user.role != "admin":
            return Response({"error": "Unauthorized"}, status=403)

        queryset = self.get_queryset()

        data = [
            {
                "id": convo.id,
                "user_email": convo.user.email,
                "created_at": convo.created_at,
            }
            for convo in queryset
        ]

        return Response(data)
    
    
class AdminConversationDetailView(generics.RetrieveAPIView):
    serializer_class = SupportConversationSerializer
    permission_classes = [IsAuthenticated]
    lookup_field = "id"
    queryset = SupportConversation.objects.all()

    def retrieve(self, request, *args, **kwargs):
        if request.user.role != "admin":
            return Response({"error": "Unauthorized"}, status=403)

        conversation = self.get_object()

        serializer = self.get_serializer(
            conversation,
            context={"request": request}
        )

        return Response(serializer.data)
    
from rest_framework.views import APIView

class AdminSendMessageView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, convo_id):
        if request.user.role != "admin":
            return Response({"error": "Unauthorized"}, status=403)

        try:
            conversation = SupportConversation.objects.get(id=convo_id)
        except SupportConversation.DoesNotExist:
            return Response({"error": "Not found"}, status=404)

        message = request.data.get("message", "")
        screenshot = request.FILES.get("screenshot")

        if not message and not screenshot:
            return Response({"error": "Message required"}, status=400)

        SupportMessage.objects.create(
            conversation=conversation,
            sender="admin",
            message=message,
            screenshot=screenshot
        )

        serializer = SupportConversationSerializer(
            conversation,
            context={"request": request}
        )

        return Response(serializer.data)