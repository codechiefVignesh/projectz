from django.db import models
from django.core.validators import MinLengthValidator
from django.contrib.auth.hashers import make_password, check_password

class User(models.Model):
    firstname = models.CharField(max_length=20)
    lastname = models.CharField(max_length=20)
    registration_time = models.DateTimeField(auto_now_add=True)
    email = models.EmailField(max_length=50, unique=True)
    password = models.CharField(max_length=128, validators=[MinLengthValidator(7)])  # stores hashed password

    def set_password(self, raw_password):
        self.password = make_password(raw_password)

    def check_password(self, raw_password):
        return check_password(raw_password, self.password)

    def __str__(self):
        return f"{self.firstname} {self.lastname}"
