# learning/views.py
from rest_framework import generics, permissions, status
from .serializers import TopicSerializer, QuizSerializer
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.response import Response
from rest_framework.views import APIView
from django.shortcuts import get_object_or_404
from .models import Topic, Module, Page, Progress, Quiz, QuizResult
from .serializers import *
from rest_framework.decorators import action
from django.db.models import Q
from django.shortcuts import render
from .models import CustomUser
from .serializers import *
from rest_framework import viewsets, permissions
from .models import Topic, Module, MainContent, Page
from .serializers import *
from accounts.serializers import *

class TopicViewSet(viewsets.ModelViewSet):
    queryset = Topic.objects.all().order_by("order")
    serializer_class = TopicSerializer
    permission_classes = [permissions.IsAuthenticated]


class ModuleViewSet(viewsets.ModelViewSet):
    queryset = Module.objects.all().order_by("order")
    serializer_class = ModuleSerializer
    permission_classes = [permissions.IsAuthenticated]


class MainContentViewSet(viewsets.ModelViewSet):
    queryset = MainContent.objects.all().order_by("order")
    serializer_class = MainContentSerializer
    permission_classes = [permissions.IsAuthenticated]


class PageViewSet(viewsets.ModelViewSet):
    queryset = Page.objects.all().order_by("order")
    serializer_class = PageSerializer
    permission_classes = [permissions.IsAuthenticated]

# ----------------------------
# Detail Views
# ----------------------------

class TopicListView(generics.ListAPIView):
    queryset = Topic.objects.all().order_by("order")
    serializer_class = TopicSerializer
    permission_classes = [permissions.IsAuthenticated]


class ModuleDetailView(generics.RetrieveAPIView):
    queryset = Module.objects.all()
    serializer_class = ModuleSerializer
    permission_classes = [permissions.IsAuthenticated]


class MainContentDetailView(generics.RetrieveAPIView):
    queryset = MainContent.objects.all()
    serializer_class = MainContentSerializer
    permission_classes = [permissions.IsAuthenticated]


class PageDetailView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, page_id):
        page = get_object_or_404(Page, id=page_id)
        serializer = PageSerializer(page, context={'request': request})
        return Response(serializer.data)
    
    
# ----------------------------
# Completion Views
# ----------------------------

class CompletePageView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, page_id):
        page = get_object_or_404(Page, id=page_id)
        PageProgress.objects.update_or_create(
            user=request.user,
            page=page,
            defaults={"completed": True}
        )

        # If last page → mark maincontent complete
        last_page = page.main_content.pages.order_by("-order").first()
        if last_page and page.id == last_page.id:
            MainContentProgress.objects.update_or_create(
                user=request.user,
                main_content=page.main_content,
                defaults={"completed": True}
            )

        return Response({"message": f"Page {page.order} marked as completed"})


class CompleteMainContentView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, maincontent_id):
        maincontent = get_object_or_404(MainContent, id=maincontent_id)
        MainContentProgress.objects.update_or_create(
            user=request.user,
            main_content=maincontent,
            defaults={"completed": True}
        )

        # If all maincontents in module are done → mark module complete
        module = maincontent.module
        all_done = all(
            MainContentProgress.objects.filter(user=request.user, main_content=mc, completed=True).exists()
            for mc in module.main_contents.all()
        )
        if all_done:
            Progress.objects.update_or_create(
                user=request.user,
                module=module,
                defaults={"completed": True}
            )

        return Response({"message": f"MainContent '{maincontent.title}' marked as completed"})


class CompleteModuleView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, module_id):
        module = get_object_or_404(Module, id=module_id)
        Progress.objects.update_or_create(
            user=request.user,
            module=module,
            defaults={"completed": True}
        )
        return Response({"message": f"Module '{module.title}' marked as completed"})


class QuizView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, topic_id):
        quiz = get_object_or_404(Quiz, topic_id=topic_id)
        serializer = QuizSerializer(quiz)
        return Response(serializer.data)


class SubmitQuizView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, topic_id):
        quiz = get_object_or_404(Quiz, topic_id=topic_id)
        answers = request.data.get("answers", {})  # {question_id: choice_id}
        score = 0
        for q in quiz.questions.all():
            correct = q.choices.filter(is_correct=True).first()
            if str(q.id) in answers and str(correct.id) == str(answers[str(q.id)]):
                score += 1
        passed = score >= quiz.questions.count() * 0.6
        QuizResult.objects.create(
            user=request.user,
            quiz=quiz,
            score=score,
            passed=passed
        )
        return Response({"score": score, "passed": passed})


class QuizViewSet(viewsets.ModelViewSet):
    queryset = Quiz.objects.all()
    serializer_class = QuizSerializer

    @action(detail=True, methods=["post"])
    def add_question(self, request, pk=None):
        quiz = self.get_object()
        serializer = QuestionSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(quiz=quiz)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    
    
    def get_queryset(self):
        qs = super().get_queryset()
        main_content = self.request.query_params.get("main_content")
        if main_content:
            qs = qs.filter(main_content_id=main_content)
        return qs
    
    
    
    @action(detail=True, methods=["post"])
    def submit(self, request, pk=None):
        quiz = self.get_object()   # quiz/<pk> is still the quiz ID
        answers = request.data.get("answers", {})  # {question_id: choice_id}
        score = 0

        for q in quiz.questions.all():
            correct = q.choices.filter(is_correct=True).first()
            if str(q.id) in answers and str(correct.id) == str(answers[str(q.id)]):
                score += 1

        passed = score >= quiz.questions.count() * 0.6

        QuizResult.objects.create(
            user=request.user,
            quiz=quiz,
            score=score,
            passed=passed,
        )

        return Response({"score": score, "passed": passed})



class UserProgressSummary(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        user = request.user
        total_modules = Module.objects.count()

        completed_modules = 0
        in_progress_modules = 0
        not_started_modules = 0

        for module in Module.objects.all():
            # ✅ check if module is fully completed
            if Progress.objects.filter(user=user, module=module, completed=True).exists():
                completed_modules += 1
            else:
                # ✅ check if any page inside this module is completed
                any_page_done = PageProgress.objects.filter(
                    user=user, page__main_content__module=module, completed=True
                ).exists()

                if any_page_done:
                    in_progress_modules += 1
                else:
                    not_started_modules += 1

        return Response({
            "total_modules": total_modules,
            "completed_modules": completed_modules,
            "in_progress_modules": in_progress_modules,
            "not_started_modules": not_started_modules,
        })

def login_page(request):
    return render(request,"login.html")

def register_page(request):
    return render(request,"register.html")

def add_module(request):
    return render(request,"add_module.html")

def add_topic(request):
    return render(request,"add_topic.html")

def add_page(request):
    return render(request,"add_page.html")


def edit_page(request, pk):
    return render(request, "edit_page.html", {"page_id": pk})

def add_maincontent(request):
    return render(request,"add_maincontent.html")


def edit_maincontent(request, pk):
    return render(request, "edit_maincontent.html", {"maincontent_id": pk})

def admin_home(request):
    return render(request,"admin_home.html")

def edit_topic(request, pk):
    return render(request, "edit_topic.html", {"topic_id": pk})

def module_page(request,module_id):
    return render(request,"module.html",{"module_id": module_id})

def edit_module(request, pk):
    return render(request, "edit_module.html", {"module_id": pk})

def pages_page(request,page_id):
    return render(request,"page.html",{"page_id": page_id})

def quiz_page(request):
    return render(request,"quiz.html")

def user_home(request):
    return render(request,"user_home.html")

def add_quiz(request):
    return render(request,"add_quiz.html")

def edit_quiz(request, question_id):
    return render(request, "edit_quiz.html", {"question_id": question_id})