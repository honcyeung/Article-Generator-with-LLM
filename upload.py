import subprocess
import os

def run_command(command, working_dir):

    result = subprocess.run(command, cwd = working_dir, capture_output = True, text = True, check = True)

    return result

def publish_article_to_hugo_repo(final_article_output, title, hugo_repo_url, clone_path):

    try:
        file_slug = title.lower().replace(' ', '-')
        filename = f"{file_slug}.md"
        destination_path = os.path.join(clone_path, "content", "posts", filename)

        with open(destination_path, "w", encoding = "utf-8") as f:
            f.write(final_article_output)

        run_command(["git", "add", "."], working_dir = clone_path)
        commit_message = f"add new article {file_slug}"
        run_command(["git", "commit", "-m", commit_message], working_dir = clone_path)
        run_command(["git", "push"], working_dir = clone_path)

        print("New article uploaded to Hugo repo.")
    except Exception as e:
        raise Exception(e)
