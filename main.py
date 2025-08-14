#!/usr/bin/env python
# coding: utf-8



import requests
import os
from dotenv import load_dotenv
from datetime import datetime
import json
import yaml
import shutil
import subprocess




load_dotenv()

try:
    PROMPTLAYER_API_KEY = os.environ["PROMPTLAYER_API_KEY"]
    GEMINI_API_KEY = os.environ["GEMINI_API_KEY"]
    HUGO_REPO_URL = os.environ["HUGO_REPO_URL"]
    PATH = os.environ["PATH"]
except KeyError as e:
    raise KeyError(f"Environment variable {e} is not set. Please set it before running the script.")


# # Generate articles and SEO metadata



def get_prompt(prompt_template_identifier):
  
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

    if not system_prompt :
            raise ValueError("System prompt not found in the PromptLayer response.")

    return system_prompt, user_prompt

def generate_text(system_prompt, user_prompt, model, config):
  
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
    headers = {
      "x-goog-api-key": GEMINI_API_KEY,
      "Content-Type": "application/json"
    }
    payload = {
        "system_instruction": {
            "parts": [{"text": system_prompt}]
        },
        "contents": [{
            "role": "user",
            "parts": [{"text": user_prompt}]
        }]
    }
    payload.update(config)

    try:
        response = requests.post(url, headers = headers, json = payload)
        response.raise_for_status()  

        data = response.json()
        if 'candidates' in data and data['candidates']:
            content_parts = data['candidates'][0].get('content', {}).get('parts', [])
            if content_parts:
                return content_parts[0].get('text', "Error: Could not extract text from response.")
        return "Error: No content generated or response format is unexpected."
    except requests.exceptions.RequestException as e:
        return f"Error making API request: {e}"
    except Exception as e:
        return f"An unexpected error occurred: {e}\nResponse Body: {response.text}"

def check_article_title(article):

    titles = article.split("\n")
    titles = [t.strip() for t in titles]

    for t in titles:
        if t.startswith("# "):
            title = t.lstrip("#").strip()
            return title
    return titles[0]
    
def format_yaml(title, parsed_json, today_string, author):

    frontmatter_data = {
        'title': title,
        'description': parsed_json['description'],
        'date': today_string,
        'draft': False,
        'author': author,
        'tags': parsed_json['tags']
    }

    yaml_string = yaml.dump(frontmatter_data, sort_keys = False, allow_unicode = True, default_flow_style = False)
    final_frontmatter_block = f"---\n{yaml_string}---"
    return final_frontmatter_block




system_prompt, user_prompt = get_prompt("80912")
if not user_prompt:
    raise ValueError("User prompt not found in the PromptLayer response.")

print("Generating article... Please wait.")

article_generation_model = "gemini-2.5-pro"
article_generation_config = {"generationConfig": {
            "temperature": 0.9,
            "maxOutputTokens": 8192,
            "topK": 40,
            "topP": 0.95
        }
    }

try:
    article = generate_text(system_prompt, user_prompt, article_generation_model, article_generation_config)
except Exception as e:
    raise Exception(f"An error occurred while generating the article: {e}")




system_prompt, _ = get_prompt("81512")
system_prompt = system_prompt.replace("[PASTE THE FULL ARTICLE TEXT HERE]", article)
title = check_article_title(article)
today = datetime.now()
today_string = today.strftime("%Y-%m-%d")
author = "Gemini"

metadata_model = "gemini-2.0-flash-lite"
metadata_config = {"generationConfig": {
            "temperature": 0.5,
            "maxOutputTokens": 1024,
            "response_mime_type": "application/json"
        }
    }

max_retries = 2
parsed_json = None
for attempt in range(max_retries):
    try:
        print(f"Attempt {attempt + 1} of {max_retries} to get SEO metadata...")
        raw_response_text = generate_text(system_prompt, "", metadata_model, metadata_config)
        parsed_json = json.loads(raw_response_text)
    except json.JSONDecodeError as e:
        print(f"Warning: Failed to decode JSON: {e}")
    except Exception as e:
        print(f"Warning: An error occurred while generating the description and tags: {e}")
    else:
        break

if "description" not in parsed_json and "tags" not in parsed_json:
    raise RuntimeError(f"Failed to get a valid JSON response after {max_retries} attempts.")

yaml_formatter = format_yaml(title, parsed_json, today_string, author)
final_output = f"{yaml_formatter}\n\n{article}"




today_ts = int(today.timestamp())  # use timestamp as a unique identifier
filename = f"{today_ts}.md"
output_dir = "output"
os.makedirs(output_dir, exist_ok = True)
file_path = os.path.join(output_dir, filename)

with open(file_path, "w", encoding = "utf-8") as f:
    f.write(final_output)
print(f"Article has been saved to {filename}")


# # Upload to Hugo Repo



def run_command(command, working_dir):

    result = subprocess.run(command, cwd = working_dir, capture_output = True, text = True, check = True)

    return result

def publish_article_to_hugo_repo(final_md_content, file_slug, hugo_repo_url, clone_path):

    try:
        if os.path.exists(clone_path):
            run_command(["git", "pull"], working_dir = clone_path)
        else:
            run_command(["git", "clone", hugo_repo_url, clone_path], working_dir = ".")

        filename = f"{file_slug}.md"
        destination_path = os.path.join(clone_path, "content", "posts", filename)

        with open(destination_path, "w", encoding = "utf-8") as f:
            f.write(final_md_content)

        run_command(["git", "add", "."], working_dir = clone_path)
        commit_message = f"add new article {file_slug}"
        run_command(["git", "commit", "-m", commit_message], working_dir = clone_path)
        run_command(["git", "push"], working_dir = clone_path)
    except (subprocess.CalledProcessError, FileNotFoundError) as e:
        print(f"\nERROR: An error occurred during the publishing process.")
        print(e)
    except Exception as e:
        print(f"\nAn unexpected error occurred: {e}")

def notebook_to_py():
    subprocess.run(["bash", "notebook_to_py.sh"], check = True)




title = check_article_title(article)
file_slug = title.lower().replace(' ', '-')

try:
    # publish_article_to_hugo_repo(final_output, file_slug, HUGO_REPO_URL, PATH)
    publish_article_to_hugo_repo(article, file_slug, HUGO_REPO_URL, PATH)
except Exception as e:
    raise Exception(f"Pipeline failed: {e}")

notebook_to_py()


# # generate image based on the heading
# code and prompt to be written later



# To run this code you need to install the following dependencies:
# pip install google-genai

from google import genai
import os

def generate():
    client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))

    result = client.models.generate_images(
        model="models/imagen-4.0-generate-preview-06-06",
        prompt="""INSERT_INPUT_HERE""",
        config=dict(
            number_of_images=1,
            output_mime_type="image/jpeg",
            person_generation="ALLOW_ADULT",
            aspect_ratio="1:1",
        ),
    )

    if not result.generated_images:
        print("No images generated.")
        return

    if len(result.generated_images) != 1:
        print("Number of images generated does not match the requested number.")

    for n, generated_image in enumerate(result.generated_images):
        generated_image.image.save(f"generated_image_{n}.jpg")


if __name__ == "__main__":
    generate()


# # tweak prompt to share knowledge, not just tips

# # develop later
# 
# logging: message to save warnings and erros

# # Testing



output_dir = "output"
file_path = os.path.join(output_dir, "1755120699.md")

with open(file_path, "r", encoding = "utf-8") as r:
    article = r.read()

print(article)






