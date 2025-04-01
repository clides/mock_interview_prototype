from django.urls import path
from . import views
from questions.views import upload_pdf

urlpatterns = [
    path('upload/', views.upload_pdf, name='upload'),
    path('questions/', views.questions, name='questions'),
    
    path('', upload_pdf, name='root_upload'),
]