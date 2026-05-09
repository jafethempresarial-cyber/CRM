import abc
import httpx
import json
from logger import setup_logger

logger = setup_logger("whatsapp_service")

class BaseWhatsApp(abc.ABC):
    @abc.abstractmethod
    async def send_message(self, to: str, text: str, media_url: str = None, media_type: str = None) -> bool:
        pass

class MockWhatsAppDriver(BaseWhatsApp):
    """
    Mock driver for local development and simulation.
    Does not make external network requests.
    """
    async def send_message(self, to: str, text: str, media_url: str = None, media_type: str = None) -> bool:
        logger.info(f"[MOCK SEND] To: {to} | Content: {text[:50]}... | Media: {media_url}")
        return True

class MetaWhatsAppDriver(BaseWhatsApp):
    # ... (MetaWhatsAppDriver logic remains same)
    def __init__(self, token: str, phone_id: str):
        self.token = token
        self.phone_id = phone_id
        self.base_url = f"https://graph.facebook.com/v23.0/{phone_id}/messages"

    async def send_message(self, to: str, text: str, media_url: str = None, media_type: str = None) -> bool:
        if not self.token or not self.phone_id:
            logger.error("Meta Driver initialized without Token or Phone ID")
            return False

        headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json"
        }

        payload = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": to,
            "type": "text",
            "text": {"preview_url": False, "body": text}
        }

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(self.base_url, headers=headers, json=payload)
                if response.status_code == 200:
                    resp_data = response.json()
                    wamid = resp_data.get("messages", [{}])[0].get("id")
                    logger.info(f"[META SEND SUCCESS] To: {to} | ID: {wamid}")
                    return wamid if wamid else True
                else:
                    logger.error(f"[META SEND FAIL] {response.status_code}: {response.text}")
                    return False
        except Exception as e:
            logger.error(f"[META SEND ERROR] {e}")
            return False

class EvolutionWhatsAppDriver(BaseWhatsApp):
    """
    Driver for Evolution API (Open Source WhatsApp API).
    Supports simulated typing for better security.
    """
    def __init__(self, api_url: str, api_key: str, instance: str):
        self.api_url = api_url.rstrip("/")
        self.api_key = api_key
        self.instance = instance

    async def send_message(self, to: str, text: str, media_url: str = None, media_type: str = None) -> bool:
        url = f"{self.api_url}/message/sendText/{self.instance}"
        headers = {
            "apikey": self.api_key,
            "Content-Type": "application/json"
        }
        
        # Normalize number
        clean_number = to.split("@")[0]
        
        payload = {
            "number": clean_number,
            "options": {
                "delay": 1200, # Simulate human typing (1.2 seconds)
                "presence": "composing",
                "linkPreview": False
            },
            "textMessage": {
                "text": text
            }
        }
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(url, headers=headers, json=payload)
                if response.status_code in [200, 201]:
                    logger.info(f"[EVOLUTION SEND SUCCESS] To: {to}")
                    return True
                else:
                    logger.error(f"[EVOLUTION SEND FAIL] {response.status_code}: {response.text}")
                    return False
        except Exception as e:
            logger.error(f"[EVOLUTION SEND ERROR] {e}")
            return False

class WhatsAppService:
    @staticmethod
    def get_driver(config_dict: dict) -> BaseWhatsApp:
        driver_type = config_dict.get("whatsapp_driver", "mock")
        
        if driver_type == "meta":
            token = config_dict.get("whatsapp_api_token")
            phone_id = config_dict.get("whatsapp_phone_id")
            return MetaWhatsAppDriver(token, phone_id)
        
        if driver_type == "evolution":
            url = config_dict.get("evolution_api_url")
            key = config_dict.get("evolution_api_key")
            instance = config_dict.get("evolution_instance_name")
            return EvolutionWhatsAppDriver(url, key, instance)
        
        return MockWhatsAppDriver()
