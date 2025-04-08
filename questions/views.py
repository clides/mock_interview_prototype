import uuid
import json
import logging
from django.shortcuts import render, redirect
from django.http import HttpResponseBadRequest
from pypdf import PdfReader
from .utils.parse_resume import ResumeParser
from .utils.generate_questions import QuestionGenerator

logger = logging.getLogger(__name__)

def upload_pdf(request):
    if request.method == 'POST' and request.FILES.get('pdf_file'):
        try:
            # Initialize session
            request.session.setdefault('session_id', str(uuid.uuid4()))
            logger.debug(f"Session ID: {request.session['session_id']}")

            # Process PDF
            pdf_file = request.FILES['pdf_file']
            text = "\n".join(page.extract_text() for page in PdfReader(pdf_file).pages)
            request.session['extracted_text'] = text

            # Parse resume and validate format
            resume_parser = ResumeParser(text)
            raw_experiences = resume_parser.extract_information('e')
            raw_projects = resume_parser.extract_information('p')
            # print("Raw experiences:", raw_experiences)  # Debug the invalid JSON
            # print("Raw projects:", raw_projects)  # Debug the invalid JSON
            
            experiences = json.loads(raw_experiences) if raw_experiences else []
            projects = json.loads(raw_projects) if raw_projects else []

            # Store validated data
            request.session['experiences'] = experiences
            request.session['projects'] = projects
            
            return redirect('questions')

        except Exception as e:
            logger.error(f"Upload error: {str(e)}", exc_info=True)
            return render(request, 'upload.html', {
                'error': f"Failed to process resume. Please try again."
            })

    return render(request, 'upload.html')

def questions(request):
    try:
        experiences = request.session.get('experiences', [])
        projects = request.session.get('projects', [])

        if not experiences and not projects:
            logger.warning("No valid experiences or projects found")
            # Redirect to upload page using the URL pattern name
            return redirect('upload')  # Changed from 'upload_pdf' to match your urls.py

        # Generate questions safely
        question_generator = QuestionGenerator()
        results = {
            'experience_bquestions': [],
            'experience_tquestions': [],
            'project_bquestions': [],
            'project_tquestions': []
        }

        def generate_safe_questions(text):
            try:
                result = question_generator.make_prediction(text)
                return str(result) if result else ""
            except Exception as e:
                logger.error(f"Question generation failed: {str(e)}")
                return ""

        # Process experiences
        for exp in experiences:
            exp_text = f"(Experience) {exp['title']}: {exp['description']}"
            if bq := generate_safe_questions(f"{exp_text} - Behavioral"):
                results['experience_bquestions'].append(bq)
            if tq := generate_safe_questions(f"{exp_text} - Technical"):
                results['experience_tquestions'].append(tq)

        # Process projects
        for proj in projects:
            proj_text = f"(Project) {proj['title']}: {proj['description']}"
            if bq := generate_safe_questions(f"{proj_text} - Behavioral"):
                results['project_bquestions'].append(bq)
            if tq := generate_safe_questions(f"{proj_text} - Technical"):
                results['project_tquestions'].append(tq)

        return render(request, 'questions.html', results)

    except Exception as e:
        logger.critical(f"Questions view error: {str(e)}", exc_info=True)
        # Fallback to upload page if error template doesn't exist
        return redirect('upload')