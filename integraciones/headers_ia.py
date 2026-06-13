#integration/headers_ia.py
"""
Configuración de headers y URLs para diferentes proveedores de IA
Basado en: https://integracion-de-apis-de-ia-de-cero-a-experto.cesarcancino.com/
"""
import os
from dotenv import load_dotenv
from typing import Optional
load_dotenv()


class IAProviders:
    """Clase estática con configuraciones de cada proveedor"""
    
    @staticmethod
    def get_mistral_headers():
        """Headers para Mistral AI"""
        return {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {os.getenv('MISTRAL_API_KEY')}"
        }
    
    @staticmethod
    def get_gemini_headers():
        """Headers para Google Gemini"""
        return {
            "Content-Type": "application/json",
            "x-goog-api-key": os.getenv('GEMINI_API_KEY')
        }
    
    @staticmethod
    def get_claude_headers():
        """Headers para Anthropic Claude"""
        return {
            "Content-Type": "application/json",
            "x-api-key": os.getenv('CLAUDE_API_KEY'),
            "anthropic-version": "2023-06-01"
        }
    
    @staticmethod
    def get_openai_headers():
        """Headers para OpenAI"""
        return {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {os.getenv('OPENAI_API_KEY')}"
        }
    
    @staticmethod
    def get_deepseek_headers():
        """Headers para DeepSeek"""
        return {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {os.getenv('DEEPSEEK_API_KEY')}"
        }


class IAEndpoints:
    """URLs base y endpoints de cada proveedor"""
    
    MISTRAL_BASE = os.getenv('MISTRAL_BASE_URL', 'https://api.mistral.ai/v1/')
    GEMINI_BASE = os.getenv('GEMINI_BASE_URL', 'https://generativelanguage.googleapis.com/v1beta')
    CLAUDE_BASE = os.getenv('CLAUDE_BASE_URL', 'https://api.anthropic.com/v1/')
    OPENAI_BASE = os.getenv('OPENAI_BASE_URL', 'https://api.openai.com/v1/')
    DEEPSEEK_BASE = os.getenv('DEEPSEEK_API_URL', 'https://api.deepseek.com/v1/')
    
    @staticmethod
    def get_chat_endpoint(provider: str, model: Optional[str] = None) -> str:
        """Retorna el endpoint de chat según el proveedor"""
        if provider.lower() == 'gemini':
            # ✅ Gemini 3.5-flash como default, modelo dinámico
            model_name = model or "gemini-3.5-flash"
            base_url = IAEndpoints.GEMINI_BASE.rstrip('/')
            return f"{base_url}/models/{model_name}:generateContent"
        
        endpoints = {
            'mistral': f"{IAEndpoints.MISTRAL_BASE}chat/completions",
            'claude': f"{IAEndpoints.CLAUDE_BASE}messages",
            'openai': f"{IAEndpoints.OPENAI_BASE}chat/completions",
            'deepseek': f"{IAEndpoints.DEEPSEEK_BASE}chat/completions",
        }
        return endpoints.get(provider.lower(), endpoints['mistral'])
