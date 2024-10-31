import requests

def analyze_text(text):
    api_url = "https://example-profanity-api.com/analyze"
    response = requests.post(api_url, json={"text": text})
    if response.status_code == 200:
        result = response.json()
        return result.get("contains_profanity", False)
    return False
