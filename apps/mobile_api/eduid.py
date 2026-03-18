import requests
from django.conf import settings


class EduIDClient:
    def __init__(self, bearer_token: str):
        self.bearer_token = bearer_token

    def get_links(self):
        url = f"{settings.EDUID_API_BASE_URL}/myconext/api/eduid/links"

        headers = {
            "Accept": "application/json",
            "Authorization": f"Bearer {self.bearer_token}",
        }

        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()

        return response.json()
