import google.generativeai as genai
from django.conf import settings

class GeminiService:
    def __init__(self):
        genai.configure(api_key=settings.GEMINI_API_KEY)
        self.model = genai.GenerativeModel('gemini-1.5-flash')
    
    def get_coding_assistance(self, problem_description, current_code, language, assistance_type):
        """
        assistance_type: 'hint', 'debug', 'optimize', 'explain'
        """
        prompts = {
            'hint': f"Give a helpful hint for this coding problem without giving away the full solution:\n\nProblem: {problem_description}\n\nCurrent code: {current_code}\n\nLanguage: {language}",
            'debug': f"Help debug this code for the given problem:\n\nProblem: {problem_description}\n\nCode: {current_code}\n\nLanguage: {language}\n\nWhat might be wrong?",
            'optimize': f"Suggest optimizations for this solution:\n\nProblem: {problem_description}\n\nCode: {current_code}\n\nLanguage: {language}",
            'explain': f"Explain this code solution step by step:\n\nProblem: {problem_description}\n\nCode: {current_code}\n\nLanguage: {language}"
        }
        
        try:
            response = self.model.generate_content(prompts[assistance_type])
            return {
                'success': True,
                'assistance': response.text,
                'type': assistance_type
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }