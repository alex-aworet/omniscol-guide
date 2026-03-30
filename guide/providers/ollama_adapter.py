import httpx
import json
import logging

logger = logging.getLogger("omniscol")

class OllamaAdapter:
    def __init__(self, model: str = "mistral", host: str = "http://localhost:11434"):
        self.model = model
        self.host = host.rstrip("/")

    async def chat(self, messages: list[dict], tools: list[dict] | None = None) -> dict:
        async with httpx.AsyncClient(timeout=600.0) as client:  # 10 minute timeout for Mistral
            payload = {
                "model": self.model,
                "messages": messages,
                "stream": False,
            }
            
            # Only include tools if they exist
            if tools:
                payload["tools"] = tools
            
            try:
                response = await client.post(
                    f"{self.host}/api/chat",
                    json=payload,
                )
                
                if response.status_code != 200:
                    error_body = response.text
                    logger.error(f"❌ Ollama error {response.status_code}: {error_body}")
                    response.raise_for_status()
                
                result = response.json()
                return result
                
            except httpx.ReadTimeout:
                logger.error(f"❌ Ollama request timed out after 600 seconds. Model may be overloaded or not responding.")
                raise
            except httpx.HTTPStatusError as e:
                logger.error(f"❌ HTTP Error from Ollama: {e.response.status_code}")
                logger.error(f"❌ Response body: {e.response.text}")
                raise
            except Exception as e:
                logger.error(f"❌ Error communicating with Ollama: {type(e).__name__}: {str(e)}")
                raise