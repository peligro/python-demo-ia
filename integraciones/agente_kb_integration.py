"""
Servicio de integración con APIs de IA para el Agente KB
Centraliza las llamadas a diferentes proveedores
"""
import requests
import os
from typing import Optional, Dict, Any, List
from .headers_ia import IAProviders, IAEndpoints


class AgenteKBIntegration:
    """
    Cliente unificado para llamar a diferentes proveedores de IA
    desde el Agente KB
    """
    
    @staticmethod
    def chat_mistral(
        prompt: str,
        model: str = "mistral-small-latest",
        temperature: float = 0.3,
        max_tokens: int = 1000,
        messages: Optional[List[Dict[str, str]]] = None  # ✅ NUEVO: historial opcional
    ) -> Dict[str, Any]:
        """
        Consulta a Mistral AI
        Retorna: {"response": str, "usage": {"input": int, "output": int, "total": int}}
        """
        try:
            # ✅ Si viene messages, usarlo; si no, construir con prompt
            if messages:
                payload = {
                    "model": model,
                    "messages": messages,
                    "temperature": temperature,
                    "max_tokens": max_tokens
                }
            else:
                payload = {
                    "model": model,
                    "messages": [{"role": "user", "content": prompt}],
                    "temperature": temperature,
                    "max_tokens": max_tokens
                }
            
            response = requests.post(
                IAEndpoints.get_chat_endpoint('mistral'),
                headers=IAProviders.get_mistral_headers(),
                json=payload,
                timeout=30
            )
            response.raise_for_status()
            data = response.json()
            
            return {
                "response": data["choices"][0]["message"]["content"],
                "usage": {
                    "input": data["usage"]["prompt_tokens"],
                    "output": data["usage"]["completion_tokens"],
                    "total": data["usage"]["total_tokens"]
                }
            }
        except Exception as e:
            raise Exception(f"Error en Mistral: {str(e)}")
    
    @staticmethod
    def chat_gemini(
        prompt: str,
        model: str = "gemini-3.5-flash",
        temperature: float = 0.3,
        max_tokens: int = 1000,
        messages: Optional[List[Dict[str, str]]] = None  # ✅ NUEVO
    ) -> Dict[str, Any]:
        """
        Consulta a Google Gemini 3.5-flash
        """
        try:
            # ✅ Gemini usa contents en lugar de messages
            if messages:
                # Convertir formato de messages a contents
                contents = []
                for msg in messages:
                    contents.append({
                        "role": "user" if msg["role"] == "user" else "model",
                        "parts": [{"text": msg["content"]}]
                    })
            else:
                contents = [{
                    "role": "user",
                    "parts": [{"text": prompt}]
                }]
            
            payload = {
                "contents": contents,
                "generationConfig": {
                    "temperature": temperature,
                    "maxOutputTokens": max_tokens
                }
            }
            
            base_url = IAEndpoints.GEMINI_BASE.rstrip('/')
            url = f"{base_url}/models/{model}:generateContent"
            
            response = requests.post(
                url,
                headers=IAProviders.get_gemini_headers(),
                json=payload,
                timeout=30
            )
            response.raise_for_status()
            data = response.json()
            
            usage = {"input": 0, "output": 0, "total": 0}
            if "usageMetadata" in data:
                usage = {
                    "input": data["usageMetadata"].get("promptTokenCount", 0),
                    "output": data["usageMetadata"].get("candidatesTokenCount", 0),
                    "total": data["usageMetadata"].get("totalTokenCount", 0)
                }
            
            return {
                "response": data["candidates"][0]["content"]["parts"][0]["text"],
                "usage": usage
            }
        except Exception as e:
            raise Exception(f"Error en Gemini: {str(e)}")
    
    @staticmethod
    def chat_claude(
        prompt: str,
        model: str = None,
        max_tokens: int = 1000,
        messages: Optional[List[Dict[str, str]]] = None  # ✅ NUEVO
    ) -> Dict[str, Any]:
        """
        Consulta a Anthropic Claude
        """
        if model is None:
            model = os.getenv('CLAUDE_MODEL', 'claude-opus-4-8')
        
        try:
            # ✅ Si viene messages, usarlo; si no, construir con prompt
            if messages:
                payload = {
                    "model": model,
                    "max_tokens": max_tokens,
                    "messages": messages
                }
            else:
                payload = {
                    "model": model,
                    "max_tokens": max_tokens,
                    "messages": [{"role": "user", "content": prompt}]
                }
            
            response = requests.post(
                IAEndpoints.get_chat_endpoint('claude'),
                headers=IAProviders.get_claude_headers(),
                json=payload,
                timeout=30
            )
            response.raise_for_status()
            data = response.json()
            
            return {
                "response": data["content"][0]["text"],
                "usage": {
                    "input": data["usage"]["input_tokens"],
                    "output": data["usage"]["output_tokens"],
                    "total": data["usage"]["input_tokens"] + data["usage"]["output_tokens"]
                }
            }
        except Exception as e:
            print(f"[Claude] Status: {e.response.status_code if hasattr(e, 'response') else 'N/A'}")
            print(f"[Claude] Response: {e.response.text if hasattr(e, 'response') else str(e)}")
            raise Exception(f"Error en Claude: {str(e)}")
    
    @staticmethod
    def chat_openai(
        prompt: str,
        model: str = "gpt-4o-mini",
        temperature: float = 0.3,
        max_tokens: int = 1000,
        messages: Optional[List[Dict[str, str]]] = None  # ✅ NUEVO
    ) -> Dict[str, Any]:
        """
        Consulta a OpenAI
        """
        try:
            if messages:
                payload = {
                    "model": model,
                    "messages": messages,
                    "temperature": temperature,
                    "max_tokens": max_tokens
                }
            else:
                payload = {
                    "model": model,
                    "messages": [{"role": "user", "content": prompt}],
                    "temperature": temperature,
                    "max_tokens": max_tokens
                }
            
            response = requests.post(
                IAEndpoints.get_chat_endpoint('openai'),
                headers=IAProviders.get_openai_headers(),
                json=payload,
                timeout=30
            )
            response.raise_for_status()
            data = response.json()
            
            return {
                "response": data["choices"][0]["message"]["content"],
                "usage": {
                    "input": data["usage"]["prompt_tokens"],
                    "output": data["usage"]["completion_tokens"],
                    "total": data["usage"]["total_tokens"]
                }
            }
        except Exception as e:
            raise Exception(f"Error en OpenAI: {str(e)}")
    
    @staticmethod
    def chat_deepseek(
        prompt: str,
        model: str = "deepseek-chat",
        temperature: float = 0.3,
        max_tokens: int = 1000,
        messages: Optional[List[Dict[str, str]]] = None  # ✅ NUEVO
    ) -> Dict[str, Any]:
        """
        Consulta a DeepSeek
        """
        try:
            if messages:
                payload = {
                    "model": model,
                    "messages": messages,
                    "temperature": temperature,
                    "max_tokens": max_tokens
                }
            else:
                payload = {
                    "model": model,
                    "messages": [{"role": "user", "content": prompt}],
                    "temperature": temperature,
                    "max_tokens": max_tokens
                }
            
            response = requests.post(
                IAEndpoints.get_chat_endpoint('deepseek'),
                headers=IAProviders.get_deepseek_headers(),
                json=payload,
                timeout=30
            )
            response.raise_for_status()
            data = response.json()
            
            return {
                "response": data["choices"][0]["message"]["content"],
                "usage": {
                    "input": data["usage"]["prompt_tokens"],
                    "output": data["usage"]["completion_tokens"],
                    "total": data["usage"]["total_tokens"]
                }
            }
        except Exception as e:
            raise Exception(f"Error en DeepSeek: {str(e)}")
    
    @staticmethod
    def chat_unificado(
        provider: str,
        prompt: str,
        model: Optional[str] = None,
        messages: Optional[List[Dict[str, str]]] = None,  # ✅ NUEVO: historial opcional
        **kwargs
    ) -> Dict[str, Any]:
        """
        Método unificado que llama al proveedor especificado
        """
        providers = {
            'mistral': AgenteKBIntegration.chat_mistral,
            'gemini': AgenteKBIntegration.chat_gemini,
            'claude': AgenteKBIntegration.chat_claude,
            'openai': AgenteKBIntegration.chat_openai,
            'deepseek': AgenteKBIntegration.chat_deepseek,
        }
        
        if provider.lower() not in providers:
            raise ValueError(f"Proveedor no soportado: {provider}")
        
        # Mapear nombres de modelos por defecto
        if model is None:
            default_models = {
                'mistral': 'mistral-small-latest',
                'gemini': 'gemini-3.5-flash',
                'claude': os.getenv('CLAUDE_MODEL', 'claude-opus-4-8'),
                'openai': 'gpt-4o-mini',
                'deepseek': 'deepseek-chat'
            }
            model = default_models.get(provider.lower(), 'mistral-small-latest')
        
        # ✅ Pasar messages a todos los proveedores
        if provider.lower() == 'claude':
            return providers[provider.lower()](prompt=prompt, model=model, messages=messages)
        
        return providers[provider.lower()](prompt=prompt, model=model, messages=messages, **kwargs)