# AI-Powered Content Generation Pipeline
[View the interactive workflow diagram here](https://honcyeung.github.io/Article-Generator-with-LLM/)

This project is a fully automated content pipeline that uses a Large Language Model (LLM) to generate, format, and publish high-quality blog articles to a live website.

The system is designed to autonomously select a creative topic, write an in-depth article, generate SEO-optimized metadata, and push the final, publish-ready Markdown file to a Git repository, which then triggers a live deployment.

## Key Features

  - **AI-Powered Article Generation:** Leverages the Gemini API to create unique, well-structured, and engaging blog posts on a wide range of topics.
  - **Automated SEO Metadata:** Intelligently generates SEO-friendly descriptions and relevant tags for each article to improve search visibility and content organization.
  - **Dynamic Frontmatter Generation:** Automatically creates perfectly formatted YAML frontmatter for seamless integration with static site generators like Hugo.
  - **End-to-End Automation:** The entire workflow, from content creation to publishing, is handled by a single Python script.
  - **Git-Based Deployment:** Pushes the final Markdown file to a Hugo repository, which can be connected to a hosting service like Vercel for automatic builds and deployments.

## Technology Stack

  - **Content Generation:** Google Gemini API (via Python `requests`)
  - **Prompt Management:** PromptLayer API
  - **Scripting:** Python (in a Jupyter Notebook `main.ipynb`)
  - **Static Site Generator:** Hugo (in a separate repository)
  - **Hosting:** Vercel (triggered by `git push`)
  - **Dependencies:** `requests`, `PyYAML`, `python-dotenv`

## Automated Workflow

The diagram below illustrates the end-to-end process, from running the script to the final deployment on the live website.

```
+---------------------+      +-------------------+      +------------------------+
|   Python Script     |----->|    Gemini API     |----->|  Generated Article     |
| (article-generator) |      | (Content & SEO)   |      | (.md with Frontmatter) |
+---------------------+      +-------------------+      +------------------------+
         |
         | (git push)
         V
+---------------------+      +-------------------+      +----------------------+
|  Hugo GitHub Repo   |----->|      Vercel       |----->|     Live Website     |
|    (my-hugo-blog)   |      | (Build & Deploy)  |      | (Future Development) |
+---------------------+      +-------------------+      +----------------------+

```

## How It Works

1.  **Prompt Retrieval:** The script fetches a highly-engineered prompt template from the PromptLayer API.
2.  **Article Generation:** It sends the prompt to the Gemini API, which selects a creative topic and writes a complete, formatted blog post in Markdown.
3.  **SEO Metadata Generation:** The generated article text is then sent back to the Gemini API with a second prompt, asking it to return an SEO-optimized description and a list of relevant tags in a clean JSON format.
4.  **Frontmatter Creation:** The script combines the title, description, and tags with other metadata (like the date and author) and uses the `PyYAML` library to generate a safe and valid YAML frontmatter block.
5.  **File Assembly:** The YAML frontmatter is prepended to the article's Markdown body, creating a single, publish-ready `.md` file.
6.  **Local Save:** The final file is saved locally in an `output/` directory for review.
7.  **Publishing:** The script can be configured to automatically place the new `.md` file into a local clone of a Hugo site's repository and run `git add`, `git commit`, and `git push` to publish the article.
