from models.image_model import analyze_image
from models.text_model import analyze_text

def analyze_content(text, image_path):
    is_nsfw = analyze_image(image_path)
    contains_profanity = analyze_text(text)
    return {"is_nsfw": is_nsfw, "contains_profanity": contains_profanity}