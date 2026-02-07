"""
Ollama Client - Interface avec l'API Ollama
Support: génération, streaming, embeddings
"""

import logging
from typing import Any, AsyncGenerator, Dict, List, Optional

import httpx
from app.core.config import settings
from app.core.metrics import record_llm_call

logger = logging.getLogger(__name__)


class OllamaClient:
    """Client pour l'API Ollama"""

    def __init__(self, base_url: Optional[str] = None):
        self.base_url = base_url or settings.OLLAMA_URL
        # Timeouts configurables (v7.1)
        self.timeout = httpx.Timeout(
            settings.TIMEOUT_OLLAMA_CHAT, connect=settings.TIMEOUT_OLLAMA_CONNECT
        )

    async def health_check(self) -> bool:
        """Vérifie si Ollama est disponible"""
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(f"{self.base_url}/api/tags")
                return response.status_code == 200
        except Exception as e:
            logger.error(f"Ollama health check failed: {e}")
            return False

    async def list_models(self) -> List[Dict[str, Any]]:
        """Liste les modèles disponibles"""
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(f"{self.base_url}/api/tags")
                if response.status_code == 200:
                    data = response.json()
                    return data.get("models", [])
                return []
        except Exception as e:
            logger.error(f"Failed to list models: {e}")
            return []

    async def generate(
        self,
        prompt: str,
        model: Optional[str] = None,
        system: Optional[str] = None,
        context: Optional[List[int]] = None,
        options: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Génère une réponse (non-streaming)"""
        model = model or settings.DEFAULT_MODEL

        payload = {
            "model": model,
            "prompt": prompt,
            "stream": False,
            "options": options or {"temperature": 0.7, "num_ctx": 8192},
        }

        if system:
            payload["system"] = system
        if context:
            payload["context"] = context

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(f"{self.base_url}/api/generate", json=payload)

                if response.status_code == 200:
                    result = response.json()

                    # Enregistrer métriques LLM (PHASE 6)
                    prompt_tokens = result.get("prompt_eval_count", 0)
                    completion_tokens = result.get("eval_count", 0)
                    record_llm_call(
                        model=model,
                        success=True,
                        prompt_tokens=prompt_tokens,
                        completion_tokens=completion_tokens,
                    )

                    return result
                else:
                    logger.error(f"Ollama generate error: {response.status_code}")

                    # Enregistrer échec (PHASE 6)
                    record_llm_call(model=model, success=False)

                    return {"error": f"HTTP {response.status_code}", "response": ""}

        except Exception as e:
            logger.error(f"Ollama generate failed: {e}")

            # Enregistrer échec exception (PHASE 6)
            record_llm_call(model=model, success=False)

            return {"error": str(e), "response": ""}

    async def generate_stream(
        self,
        prompt: str,
        model: Optional[str] = None,
        system: Optional[str] = None,
        options: Optional[Dict[str, Any]] = None,
    ) -> AsyncGenerator[str, None]:
        """Génère une réponse en streaming"""
        model = model or settings.DEFAULT_MODEL

        payload = {
            "model": model,
            "prompt": prompt,
            "stream": True,
            "options": options or {"temperature": 0.7, "num_ctx": 8192},
        }

        if system:
            payload["system"] = system

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                async with client.stream(
                    "POST", f"{self.base_url}/api/generate", json=payload
                ) as response:
                    async for line in response.aiter_lines():
                        if line:
                            import json

                            try:
                                data = json.loads(line)
                                if "response" in data:
                                    yield data["response"]
                                if data.get("done"):
                                    break
                            except json.JSONDecodeError:
                                continue
        except Exception as e:
            logger.error(f"Ollama stream failed: {e}")
            yield f"[Erreur: {str(e)}]"

    async def chat(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        options: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Chat avec historique (format OpenAI-like)"""
        model = model or settings.DEFAULT_MODEL

        payload = {
            "model": model,
            "messages": messages,
            "stream": False,
            "options": options or {"temperature": 0.7, "num_ctx": 8192},
        }

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(f"{self.base_url}/api/chat", json=payload)

                if response.status_code == 200:
                    result = response.json()

                    # Enregistrer métriques LLM (PHASE 6)
                    prompt_tokens = result.get("prompt_eval_count", 0)
                    completion_tokens = result.get("eval_count", 0)
                    record_llm_call(
                        model=model,
                        success=True,
                        prompt_tokens=prompt_tokens,
                        completion_tokens=completion_tokens,
                    )

                    return result
                else:
                    # Enregistrer échec (PHASE 6)
                    record_llm_call(model=model, success=False)

                    return {"error": f"HTTP {response.status_code}"}

        except Exception as e:
            logger.error(f"Ollama chat failed: {e}")

            # Enregistrer échec exception (PHASE 6)
            record_llm_call(model=model, success=False)

            return {"error": str(e)}

    async def chat_stream(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        options: Optional[Dict[str, Any]] = None,
    ) -> AsyncGenerator[str, None]:
        """Chat avec historique en streaming"""
        model = model or settings.DEFAULT_MODEL

        payload = {
            "model": model,
            "messages": messages,
            "stream": True,
            "options": options or {"temperature": 0.7, "num_ctx": 8192},
        }

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                async with client.stream(
                    "POST", f"{self.base_url}/api/chat", json=payload
                ) as response:
                    async for line in response.aiter_lines():
                        if line:
                            import json

                            try:
                                data = json.loads(line)
                                if "message" in data and "content" in data["message"]:
                                    yield data["message"]["content"]
                                if data.get("done"):
                                    break
                            except json.JSONDecodeError:
                                continue
        except Exception as e:
            logger.error(f"Ollama chat stream failed: {e}")
            yield f"[Erreur: {str(e)}]"

    async def embeddings(self, text: str, model: str = "nomic-embed-text") -> List[float]:
        """Génère des embeddings pour un texte"""
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{self.base_url}/api/embeddings", json={"model": model, "prompt": text}
                )

                if response.status_code == 200:
                    data = response.json()
                    return data.get("embedding", [])
                return []

        except Exception as e:
            logger.error(f"Embeddings failed: {e}")
            return []


# Instance singleton
ollama_client = OllamaClient()
