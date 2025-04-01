import os
import requests
import json
from pypdf import PdfReader
from dotenv import load_dotenv

# Define the prompt for resume parsing
PROMPTS = {
    "b": """You are a hiring manager trained to extract relevant information from a resume. You are to only include relevant details, do not make up any information. Look at the following resume text and extract the First name, Last name, University, Majors.
Resume text:""",
    
    "e": """You are a hiring manager trained to extract relevant information from a resume. You are to only include relevant details, do not make up any information, and do not add additional markdown formatting. Look at the following resume text and extract each experience. For each experience, extract the following details: job title, description. Do not add additional formatting. If there are no experiences, return an empty list.

Return the extracted information as a valid JSON object with exactly the following structure:
[
    {
        "title": "<job title>",
        "description": "<description>"
    },
    ...
]

Resume text:""",
    
    "s": """You are a hiring manager extracting technical skills from a resume. Extract ONLY the existing skills, do not make up or create any information.
Return the skills in a list format.
Resume text:""",
    
    "p": """You are a hiring manager trained to extract relevant information from a resume. You are to only include relevant details, do not make up any information, and do not add additional markdown formatting. Look at the following resume text and extract each project. For each project, extract the following details: project name, description. Do not add additional formatting. If there are no projects, return an empty list.

Return the extracted information as a valid JSON object with the following structure:
[
    {
        "title": "<project name>",
        "description": "<description>"
    },
    ...
]

Resume text:""",
}


class ResumeParser():
  def __init__(self, resume_text):
    load_dotenv()
    
    self.resume_text = resume_text
    self.OPENROUTER_API_KEY = os.getenv("OPENROUTER")
    self.OPENROUTER_API_URL = "https://openrouter.ai/api/v1/chat/completions"
  
  def extract_information(self, prompt_key):
    headers = {
      "Authorization": f"Bearer {self.OPENROUTER_API_KEY}",
      "Content-Type": "application/json"
    }
    
    prompt = str(PROMPTS.get(prompt_key))
    full_prompt = prompt + '\n' + self.resume_text
    
    payload = {
      "model": "deepseek/deepseek-chat:free",  # Specify DeepSeek-V3
      "messages": [
        {"role": "user", "content": full_prompt}
      ],
      "temperature": 0.1,  # Lower temperature for more deterministic output
    }

    # Send the request to OpenRouter
    response = requests.post(self.OPENROUTER_API_URL, headers=headers, json=payload)
    
    # Check if the request was successful
    if response.status_code == 200:
      # Extract the generated text from the response
      generated_text = response.json()["choices"][0]["message"]["content"]
      
      return generated_text
    else:
      print("Error:", response.status_code, response.text)