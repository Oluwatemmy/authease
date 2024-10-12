from django.urls import path
from .views import GoogleSignInView, GithubSignInView


urlpatterns = [
    path('google/', GoogleSignInView.as_view(), name='google-sign-in'),
    path('github/', GithubSignInView.as_view(), name='github-sign-in'),
]
