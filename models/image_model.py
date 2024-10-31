import requests

def analyze_image(image_path):
    api_url = "https://example-nsfw-api.com/analyze"
    files = {'image': open(image_path, 'rb')}
    response = requests.post(api_url, files=files)
    if response.status_code == 200:
        result = response.json()
        return result.get("nsfw_score", 0) > 0.5  # 예: 0.5 이상의 점수면 음란물로 간주
    return False