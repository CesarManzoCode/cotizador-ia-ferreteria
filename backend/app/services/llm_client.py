"""
Cliente LLM abstracto para integración con Groq.
La abstracción permite cambiar de proveedor (OpenAI, Anthropic, local) 
en el futuro modificando solo este módulo.

ARQUITECTURA: Este módulo es la capa de adaptador hacia el LLM.
Si cambias de proveedor, modifica solo este archivo y el .env.
"""

import json
import logging
from typing import Optional
import httpx

from app.core.config import settings

logger = logging.getLogger(__name__)


class LLMClient:
    """
    Cliente abstracto para interacción con el LLM.
    Actualmente usa la API compatible con OpenAI de Groq.
    
    FUTURA EXTENSIÓN: Para cambiar de proveedor, implementa una clase
    alternativa con el mismo método `completar()` y actualiza la
    instancia en `get_llm_client()`.
    """

    def __init__(self):
        self.api_key = settings.GROQ_API_KEY
        self.base_url = settings.GROQ_BASE_URL
        self.modelo = settings.GROQ_MODELO
        self.temperatura = settings.GROQ_TEMPERATURA
        self.max_tokens = settings.GROQ_MAX_TOKENS

        # PUNTO DE DEBUGGING: Si la API key está vacía, el LLM fallará silenciosamente
        if not self.api_key:
            logger.warning(
                "GROQ_API_KEY no configurada. El LLM no funcionará. "
                "Configura GROQ_API_KEY en el archivo .env"
            )

    async def completar(
        self,
        prompt_sistema: str,
        prompt_usuario: str,
        temperatura: Optional[float] = None,
    ) -> Optional[str]:
        """
        Envía un prompt al LLM y devuelve la respuesta como texto.
        
        Args:
            prompt_sistema: Instrucciones del sistema para el modelo
            prompt_usuario: Mensaje del usuario
            temperatura: Override de temperatura (usa config por defecto si None)
        
        Returns:
            Texto de respuesta del LLM, o None si falla
        """
        if not self.api_key:
            logger.error("Intento de llamada al LLM sin API key configurada.")
            return None

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        payload = {
            "model": self.modelo,
            "messages": [
                {"role": "system", "content": prompt_sistema},
                {"role": "user", "content": prompt_usuario},
            ],
            "temperature": temperatura if temperatura is not None else self.temperatura,
            "max_tokens": self.max_tokens,
        }

        try:
            async with httpx.AsyncClient(timeout=30.0) as cliente:
                respuesta = await cliente.post(
                    f"{self.base_url}/chat/completions",
                    headers=headers,
                    json=payload,
                )
                respuesta.raise_for_status()
                data = respuesta.json()
                contenido = data["choices"][0]["message"]["content"]
                return contenido

        except httpx.TimeoutException:
            logger.error("Timeout al conectar con Groq API. Verifica tu conexión.")
            return None
        except httpx.HTTPStatusError as e:
            logger.error(f"Error HTTP de Groq API: {e.response.status_code} - {e.response.text}")
            return None
        except Exception as e:
            logger.error(f"Error inesperado al llamar al LLM: {e}")
            return None

    async def extraer_productos_json(self, texto_usuario: str) -> Optional[list]:
        """
        Usa el LLM para extraer productos y cantidades del texto del usuario.
        Devuelve una lista de dicts con {nombre, cantidad, unidad, notas}.
        
        PUNTO DE DEBUGGING: Si el LLM devuelve JSON malformado, revisa el prompt
        de sistema en esta función. También revisa GROQ_MODELO en .env.
        """
        prompt_sistema = """Eres un asistente especializado en cotizaciones de materiales de construcción y ferretería.
Tu tarea es extraer productos y cantidades de un texto de solicitud de cotización.

INSTRUCCIONES ESTRICTAS:
1. Extrae SOLO los productos y cantidades mencionados explícitamente.
2. NO inventes productos ni modifiques lo que el usuario pidió.
3. Normaliza las descripciones (quita errores ortográficos obvios, expande abreviaciones).
4. Si no hay cantidad explícita, asume 1.
5. Responde ÚNICAMENTE con un array JSON válido. Sin texto adicional, sin markdown.

Formato de respuesta:
[
  {
    "nombre_original": "texto exacto del usuario",
    "nombre_normalizado": "versión normalizada y limpia",
    "cantidad": número,
    "unidad": "pieza/metro/kg/etc o null si no se menciona",
    "notas": "observaciones relevantes o null"
  }
]

Si el texto no contiene productos, responde: []"""

        prompt_usuario = f"Extrae los productos de esta solicitud:\n\n{texto_usuario}"

        respuesta = await self.completar(prompt_sistema, prompt_usuario, temperatura=0.0)

        if not respuesta:
            return None

        # Limpiar posibles backticks de markdown que el LLM podría incluir
        respuesta_limpia = respuesta.strip()
        if respuesta_limpia.startswith("```"):
            lineas = respuesta_limpia.split("\n")
            respuesta_limpia = "\n".join(lineas[1:-1])

        try:
            productos = json.loads(respuesta_limpia)
            if isinstance(productos, list):
                return productos
            else:
                logger.warning(f"LLM no devolvió un array: {respuesta_limpia[:200]}")
                return None
        except json.JSONDecodeError as e:
            # PUNTO DE DEBUGGING: Si falla aquí, el LLM no respetó el formato JSON
            # Posible solución: cambiar de modelo o ajustar el prompt de sistema
            logger.error(f"Error al parsear JSON del LLM: {e}")
            logger.debug(f"Respuesta raw del LLM: {respuesta_limpia[:500]}")
            return None


# Instancia global del cliente LLM
# Para cambiar de proveedor: reemplaza la clase aquí
_llm_client: Optional[LLMClient] = None


def get_llm_client() -> LLMClient:
    """Retorna la instancia global del cliente LLM (singleton)."""
    global _llm_client
    if _llm_client is None:
        _llm_client = LLMClient()
    return _llm_client
