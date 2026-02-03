from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models

class UserManager(BaseUserManager):
    def create_user(self, login_id, password=None, **extra_fields):
        if not login_id:
            raise ValueError("login_id is required")

        user = self.model(login_id=login_id, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, login_id, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        return self.create_user(login_id, password, **extra_fields)

class User(AbstractUser):
    username = None

    login_id = models.EmailField(unique=True)
    nickname = models.CharField(max_length=20)
    profile_image = models.URLField(blank=True)
    height = models.IntegerField()
    weight = models.IntegerField()

    class Gender(models.TextChoices):
        MALE = "MALE", "남성"
        FEMALE = "FEMALE", "여성"

    gender = models.CharField(
        max_length=10,
        choices=Gender.choices
    )

    USERNAME_FIELD = "login_id"
    REQUIRED_FIELDS = []

    objects=UserManager()

class Style(models.Model):
    name = models.CharField(max_length=20, unique=True)

    def __str__(self):
        return self.name
    
class UserStyle(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="user_s
    style = models.ForeignKey(
        Style,
        on_delete=models.CASCADE
    )

    class Meta:
        unique_together = ("user", "style")

class Address(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="addresses"
    )
    receiver = models.CharField(max_length=50)
    phone = models.CharField(max_length=20)
    address = models.TextField()
    is_default = models.BooleanField(default=False)

