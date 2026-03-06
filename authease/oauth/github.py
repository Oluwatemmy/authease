import logging

import requests
from django.conf import settings
from rest_framework.exceptions import AuthenticationFailed

logger = logging.getLogger(__name__)

GITHUB_TOKEN_URL = "https://github.com/login/oauth/access_token"
GITHUB_USER_URL = "https://api.github.com/user"
REQUEST_TIMEOUT = 10


class Github():

    @staticmethod
    def exchange_code_for_token(code):
        payload = {
            "client_id": settings.GITHUB_CLIENT_ID,
            "client_secret": settings.GITHUB_CLIENT_SECRET,
            "code": code,
        }
        try:
            response = requests.post(
                GITHUB_TOKEN_URL,
                params=payload,
                headers={'Accept': "application/json"},
                timeout=REQUEST_TIMEOUT,
            )
            response.raise_for_status()
            result = response.json()
        except requests.RequestException as e:
            logger.error("GitHub token exchange failed: %s", e)
            raise AuthenticationFailed("Unable to connect to GitHub. Please try again.")
        except ValueError:
            logger.error("GitHub token response was not valid JSON")
            raise AuthenticationFailed("Received an invalid response from GitHub.")

        error = result.get("error")
        if error:
            logger.warning("GitHub token exchange returned error: %s - %s", error, result.get("error_description", ""))
            raise AuthenticationFailed("The GitHub code is invalid or has expired.")

        token = result.get("access_token")
        if not token:
            raise AuthenticationFailed("The GitHub code is invalid or has expired.")
        return token

    @staticmethod
    def retrieve_github_user(access_token):
        try:
            headers = {
                "Authorization": f"Bearer {access_token}",
            }
            response = requests.get(
                GITHUB_USER_URL,
                headers=headers,
                timeout=REQUEST_TIMEOUT,
            )
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            logger.error("GitHub user retrieval failed: %s", e)
            raise AuthenticationFailed("Unable to retrieve user info from GitHub. Please try again.")
        except ValueError:
            logger.error("GitHub user response was not valid JSON")
            raise AuthenticationFailed("Received an invalid response from GitHub.")
