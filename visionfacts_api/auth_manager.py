import requests
import os
from dotenv import load_dotenv

load_dotenv()

class AuthManager:
    """
    Manages authentication tokens for the application.
    Stores tokens globally within the instance or can be used as a singleton.
    """
    def __init__(self):
        self.access_token = None
        self.refresh_token = None
        self.base_url = os.getenv("AUTH_BASE_URL", "http://10.254.10.250:5000")
        self.email = os.getenv("VISIONFACTS_EMAIL", None)
        self.password = os.getenv("VISIONFACTS_PASSWORD", None)

    def login(self, email, password):
        """
        Performs login to retrieve JWT tokens.
        
        Args:
            email (str): The user's email address.
            password (str): The user's password.
            
        Returns:
            dict: A dictionary containing the access and refresh tokens.
        """
        url = f"{self.base_url}/users/refresh-login"
        headers = {
            "accept": "application/json",
            "Content-Type": "application/json"
        }
        payload = {
            "email": email,
            "password": password
        }

        try:
            response = requests.post(url, json=payload, headers=headers)
            response.raise_for_status()  # Check for HTTP errors
            
            data = response.json()
            self.access_token = data.get("accessToken")
            self.refresh_token = data.get("refreshToken")
            self.email = email
            self.password = password
            
            print("Successfully logged in and tokens stored.")
            return {
                "accessToken": self.access_token,
                "refreshToken": self.refresh_token
            }
        except requests.exceptions.HTTPError as e:
            print(f"HTTP error occurred: {e}")
            if response.status_code == 401:
                print("Invalid credentials.")
            raise
        except Exception as e:
            print(f"An error occurred: {e}")
            raise

    def get_auth_header(self):
        """
        Returns the Authorization header with the current access token.
        """
        if self.access_token:
            return {"Authorization": f"Bearer {self.access_token}"}
        return {}

# Global instance for easy access across the project
auth = AuthManager()


