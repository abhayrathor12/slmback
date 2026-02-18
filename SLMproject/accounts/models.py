from django.contrib.auth.models import AbstractUser
from django.db import models

class CustomUser(AbstractUser):

    username = None  # ❌ remove username completely

    ROLE_CHOICES = (
        ("student", "Student"),
        ("professional", "Professional"),
        ("admin", "Admin"),
    )

    email = models.EmailField(unique=True)  # ✅ login field
    
    role = models.CharField(max_length=20, choices=ROLE_CHOICES)
    phone = models.CharField(max_length=15, null=True, blank=True)

    dob = models.DateField(blank=True, null=True)

    is_active = models.BooleanField(default=False)

    USERNAME_FIELD = "email"   # ✅ login with email
    REQUIRED_FIELDS = []
    
    topics = models.ManyToManyField(
    "SLMapp.Topic",
    blank=True,
    related_name="users"
)

    def __str__(self):
        return f"{self.email} ({self.role})"

class StudentProfile(models.Model):
    user = models.OneToOneField(
        CustomUser,
        on_delete=models.CASCADE,
        related_name="student_profile"
    )
    passing_year = models.CharField(
    max_length=10,
    blank=True,
    null=True   # ✅ ADD THIS
)
    current_year = models.CharField(max_length=20)
    stream = models.CharField(max_length=100)
    interest = models.CharField(max_length=50)
    city = models.CharField(max_length=100,blank=True, null=True)
    def __str__(self):
        return f"Student Profile - {self.user.username}"

class ProfessionalProfile(models.Model):
    user = models.OneToOneField(
        CustomUser,
        on_delete=models.CASCADE,
        related_name="professional_profile"
    )
    interest = models.CharField(
        max_length=50,
        blank=True,
        null=True   # ✅ ADD THIS
    )
    company = models.CharField(max_length=255)
    city = models.CharField(max_length=100)
    company_email = models.EmailField(blank=True, null=True)

    def __str__(self):
        return f"Professional Profile - {self.user.email}"