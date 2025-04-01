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
            if 'session_id' not in request.session:
                request.session['session_id'] = str(uuid.uuid4())
                logger.debug(f"New session created: {request.session['session_id']}")

            # Process PDF file
            pdf_file = request.FILES['pdf_file']
            pdf_reader = PdfReader(pdf_file)
            text = "\n".join(page.extract_text() for page in pdf_reader.pages)
            request.session['extracted_text'] = text

            # Parse resume and store as JSON
            resume_parser = ResumeParser(text)
            experiences = resume_parser.extract_information('e') or []
            projects = resume_parser.extract_information('p') or []
            
            request.session['experiences'] = json.dumps(experiences)
            request.session['projects'] = json.dumps(projects)
            
            logger.info("Successfully processed resume")
            return redirect('questions')

        except Exception as e:
            logger.error(f"Error processing PDF: {str(e)}")
            return render(request, 'upload.html', {
                'error': f"Error processing your resume: {str(e)}"
            })

    return render(request, 'upload.html')

def questions(request):
    try:
        # Safely load session data
        experiences = []
        projects = []
        
        try:
            experiences = json.loads(request.session.get('experiences', '[]'))
            projects = json.loads(request.session.get('projects', '[]'))
        except json.JSONDecodeError as e:
            logger.error(f"Invalid session data: {str(e)}")
            return render(request, 'questions.html', {
                'error': "Invalid session data. Please upload your resume again."
            })

        if not experiences and not projects:
            return render(request, 'questions.html', {
                'error': "No valid experiences or projects found in your resume."
            })

        # Initialize question generator
        question_generator = QuestionGenerator()
        experience_bq = []
        experience_tq = []
        project_bq = []
        project_tq = []

        # Generate questions with timeout protection
        try:
            for experience in experiences:
                if not isinstance(experience, dict):
                    continue
                    
                exp_text = f"(Experience) {experience.get('title', '')}: {experience.get('description', '')}"
                
                behavioral_q = question_generator.generate_questions(f"{exp_text} - Behavioral", 'b')
                if behavioral_q:
                    experience_bq.append(behavioral_q)
                
                technical_q = question_generator.generate_questions(f"{exp_text} - Technical", 't')
                if technical_q:
                    experience_tq.append(technical_q)

            for project in projects:
                if not isinstance(project, dict):
                    continue
                    
                proj_text = f"(Project) {project.get('title', '')}: {project.get('description', '')}"
                
                behavioral_q = question_generator.generate_questions(f"{proj_text} - Behavioral", 'b')
                if behavioral_q:
                    project_bq.append(behavioral_q)
                
                technical_q = question_generator.generate_questions(f"{proj_text} - Technical", 't')
                if technical_q:
                    project_tq.append(technical_q)

        except Exception as e:
            logger.error(f"Error generating questions: {str(e)}")
            return render(request, 'questions.html', {
                'error': f"Error generating questions: {str(e)}"
            })

        context = {
            'experience_bquestions': experience_bq,
            'experience_tquestions': experience_tq,
            'project_bquestions': project_bq,
            'project_tquestions': project_tq
        }

        return render(request, 'questions.html', context)

    except Exception as e:
        logger.critical(f"Unexpected error in questions view: {str(e)}")
        return render(request, 'questions.html', {
            'error': "An unexpected error occurred. Please try again."
        })