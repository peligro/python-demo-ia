"""
Servicio de integración con APIs de IA para el Agente KB
Centraliza las llamadas a diferentes proveedores
"""
import requests
import os
import base64
from typing import Optional, Dict, Any, List
from .headers_ia import IAProviders, IAEndpoints


class AgenteIntegration:
    """
    Cliente unificado para llamar a diferentes proveedores de IA
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
            'mistral': AgenteIntegration.chat_mistral,
            'gemini': AgenteIntegration.chat_gemini,
            'claude': AgenteIntegration.chat_claude,
            'openai': AgenteIntegration.chat_openai,
            'deepseek': AgenteIntegration.chat_deepseek,
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

    
    @staticmethod
    def analyze_image_openai(
        prompt: str,
        image_url: str,
        model: str = "gpt-4o",
        max_tokens: int = 500
    ) -> Dict[str, Any]:
        """Analiza imagen con OpenAI GPT-4o"""
        try:
            # Descargar y codificar imagen
            response_imagen = requests.get(image_url, timeout=10)
            response_imagen.raise_for_status()
            imagen_base64 = base64.b64encode(response_imagen.content).decode('utf-8')
            content_type = response_imagen.headers.get('content-type', 'image/jpeg')
            
            payload = {
                "model": model,
                "messages": [{
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:{content_type};base64,{imagen_base64}"
                            }
                        }
                    ]
                }],
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
            raise Exception(f"Error en OpenAI Image: {str(e)}")


    
    @staticmethod
    def analyze_image_gemini(
        prompt: str,
        image_url: str,
        model: str = "gemini-2.5-flash",
        max_tokens: int = 500
    ) -> Dict[str, Any]:
        """Analiza imagen con Google Gemini"""
        try:
            # Descargar y codificar imagen
            response_imagen = requests.get(image_url, timeout=10)
            response_imagen.raise_for_status()
            imagen_base64 = base64.b64encode(response_imagen.content).decode('utf-8')
            content_type = response_imagen.headers.get('content-type', 'image/jpeg')
            
            payload = {
                "contents": [{
                    "role": "user",
                    "parts": [
                        {"text": prompt},
                        {
                            "inline_data": {
                                "mime_type": content_type,
                                "data": imagen_base64
                            }
                        }
                    ]
                }],
                "generationConfig": {
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
            raise Exception(f"Error en Gemini Image: {str(e)}")

    @staticmethod
    def transcribe_audio_openai(
        audio_file_path: str,
        language: Optional[str] = "es",
        model: str = "whisper-1"
    ) -> Dict[str, Any]:
        """Transcribe audio usando OpenAI Whisper"""
        try:
            # Validar archivo
            if not os.path.exists(audio_file_path):
                raise FileNotFoundError(f"Archivo no encontrado: {audio_file_path}")
            
            # Determinar MIME type
            ext = os.path.splitext(audio_file_path)[1].lower().lstrip('.')
            mime_types = {
                'mp3': 'audio/mpeg',
                'ogg': 'audio/ogg',
                'wav': 'audio/wav',
                'm4a': 'audio/mp4',
                'flac': 'audio/flac'
            }
            mime_type = mime_types.get(ext, 'audio/mpeg')
            
            # Preparar request multipart/form-data
            with open(audio_file_path, 'rb') as audio_file:
                files = {
                    'file': (os.path.basename(audio_file_path), audio_file, mime_type),
                    'model': (None, model),
                    'response_format': (None, 'text'),
                }
                if language:
                    files['language'] = (None, language)
                
                response = requests.post(
                    f"{IAEndpoints.OPENAI_BASE}audio/transcriptions",
                    headers={"Authorization": f"Bearer {os.getenv('OPENAI_API_KEY')}"},
                    files=files,
                    timeout=120  # Whisper puede tardar con archivos largos
                )
                response.raise_for_status()
                
                return {
                    "transcription": response.text.strip(),
                    "usage": {"input": 0, "output": 0, "total": 0},  # Whisper no retorna tokens
                    "duration": None,  # Podríamos extraerlo con mutagen si es necesario
                    "detected_language": language
                }
        except Exception as e:
            raise Exception(f"Error en Whisper: {str(e)}")

    @staticmethod
    def transcribe_audio_gemini(
        audio_file_path: str,
        model: str = "gemini-2.5-flash",
        language: Optional[str] = "es"
    ) -> Dict[str, Any]:
        """Transcribe audio usando Google Gemini"""
        try:
            # Validar archivo y tamaño (Gemini: máx 20MB)
            if not os.path.exists(audio_file_path):
                raise FileNotFoundError(f"Archivo no encontrado: {audio_file_path}")
            
            file_size = os.path.getsize(audio_file_path) / (1024 * 1024)
            if file_size > 20:
                raise ValueError(f"Archivo demasiado grande ({file_size:.1f}MB). Máximo 20MB para Gemini")
            
            # Determinar MIME type
            ext = os.path.splitext(audio_file_path)[1].lower().lstrip('.')
            mime_types = {
                'mp3': 'audio/mpeg',
                'ogg': 'audio/ogg',
                'wav': 'audio/wav',
                'm4a': 'audio/mp4',
                'flac': 'audio/flac'
            }
            mime_type = mime_types.get(ext, 'audio/mpeg')
            
            # Leer y codificar audio
            with open(audio_file_path, 'rb') as audio_file:
                audio_data = audio_file.read()
                audio_base64 = base64.b64encode(audio_data).decode('utf-8')
            
            # Construir prompt
            prompt = "Transcribe este audio a texto exactamente como se escucha. Devuelve solo la transcripción sin comentarios adicionales, títulos o explicaciones."
            
            payload = {
                'contents': [{
                    'role': 'user',
                    'parts': [
                        {'text': prompt},
                        {
                            'inline_data': {
                                'mime_type': mime_type,
                                'data': audio_base64
                            }
                        }
                    ]
                }],
                'generationConfig': {
                    'temperature': 0.1,
                    'maxOutputTokens': 2000
                }
            }
            
            # Hacer request a Gemini
            base_url = IAEndpoints.GEMINI_BASE.rstrip('/')
            url = f"{base_url}/models/{model}:generateContent"
            
            response = requests.post(
                url,
                headers=IAProviders.get_gemini_headers(),
                json=payload,
                timeout=120
            )
            response.raise_for_status()
            data = response.json()
            
            # Verificar bloqueos de seguridad
            if 'promptFeedback' in data and 'blockReason' in data['promptFeedback']:
                raise ValueError(f"Bloqueo de contenido: {data['promptFeedback']['blockReason']}")
            
            # Extraer transcripción
            if 'candidates' in data and len(data['candidates']) > 0:
                transcription = data['candidates'][0]['content']['parts'][0]['text'].strip()
            else:
                raise ValueError("Gemini no devolvió una transcripción válida")
            
            # Extraer tokens si están disponibles
            usage = {"input": 0, "output": 0, "total": 0}
            if "usageMetadata" in data:
                usage = {
                    "input": data["usageMetadata"].get("promptTokenCount", 0),
                    "output": data["usageMetadata"].get("candidatesTokenCount", 0),
                    "total": data["usageMetadata"].get("totalTokenCount", 0)
                }
            
            return {
                "transcription": transcription,
                "usage": usage,
                "duration": None,  # Gemini no retorna duración en la respuesta
                "detected_language": language
            }
        except Exception as e:
            raise Exception(f"Error en Gemini Audio: {str(e)}")