# learning/serializers.py
from rest_framework import serializers
from .models import *
import hashlib
import time
from django.conf import settings
from rest_framework import serializers
from django.db import transaction

class PageMiniSerializer(serializers.ModelSerializer):
    completed = serializers.SerializerMethodField()
    formatted_duration = serializers.SerializerMethodField()
    locked = serializers.SerializerMethodField()   # ✅ ADD THIS

    class Meta:
        model = Page
        fields = ["id", "order", "completed", "title", "formatted_duration", "locked"]

    def get_completed(self, obj):
        user = self.context["request"].user
        return PageProgress.objects.filter(
            user=user, page=obj, completed=True
        ).exists()

    def get_locked(self, obj):
        user = self.context["request"].user

        # First page is never locked
        if obj.order == 1:
            return False

        # Get previous page
        prev_page = Page.objects.filter(
            main_content=obj.main_content,
            order=obj.order - 1
        ).first()

        if not prev_page:
            return True

        return not PageProgress.objects.filter(
            user=user,
            page=prev_page,
            completed=True
        ).exists()

    def get_formatted_duration(self, obj):
        return format_duration(obj.time_duration)


class PageSerializer(serializers.ModelSerializer):
    main_content = serializers.SerializerMethodField()
    completed = serializers.SerializerMethodField()
    formatted_duration = serializers.SerializerMethodField()
    video_url = serializers.SerializerMethodField()
    
    class Meta:
        model = Page
        fields = "__all__"

    # -------------------------
    # SERIALIZER FIELDS
    # -------------------------

    def get_main_content(self, obj):
        return MainContentSerializer(obj.main_content, context=self.context).data

    def get_completed(self, obj):
        user = self.context["request"].user
        return PageProgress.objects.filter(
            user=user,
            page=obj,
            completed=True
        ).exists()

    def get_formatted_duration(self, obj):
        return format_duration(obj.time_duration)

    def get_video_url(self, obj):
        if not obj.video_id:
            return None

        LIBRARY_ID = settings.BUNNY_LIBRARY_ID
        TOKEN_KEY = settings.BUNNY_TOKEN_KEY

        expires = int(time.time()) + 60
        raw = f"{TOKEN_KEY}{obj.video_id}{expires}"
        token = hashlib.sha256(raw.encode("utf-8")).hexdigest()

        return (
            f"https://iframe.mediadelivery.net/embed/"
            f"{LIBRARY_ID}/{obj.video_id}"
            f"?token={token}&expires={expires}"
             f"&playerjs=1"
        )

    # -------------------------
    # CREATE WITH ORDER SHIFT
    # -------------------------

    @transaction.atomic
    def create(self, validated_data):
        request = self.context["request"]

        main_content_id = request.data.get("main_content")
        new_order = int(request.data.get("order", 0))

        # Shift existing pages forward
        Page.objects.filter(
            main_content_id=main_content_id,
            order__gte=new_order
        ).update(order=F("order") + 1)

        validated_data["main_content_id"] = main_content_id
        validated_data["order"] = new_order

        return super().create(validated_data)

    # -------------------------
    # UPDATE WITH SMART REORDER
    # -------------------------

    @transaction.atomic
    def update(self, instance, validated_data):
        request = self.context["request"]

        new_order = int(request.data.get("order", instance.order))
        old_order = instance.order
        main_content_id = instance.main_content_id

        if new_order != old_order:

            if new_order > old_order:
                # Moving DOWN → shift others UP
                Page.objects.filter(
                    main_content_id=main_content_id,
                    order__gt=old_order,
                    order__lte=new_order
                ).update(order=F("order") - 1)

            else:
                # Moving UP → shift others DOWN
                Page.objects.filter(
                    main_content_id=main_content_id,
                    order__gte=new_order,
                    order__lt=old_order
                ).update(order=F("order") + 1)

        validated_data["order"] = new_order
        return super().update(instance, validated_data)

class MainContentSerializer(serializers.ModelSerializer):
    pages = serializers.SerializerMethodField()
    completed = serializers.SerializerMethodField()
    locked = serializers.SerializerMethodField()
    quiz = serializers.SerializerMethodField()
    total_duration = serializers.SerializerMethodField()
    formatted_duration = serializers.SerializerMethodField()
    module = serializers.PrimaryKeyRelatedField(queryset=Module.objects.all())  # for write
    module_detail = serializers.SerializerMethodField()  # for read

    class Meta:
        model = MainContent
        fields = '__all__'
        # OR if you want to keep both:
        # fields = [ ..., 'module', 'module_detail', ...]

    def get_pages(self, obj):
        qs = obj.pages.all().order_by("order")
        return PageMiniSerializer(qs, many=True, context=self.context).data
    
    def get_quiz(self, obj):
        return hasattr(obj, "quiz") and obj.quiz is not None
    
    def get_completed(self, obj):
        user = self.context["request"].user
        return MainContentProgress.objects.filter(user=user, main_content=obj, completed=True).exists()
    
    def get_completion_percentage(self, obj):
        user = self.context["request"].user
        total = obj.pages.count()
        if total == 0:
            return 0
        completed = PageProgress.objects.filter(
            user=user, page__main_content=obj, completed=True
        ).count()
        return round((completed / total) * 100)
    
    def get_locked(self, obj):
        user = self.context["request"].user
        if obj.order == 1:
            return False
        prev = MainContent.objects.filter(module=obj.module, order=obj.order - 1).first()
        if prev:
            return not MainContentProgress.objects.filter(
                user=user, main_content=prev, completed=True
            ).exists()
        return True
    
    def get_total_duration(self, obj):
        return obj.total_duration

    def get_formatted_duration(self, obj):
        return obj.formatted_duration
    
    def get_module_detail(self, obj):
        return {
            "id": obj.module.id,
            "title": obj.module.title
        }

class MainContentListSerializer(serializers.ModelSerializer):
    module_detail = serializers.SerializerMethodField()

    class Meta:
        model = MainContent
        fields = ["id", "title", "description", "order", "module", "module_detail"]

    def get_module_detail(self, obj):
        return {
            "id": obj.module.id,
            "title": obj.module.title
        }

class ModuleSerializer(serializers.ModelSerializer):
    main_contents = MainContentSerializer(many=True, read_only=True)
    completed = serializers.SerializerMethodField()
    locked = serializers.SerializerMethodField()
    has_quiz = serializers.SerializerMethodField()   # ✅ ADD THIS
    completion_percentage = serializers.SerializerMethodField()
    total_duration = serializers.SerializerMethodField()         
    formatted_duration = serializers.SerializerMethodField() 
    difficulty_level = serializers.CharField(read_only=False, required=False)
    

    class Meta:
        model = Module
        fields = [
            "id",
            "title",
            "description",
            "order",
            "difficulty_level",  
            "completed",
            "locked",
            "main_contents",
            "topic",
            "completion_percentage",
            "total_duration",
            "formatted_duration",
            "has_quiz"
        ]

    def get_completed(self, obj):
        user = self.context["request"].user
        return Progress.objects.filter(user=user, module=obj, completed=True).exists()

    
    def get_locked(self, obj):
        user = self.context["request"].user
        if obj.order == 1:
            return False
        prev = Module.objects.filter(topic=obj.topic, order=obj.order - 1).first()
        if prev:
            return not Progress.objects.filter(
                user=user, module=prev, completed=True
            ).exists()
        return True

    def get_completion_percentage(self, obj):
        """
        Calculate module completion based on total pages in all main_contents.
        """
        user = self.context["request"].user
        main_contents = obj.main_contents.all()

        total_pages = 0
        completed_pages = 0

        for mc in main_contents:
            total_pages += mc.pages.count()
            completed_pages += PageProgress.objects.filter(
                user=user, page__main_content=mc, completed=True
            ).count()

        if total_pages == 0:
            return 0

        return round((completed_pages / total_pages) * 100, 2)
    
    def get_total_duration(self, obj):
        return obj.total_duration

    def get_formatted_duration(self, obj):
        return obj.formatted_duration
    
    def get_has_quiz(self, obj):   # ✅ ADD THIS
        return hasattr(obj, "quiz") and obj.quiz is not None



class TopicSerializer(serializers.ModelSerializer):
    modules = ModuleSerializer(many=True, read_only=True)
    completed = serializers.SerializerMethodField()
    total_duration = serializers.SerializerMethodField()   
    formatted_duration = serializers.SerializerMethodField()

    class Meta:
        model = Topic
        fields = ["id", "name", "order", "modules","prize", "completed",  "total_duration",
            "formatted_duration",]

    def get_completed(self, obj):
        user = self.context["request"].user
        for module in obj.modules.all():
            if not Progress.objects.filter(user=user, module=module, completed=True).exists():
                return False
        return True
    
        # ✅ Duration methods
    def get_total_duration(self, obj):
        """Sum of durations of all modules in this topic."""
        return sum(module.total_duration for module in obj.modules.all())

    def get_formatted_duration(self, obj):
        """Human-readable duration, e.g., '2 hr 15 min'."""
        total_minutes = self.get_total_duration(obj)
        return format_duration(total_minutes)
    
class PublicTopicSerializer(serializers.ModelSerializer):
    class Meta:
        model = Topic
        fields = ["id", "name","prize"]


class ChoiceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Choice
        fields = ["id", "text", "is_correct"]

class QuestionSerializer(serializers.ModelSerializer):
    choices = ChoiceSerializer(many=True)

    class Meta:
        model = Question
        fields = ["id", "text", "choices"]

    def create(self, validated_data):
        choices_data = validated_data.pop("choices")
        question = Question.objects.create(**validated_data)
        for choice_data in choices_data:
            Choice.objects.create(question=question, **choice_data)
        return question

    def update(self, instance, validated_data):
        # Extract nested choice data
        choices_data = validated_data.pop("choices", [])
        instance.text = validated_data.get("text", instance.text)
        instance.save()

        # Update choices
        existing_choices = list(instance.choices.all())

        for i, choice_data in enumerate(choices_data):
            if i < len(existing_choices):
                # Update existing choice
                choice = existing_choices[i]
                choice.text = choice_data.get("text", choice.text)
                choice.is_correct = choice_data.get("is_correct", choice.is_correct)
                choice.save()
            else:
                # Create new choice if extra provided
                Choice.objects.create(question=instance, **choice_data)

        # If fewer choices sent, delete extras
        if len(choices_data) < len(existing_choices):
            for extra_choice in existing_choices[len(choices_data):]:
                extra_choice.delete()

        return instance


class QuizSerializer(serializers.ModelSerializer):
    questions = QuestionSerializer(many=True, required=False)

    class Meta:
        model = Quiz
        fields = ["id", "title", "questions", "main_content"]

class ModuleListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Module
        fields = [
            "id",
            "title",
            "description",
            "difficulty_level",
            "order",
            "formatted_duration",
            "completion_percentage",
        ]

class TopicListSerializer(serializers.ModelSerializer):
    modules = ModuleListSerializer(many=True)

    class Meta:
        model = Topic
        fields = [
            "id",
            "name",
            "order",
            "modules",
        ]
        
class PageSidebarSerializer(serializers.ModelSerializer):
    completed = serializers.SerializerMethodField()
    formatted_duration = serializers.SerializerMethodField()

    class Meta:
        model = Page
        fields = [
            "id",
            "title",
            "order",
            "completed",
            "formatted_duration",
        ]

    def get_completed(self, obj):
        user = self.context["request"].user
        return PageProgress.objects.filter(
            user=user,
            page=obj,
            completed=True
        ).exists()

    def get_formatted_duration(self, obj):
        return format_duration(obj.time_duration)



class TopicAdminListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Topic
        fields = ["id", "name", "order", "prize"]

class AdminModuleListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Module
        fields = [
            "id",
            "title",
            "description",
            "difficulty_level",
            "order",
            "topic",
        ]
        
class AdminPageListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Page
        fields = [
            "id",
            "title",
            "content",
            "order",
            "time_duration",
            "main_content",
            "video_id",
        ]
