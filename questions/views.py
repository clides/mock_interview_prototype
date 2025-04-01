from asyncio.queues import Queue
from pickle import PROTO
from django.shortcuts import render, redirect
from django.http import HttpResponseBadRequest, HttpResponse
from django.template import loader
from pypdf import PdfReader
from io import BytesIO
import uuid
import json

from .utils.parse_resume import ResumeParser
from .utils.generate_questions import QuestionGenerator

# Create your views here.
def upload_pdf(request):
    if request.method == 'POST' and request.FILES.get('pdf_file'):
        # Generate unique session ID if doesn't exist
        if 'session_id' not in request.session:
            request.session['session_id'] = str(uuid.uuid4())
        
        # Store PDF content in session (for small files)
        pdf_file = request.FILES['pdf_file']
        pdf_reader = PdfReader(pdf_file)
        text = "\n".join(page.extract_text() for page in pdf_reader.pages)
        
        # Store results in session
        request.session['extracted_text'] = text
        
        resume_parser = ResumeParser(text)
        request.session['experiences'] = resume_parser.extract_information('e')
        request.session['projects'] = resume_parser.extract_information('p')
        
        return redirect('questions')
    
    return render(request, 'upload.html')
    
def questions(request):
    question_generator = QuestionGenerator()
    
    experiences = json.loads(request.session.get('experiences', []))
    projects = json.loads(request.session.get('projects', []))
    
    if not experiences and not projects:
        return render(request, 'questions.html', {
            'error': "No valid experiences or projects found in your resume."
        })
    
    experience_bq = []
    experience_tq = []
    project_bq = []
    project_tq = []
    
    for experience in experiences:
        experience_text = f"(Experience) {experience['title']}: {experience['description']}"
        behavioral_q = question_generator.generate_questions(experience_text + " - Behavioral", 'b')
        technical_q = question_generator.generate_questions(experience_text + " - Technical", 't')
        
        if behavioral_q:
            experience_bq.append(behavioral_q)
        if technical_q:
            experience_tq.append(technical_q)
            
    for project in projects:
        project_text = f"(Project) {project.get('title', '')}: {project.get('description', '')}"
        behavioral_q = question_generator.generate_questions(project_text + " - Behavioral", 'b')
        technical_q = question_generator.generate_questions(project_text + " - Technical", 't')
        
        if behavioral_q:
            project_bq.append(behavioral_q)
        if technical_q:
            project_tq.append(technical_q)
            
    context = {
        'experience_bquestions': experience_bq,
        'experience_tquestions': experience_tq,
        'project_bquestions': project_bq,
        'project_tquestions': project_tq
    }
    
    return render(request, 'questions.html', context)