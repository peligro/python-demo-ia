import time
import re
from typing import Optional, Literal
from sqlmodel import Session
from integraciones.agente_integration import AgenteIntegration
from schemas.generate_sql import GenerateSQLRequest, GenerateSQLResponse

class GenerateSQLService:
    # Schema de la tabla usuarios (para inyectar en el prompt)
    TABLE_SCHEMA = """
    Tabla: usuarios
    Columnas:
    - id (int): ID único, primary key, autoincremental
    - name (string): Nombre completo del usuario
    - correo (string): Email del usuario, único
    - password (string): Password encriptado/hash
    - state (int): Estado del usuario: 1=activo, 0=inactivo
    - created_ut (datetime): Fecha y hora de creación
    - updated_at (datetime): Fecha y hora de última actualización
    - phone (string): Número de teléfono
    """

    def __init__(self, session: Session):
        self.session = session

    async def generate(self, request: GenerateSQLRequest) -> GenerateSQLResponse:
        start_time = time.time()
        
        # Construir prompt optimizado para generación SQL
        prompt = self._build_sql_prompt(
            question=request.question,
            dialect=request.dialect
        )
        
        # Determinar proveedor
        provider = self._get_provider_from_model(request.model)
        
        try:
            # Llamar a la IA
            result = AgenteIntegration.chat_unificado(
                provider=provider,
                prompt=prompt,
                model=request.model
            )
            
            latency_ms = int((time.time() - start_time) * 1000)
            
            # Parsear respuesta: extraer SQL y explicación
            sql_query, explanation = self._parse_sql_response(result["response"], request.dialect)
            
            return GenerateSQLResponse(
                question=request.question,
                sql_query=sql_query,
                explanation=explanation,
                dialect=request.dialect,
                model_used=request.model,
                metrics={
                    "input_tokens": result["usage"]["input"],
                    "output_tokens": result["usage"]["output"],
                    "total_tokens": result["usage"]["total"],
                    "latency_ms": latency_ms
                }
            )
        except Exception as e:
            latency_ms = int((time.time() - start_time) * 1000)
            return GenerateSQLResponse(
                question=request.question,
                sql_query=f"-- Error: {str(e)}",
                explanation="No se pudo generar la consulta SQL",
                dialect=request.dialect,
                model_used=request.model,
                metrics={"latency_ms": latency_ms}
            )

    def _build_sql_prompt(self, question: str, dialect: str) -> str:
        """Construye el prompt optimizado para generación de SQL"""
        return f"""Eres un experto en bases de datos {dialect.upper()}. Tu tarea es convertir preguntas en lenguaje natural a consultas SQL válidas.

Esquema de la tabla disponible:
{self.TABLE_SCHEMA}

Pregunta del usuario: "{question}"

Instrucciones estrictas:
1. Genera SOLO una consulta SQL válida para {dialect}
2. NUNCA uses SELECT * - especifica siempre las columnas necesarias
3. Usa la columna 'state' para filtrar usuarios activos (state = 1) cuando sea relevante
4. Ordena los resultados por 'id DESC' por defecto, a menos que la pregunta indique otro orden
5. Usa nombres de columnas exactos como están definidos en el esquema
6. NO agregues explicaciones, comentarios ni código markdown (```sql)
7. Si la pregunta es ambigua, asume el comportamiento más común y seguro
8. Para filtros de texto, usa LIKE con % para búsquedas parciales cuando sea apropiado

Respuesta (SOLO la consulta SQL, nada más):"""

    def _parse_sql_response(self, response: str, dialect: str) -> tuple[str, str]:
        """Parsea la respuesta para extraer SQL limpio y una breve explicación"""
        # Limpiar respuesta: remover markdown, comentarios, etc.
        sql = response.strip()
        
        # Remover bloques de código markdown si existen
        if sql.startswith("```sql"):
            sql = sql[6:]
        if sql.startswith("```"):
            sql = sql[3:]
        if sql.endswith("```"):
            sql = sql[:-3]
        
        sql = sql.strip()
        
        # Intentar extraer explicación si viene después del SQL
        lines = sql.split('\n')
        sql_lines = []
        explanation_lines = []
        in_explanation = False
        
        for line in lines:
            stripped = line.strip()
            if stripped.startswith('--') and not stripped.startswith('-- Error'):
                in_explanation = True
                explanation_lines.append(stripped[2:].strip())
            elif in_explanation:
                explanation_lines.append(stripped)
            else:
                sql_lines.append(line)
        
        clean_sql = '\n'.join(sql_lines).strip()
        explanation = ' '.join(explanation_lines).strip() if explanation_lines else None
        
        # Validar que la consulta parece SQL válido
        if not re.search(r'\b(SELECT|INSERT|UPDATE|DELETE)\b', clean_sql, re.IGNORECASE):
            match = re.search(r'(SELECT .*?;?)', clean_sql, re.DOTALL | re.IGNORECASE)
            if match:
                clean_sql = match.group(1).strip()
        
        return clean_sql, explanation

    def _get_provider_from_model(self, model: str) -> str:
        model_lower = model.lower()
        if 'mistral' in model_lower: return 'mistral'
        elif 'gemini' in model_lower: return 'gemini'
        elif 'claude' in model_lower: return 'claude'
        elif 'gpt' in model_lower or 'openai' in model_lower: return 'openai'
        elif 'deepseek' in model_lower: return 'deepseek'
        return 'mistral'