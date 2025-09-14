import generate
import upload

import os
from datetime import datetime
import json
import subprocess

from dotenv import load_dotenv
load_dotenv()

HUGO_REPO_URL = os.environ.get("HUGO_REPO_URL")
CLONE_PATH = os.environ.get("CLONE_PATH")
MODEL = "gemini-2.5-flash"
TEMPERATURE = 0.8

def main():

    final_article_output, title = generate.pipeline(MODEL, TEMPERATURE)
    upload.publish_article_to_hugo_repo(final_article_output, title, HUGO_REPO_URL, CLONE_PATH)

if __name__ == "__main__":
    main()
