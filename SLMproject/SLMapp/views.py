# learning/views.py
from rest_framework import generics, permissions, status
from .serializers import TopicSerializer, QuizSerializer,PageSerializer
from rest_framework.response import Response
from rest_framework.views import APIView
from django.shortcuts import get_object_or_404
from .models import Topic, Module, Page, Progress, Quiz, QuizResult
from .serializers import *
from rest_framework.decorators import action
from django.shortcuts import render
from rest_framework import viewsets, permissions
from .models import Topic, Module, MainContent, Page
from accounts.serializers import *
from rest_framework.exceptions import PermissionDenied


class TopicViewSet(viewsets.ModelViewSet):
    queryset = Topic.objects.all()
    serializer_class = TopicSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        # If the user is an admin, return all topics
        if user.is_superuser:
            return Topic.objects.all().order_by("order")
        # Otherwise, return only the user's topics
        return user.topics.all().order_by("order")


class ModuleViewSet(viewsets.ModelViewSet):
    queryset = Module.objects.all().order_by("order")
    serializer_class = ModuleSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        # If admin, return all modules
        if user.is_superuser:
            return Module.objects.all().order_by("order")
        # Otherwise, return modules related to the user's topics
        user_topic_ids = user.topics.values_list('id', flat=True)
        return Module.objects.filter(topic_id__in=user_topic_ids).order_by("order")



class MainContentViewSet(viewsets.ModelViewSet):
    queryset = MainContent.objects.all().order_by("order")
    serializer_class = MainContentSerializer
    permission_classes = [permissions.IsAuthenticated]


class PageViewSet(viewsets.ModelViewSet):
    serializer_class = PageSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_serializer_class(self):
        if self.action == "list":
            return PageSidebarSerializer
        if self.request.user.is_staff:
            return PageSerializer
        return PageSerializer

    def get_queryset(self):
        queryset = Page.objects.all().order_by("order")

        module_id = self.request.query_params.get("module")
        main_content_id = self.request.query_params.get("main_content")

        if module_id:
            queryset = queryset.filter(main_content__module_id=module_id)

        if main_content_id:
            queryset = queryset.filter(main_content_id=main_content_id)

        return queryset

class AdminPageViewSet(viewsets.ModelViewSet):
    queryset = Page.objects.all().order_by("order")
    serializer_class = PageSerializer
    permission_classes = [permissions.IsAdminUser]

    def get_queryset(self):
        queryset = super().get_queryset()

        module_id = self.request.query_params.get("module")
        main_content_id = self.request.query_params.get("main_content")

        if module_id:
            queryset = queryset.filter(main_content__module_id=module_id)

        if main_content_id:
            queryset = queryset.filter(main_content_id=main_content_id)

        return queryset

# ----------------------------
# Detail Views
# ----------------------------

class TopicListView(generics.ListAPIView):
    serializer_class = TopicListSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        return (
            Topic.objects
            .filter(users=user)
            .prefetch_related("modules")  # 🚀 performance boost
            .order_by("order")
        )


class ModuleDetailView(generics.RetrieveAPIView):
    serializer_class = ModuleSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        # Filter modules based on the user's topics
        user = self.request.user
        return Module.objects.filter(topic__in=user.topics.all())

    def get_object(self):
        # Additional check to ensure the module is accessible
        obj = super().get_object()
        if obj.topic not in self.request.user.topics.all():
            raise PermissionDenied("You do not have access to this module.")
        return obj


class MainContentDetailView(generics.RetrieveAPIView):
    queryset = MainContent.objects.all()
    serializer_class = MainContentSerializer
    permission_classes = [permissions.IsAuthenticated]


class PageDetailView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, page_id):
        page = get_object_or_404(Page, id=page_id)

        # 🔒 Check previous pages
        prev_pages = Page.objects.filter(
            main_content=page.main_content,
            order__lt=page.order
        )

        for prev in prev_pages:
            if not PageProgress.objects.filter(
                user=request.user,
                page=prev,
                completed=True
            ).exists():
                return Response(
                    {"detail": "Please complete previous pages first"},
                    status=403
                )

        serializer = PageSerializer(page, context={'request': request})
        return Response(serializer.data)


class PublicTopicListView(generics.ListAPIView):
    queryset = Topic.objects.all().order_by("order")
    serializer_class = PublicTopicSerializer
    permission_classes = [permissions.AllowAny]
    
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

    # ✅ Add Question
    @action(detail=True, methods=["post"])
    def add_question(self, request, pk=None):
        quiz = self.get_object()
        serializer = QuestionSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(quiz=quiz)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    # ✅ Update Question
    @action(detail=True, methods=["put", "patch"])
    def update_question(self, request, pk=None):
        quiz = self.get_object()
        question_id = request.data.get("question_id")
        if not question_id:
            return Response({"error": "question_id is required"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            question = quiz.questions.get(id=question_id)
        except Question.DoesNotExist:
            return Response({"error": "Question not found in this quiz"}, status=status.HTTP_404_NOT_FOUND)

        serializer = QuestionSerializer(question, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    # ✅ Delete Question
    @action(detail=True, methods=["delete"])
    def delete_question(self, request, pk=None):
        quiz = self.get_object()
        question_id = request.query_params.get("question_id") or request.data.get("question_id")

        if not question_id:
            return Response({"error": "question_id is required"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            question = quiz.questions.get(id=question_id)
        except Question.DoesNotExist:
            return Response({"error": "Question not found in this quiz"}, status=status.HTTP_404_NOT_FOUND)

        question.delete()
        return Response({"message": "Question deleted successfully"}, status=status.HTTP_204_NO_CONTENT)

    # ✅ Filter quizzes by main_content
    def get_queryset(self):
        qs = super().get_queryset()
        main_content = self.request.query_params.get("main_content")
        if main_content:
            qs = qs.filter(main_content_id=main_content)
        return qs

    @action(detail=True, methods=["post"])
    def submit(self, request, pk=None):
        quiz = self.get_object()
        answers = request.data.get("answers", {})  # {question_id: choice_id}
        score = 0
        total_questions = quiz.questions.count()
        results = []

        for q in quiz.questions.all():
            user_choice_id = answers.get(str(q.id))
            correct_choice = q.choices.filter(is_correct=True).first()

            is_correct = str(user_choice_id) == str(correct_choice.id) if user_choice_id and correct_choice else False
            if is_correct:
                score += 1

            results.append({
                "question_id": q.id,
                "question_text": q.text,
                "user_answer": user_choice_id,
                "correct_answer": correct_choice.id if correct_choice else None,
                "is_correct": is_correct,
                "choices": [
                    {"id": c.id, "text": c.text, "is_correct": c.is_correct}
                    for c in q.choices.all()
                ]
            })

        passed = score >= total_questions * 0.6

        # Save result
        QuizResult.objects.create(
            user=request.user,
            quiz=quiz,
            score=score,
            passed=passed,
        )

        return Response({
            "score": score,
            "total": total_questions,
            "percentage": int((score / total_questions) * 100),
            "passed": passed,
            "results": results  # This is the key!
        })



class UserProgressSummary(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        user = request.user
        # Filter modules based on user's topics
        modules = Module.objects.filter(topic__in=user.topics.all())
        total_modules = modules.count()

        completed_modules = 0
        in_progress_modules = 0
        not_started_modules = 0

        for module in modules:
            # Check if module is fully completed
            if Progress.objects.filter(user=user, module=module, completed=True).exists():
                completed_modules += 1
            else:
                # Check if any page inside this module is completed
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
