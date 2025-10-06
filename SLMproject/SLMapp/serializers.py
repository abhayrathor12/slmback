# learning/serializers.py
from rest_framework import serializers
from .models import *


class PageMiniSerializer(serializers.ModelSerializer):
    """ Lightweight serializer for listing pages (used inside MainContent) """
    completed = serializers.SerializerMethodField()

    class Meta:
        model = Page
        fields = ["id", "order", "completed","title"]

    def get_completed(self, obj):
        user = self.context["request"].user
        return PageProgress.objects.filter(user=user, page=obj, completed=True).exists()


class PageSerializer(serializers.ModelSerializer):
    main_content = serializers.SerializerMethodField()
    completed = serializers.SerializerMethodField()

    class Meta:
        model = Page
        fields = '__all__'

    def get_main_content(self, obj):
        return MainContentSerializer(obj.main_content, context=self.context).data

    def get_completed(self, obj):
        user = self.context["request"].user
        return PageProgress.objects.filter(user=user, page=obj, completed=True).exists()

    def create(self, validated_data):
        # main_content comes from request.data, not validated_data
        main_content_id = self.context['request'].data.get("main_content")
        validated_data["main_content_id"] = main_content_id
        return super().create(validated_data)

    def update(self, instance, validated_data):
        main_content_id = self.context['request'].data.get("main_content")
        if main_content_id:
            validated_data["main_content_id"] = main_content_id
        return super().update(instance, validated_data)



class MainContentSerializer(serializers.ModelSerializer):
    pages = serializers.SerializerMethodField()
    completed = serializers.SerializerMethodField()
    locked = serializers.SerializerMethodField()
    quiz = serializers.SerializerMethodField()  # <-- add this
    

    class Meta:
        model = MainContent
        fields = '__all__'

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


class ModuleSerializer(serializers.ModelSerializer):
    main_contents = MainContentSerializer(many=True, read_only=True)
    completed = serializers.SerializerMethodField()
    locked = serializers.SerializerMethodField()
    completion_percentage = serializers.SerializerMethodField()

    class Meta:
        model = Module
        fields = [
            "id",
            "title",
            "description",
            "order",
            "completed",
            "locked",
            "main_contents",
            "topic",
             "completion_percentage",
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


class TopicSerializer(serializers.ModelSerializer):
    modules = ModuleSerializer(many=True, read_only=True)
    completed = serializers.SerializerMethodField()

    class Meta:
        model = Topic
        fields = ["id", "name", "order", "modules", "completed"]

    def get_completed(self, obj):
        user = self.context["request"].user
        for module in obj.modules.all():
            if not Progress.objects.filter(user=user, module=module, completed=True).exists():
                return False
        return True
    
    


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

class QuizSerializer(serializers.ModelSerializer):
    questions = QuestionSerializer(many=True, required=False)

    class Meta:
        model = Quiz
        fields = ["id", "title", "questions", "main_content"]
