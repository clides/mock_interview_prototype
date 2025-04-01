import os
import requests
import json
from dotenv import load_dotenv

TYPE = {
    "b": """You are a hiring manager trained to come up with behavioural interview questions. Based on the information below, generate only a behavioral interview question. Do not add additional formatting.
    
Information:""",
    "t": """You are a hiring manager trained to come up with technical interview questions. Based on the information below, generate only a technical interview question. Do not add additional formatting.
    
Information:"""
}

class QuestionGenerator():
    def __init__(self):
        load_dotenv()
        
        self.OPENROUTER_API_KEY = os.getenv("OPENROUTER")
        self.OPENROUTER_API_URL = "https://openrouter.ai/api/v1/chat/completions"
        
    def generate_questions(self, section_text, question_type):
        headers = {
            "Authorization": f"Bearer {self.OPENROUTER_API_KEY}",
            "Content-Type": "application/json"
        }
        
        question = str(TYPE.get(question_type))
        prompt = question + '\n' + section_text
        
        payload = {
            "model": "deepseek/deepseek-chat:free",  # Specify DeepSeek-V3
            "messages": [
                {"role": "user", "content": prompt}
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