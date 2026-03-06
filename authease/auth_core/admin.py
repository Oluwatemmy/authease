from django.contrib import admin
from django.contrib.admin.sites import AlreadyRegistered
from django.contrib.auth import get_user_model

try:
    admin.site.register(get_user_model())
except AlreadyRegistered:
    pass