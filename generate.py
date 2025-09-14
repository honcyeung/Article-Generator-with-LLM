import requests
from google import genai
from google.genai import types
import yaml
import os
import json
from datetime import datetime

from dotenv import load_dotenv
load_dotenv()
PROMPTLAYER_API_KEY = os.environ.get("PROMPTLAYER_API_KEY")
PROMPT_TEMPLATE_IDENTIFIER = os.environ.get("PROMPT_TEMPLATE_IDENTIFIER")
PROMPT_TEMPLATE_IDENTIFIER2 = os.environ.get("PROMPT_TEMPLATE_IDENTIFIER2")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

def get_prompt(prompt_template_identifier):
  
    try:
        url = f"https://api.promptlayer.com/prompt-templates/{prompt_template_identifier}"
        headers = {
            "X-API-KEY": PROMPTLAYER_API_KEY,
            "Content-Type": "application/json"
        }

        response = requests.post(url, headers = headers)
        response.raise_for_status()
        data = response.json()

        messages = data.get("prompt_template", {}).get("messages", {})
        user_prompt = ""
        system_prompt = ""
        for m in messages:
            if m.get("role", {}) == "system":
                system_prompt = m.get("content", [])[0].get("text", "")
            if m.get("role", {}) == "user":
                user_prompt = m.get("content", [])[0].get("text", "")

        return system_prompt, user_prompt
    except Exception as e:
        raise Exception(e)

def generate_article(model, system_prompt, user_prompt, temperature):

    try:
        client = genai.Client(api_key = GEMINI_API_KEY)
        response = client.models.generate_content(
            model = model, 
            contents = user_prompt,
            config = types.GenerateContentConfig(
                system_instruction = system_prompt,
                temperature = temperature
            )
        )

        print("Article generated successfully.")
        return response.text
    except Exception as e:
        raise Exception(e)

def check_article_title(article):

    titles = article.split("\n")
    titles = [t.strip() for t in titles]

    for t in titles:
        if t.startswith("# "):
            title = t.lstrip("#").strip()
            return title
    return titles[0]
    
def generate_metadata(system_prompt, article):

    try:
        system_prompt = system_prompt.replace("[PASTE THE FULL ARTICLE TEXT HERE]", article)

        schema = {
            "type": "object",
            "properties": {
                "description": {
                    "type": "string",
                    "description": "This is the compelling, SEO-optimized description under 160 characters, designed to maximize clicks."
                },
                "tags": {
                    "type": "array",
                    "items": {
                        "type": "string"
                    }
                }
            },
            "required": ["description", "tags"]
        }

        client = genai.Client(api_key = GEMINI_API_KEY)
        response = client.models.generate_content(
            model = "gemini-2.0-flash-lite", 
            contents = system_prompt,
            config = types.GenerateContentConfig(
                temperature = 0.5,
                response_mime_type = "application/json",
                max_output_tokens = 1024,
                response_schema = schema
            )
        )

        print("Metadata generated successfully.")
        parsed_json = json.loads(response.text)

        return parsed_json
    except Exception as e:
        raise Exception(e)

def format_yaml(article, parsed_json):

    try:
        title = check_article_title(article)
        today_string = datetime.now().strftime("%Y-%m-%d")

        frontmatter_data = {
            'title': title,
            'description': parsed_json['description'],
            'date': today_string,
            'draft': False,
            'author': "Gemini",
            'tags': parsed_json['tags']
        }

        yaml_string = yaml.dump(frontmatter_data, sort_keys = False, allow_unicode = True, default_flow_style = False)
        final_frontmatter_block = f"---\n{yaml_string}---"

        return final_frontmatter_block, title
    except Exception as e:
        raise Exception(e)

def save_article_as_markdown(final_article_output):

    try:
        today_ts = int(datetime.now().timestamp())  # use timestamp as a unique identifier
        filename = f"{today_ts}.md"
        output_dir = "output"
        os.makedirs(output_dir, exist_ok = True)
        file_path = os.path.join(output_dir, filename)

        with open(file_path, "w", encoding = "utf-8") as f:
            f.write(final_article_output)
        print(f"Article has been saved to {filename}")
    except Exception as e:
        raise Exception(e)

def pipeline(model, temperature):

    system_prompt, user_prompt = get_prompt(PROMPT_TEMPLATE_IDENTIFIER)
    article = generate_article(model, system_prompt, user_prompt, temperature)

    system_prompt, _ = get_prompt(PROMPT_TEMPLATE_IDENTIFIER2)
    article_metadata = generate_metadata(system_prompt, article)
    yaml_formatter, title = format_yaml(article, article_metadata)
    
    final_article_output = f"{yaml_formatter}\n\n{article}"
    save_article_as_markdown(final_article_output)
    
    return final_article_output, title