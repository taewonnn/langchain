import os
import requests
from dotenv import load_dotenv

load_dotenv()

def scrape_linkedin_profile(linkedin_profile_url: str, mock: bool = False):
    """Scrape information from LinkedIn profiles."""

    if mock:
        linkedin_profile_url = "https://gist.githubusercontent.com/emarco177/859ec7d786b45d8e3e3f688c6c9139d8/raw/32f3c85b9513994c572613f2c8b376b633bfc43f/eden-marco-scrapin.json"
        response = requests.get(linkedin_profile_url, timeout=10)
    else:
        # 공식 문서에 나온 endpoint 사용 (예: Proxycurl)
        api_endpoint = "https://nubela.co/proxycurl/api/v2/linkedin"
        headers = {
            "Authorization": f"Bearer {os.getenv('SCRAPIN_API_KEY')}"
        }
        params = {
            "linkedin_profile_url": linkedin_profile_url,
            "extra": "include",
            "github_profile_id": "include",
            "facebook_profile_id": "include",
            "twitter_profile_id": "include",
            "personal_contact_number": "include",
            "personal_email": "include",
            "inferred_salary": "include",
            "skills": "include",
            "use_cache": "if-present",
            "fallback_to_cache": "on-error",
        }
        response = requests.get(api_endpoint, headers=headers, params=params, timeout=10)

    json_data = response.json()
    #print(json_data)
    
    # 프로필
    data = json_data.get("profile_pic_url")
    print(data)


    return data

if __name__ == "__main__":
    print(
        scrape_linkedin_profile(
            linkedin_profile_url="https://www.linkedin.com/in/taewon-park-1b3469194/"
        )
    )
