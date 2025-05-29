#!/usr/bin/env python3
import os
import yaml
import subprocess
import argparse
from datetime import datetime
from pathlib import Path
import re
import questionary

try:
    from thefuzz import process
except ImportError:
    print("⚠️  'thefuzz' library not found. Install with: pip install 'thefuzz[speedup]'")
    process = None

# Define the base directory for the journal
HOME_DIR = Path.home() / ".prompt-journal"
DEFAULT_FIELDS = {
    "title": "",
    "date": "",
    "tags": [],
    "models": [],
    "experiment_notes": "",
    "follow_ups": [],
    "source": "",
    "response_quality": "",
    "version": "v1",
    "private": False,
    "related_prompts": []
}

ENUM_OPTIONS = {
    "models": ["chatgpt-4", "claude-3", "gemini", "mistral"],
    "response_quality": ["excellent", "good", "okay", "poor"],
    "source": ["chatgpt", "claude", "gemini"]
}

ORDINAL_SUFFIXES = {1: 'st', 2: 'nd', 3: 'rd'}

def format_human_date():
    now = datetime.now()
    day = now.day
    suffix = ORDINAL_SUFFIXES.get(day if day < 20 else day % 10, 'th')
    return now.strftime(f"%-d{suffix} %B, %Y")

def snake_to_title(s):
    return ' '.join(word.capitalize() for word in s.split('_'))

def ensure_home():
    HOME_DIR.mkdir(exist_ok=True)
    os.chdir(HOME_DIR)
    if not (HOME_DIR / ".git").exists():
        subprocess.run(["git", "init"])
        print("✅ Initialized Git repository")

def create_today_folder():
    today = datetime.today()
    folder_path = HOME_DIR / today.strftime("%Y") / today.strftime("%m")
    folder_path.mkdir(parents=True, exist_ok=True)
    print(f"📁 Folder: {folder_path.relative_to(HOME_DIR)}")
    return folder_path

def collect_existing_tags():
    tag_set = set()
    for md_file in HOME_DIR.rglob("*.md"):
        with open(md_file, encoding="utf-8") as f:
            content = f.read()
            if content.startswith("---"):
                end = content.find("---", 3)
                if end != -1:
                    front_matter = yaml.safe_load(content[3:end])
                    tag_set.update(front_matter.get("tags", []))
    return sorted(tag_set)

def write_note(folder):
    filename = questionary.text("Note filename (snake_case, no extension)").ask()
    title = snake_to_title(filename)
    tags_existing = collect_existing_tags()
    tag_choices = questionary.checkbox("Select tags (or leave empty)", choices=tags_existing).ask()
    tag_custom = questionary.text("Additional tags (comma-separated)").ask()
    if tag_custom:
        tag_choices += [t.strip() for t in tag_custom.split(",") if t.strip()]

    note_content = questionary.text("Write your note:").ask()
    note_path = folder / f"{filename}.note.md"

    metadata = {
        "title": title,
        "date": format_human_date(),
        "tags": sorted(set(tag_choices))
    }

    yaml_block = yaml.dump(metadata, sort_keys=False)
    full_content = f"---\n{yaml_block}---\n\n# {title}\n\n{note_content}\n"
    note_path.write_text(full_content, encoding="utf-8")
    print(f"📝 Note saved to {note_path.relative_to(HOME_DIR)}")

    subprocess.run(["git", "add", str(note_path)])
    subprocess.run(["git", "commit", "-m", f"Add note: {title}"])

def prompt_for_metadata(default_title):
    metadata = {}
    metadata["title"] = questionary.text("Title", default=snake_to_title(default_title)).ask()
    metadata["date"] = format_human_date()

    existing_tags = collect_existing_tags()
    selected_tags = questionary.checkbox("Select tags (or enter custom)", choices=existing_tags).ask()
    custom_tags = questionary.text("Any custom tags to add? (comma-separated)").ask()
    if custom_tags:
        selected_tags.extend([t.strip() for t in custom_tags.split(",") if t.strip()])
    metadata["tags"] = sorted(set(selected_tags))

    metadata["models"] = questionary.checkbox("Select models used", choices=ENUM_OPTIONS["models"]).ask()
    metadata["experiment_notes"] = questionary.text("Any experiment notes or context?").ask()
    metadata["follow_ups"] = [i.strip() for i in questionary.text("Follow-up prompts? (comma-separated)").ask().split(",") if i.strip()]
    metadata["source"] = questionary.select("Which LLM replied?", choices=ENUM_OPTIONS["source"]).ask()
    metadata["response_quality"] = questionary.select("Rate the quality of the response", choices=ENUM_OPTIONS["response_quality"]).ask()
    metadata["version"] = "v1"
    metadata["private"] = questionary.confirm("Should this prompt be private?", default=False).ask()
    metadata["related_prompts"] = [i.strip() for i in questionary.text("Related prompts? (comma-separated)").ask().split(",") if i.strip()]
    return metadata

def write_metadata_to_md(filepath, metadata):
    contents = filepath.read_text(encoding="utf-8") if filepath.exists() else ""
    if contents.startswith("---"):
        print("⚠️ YAML metadata already exists. Skipping insertion.")
        return

    yaml_block = yaml.dump(metadata, sort_keys=False)
    new_contents = f"---\n{yaml_block}---\n\n{contents}"
    filepath.write_text(new_contents, encoding="utf-8")
    print(f"✅ Metadata written to {filepath.relative_to(HOME_DIR)}")

    subprocess.run(["git", "add", str(filepath)])
    subprocess.run(["git", "commit", "-m", f"Add prompt: {metadata['title']}"])

def write_response_file(filepath, metadata):
    response_path = filepath.with_suffix(".response.md")
    partial_metadata = {
        "models": metadata.get("models"),
        "source": metadata.get("source"),
        "response_quality": metadata.get("response_quality"),
        "date": metadata.get("date"),
    }
    yaml_block = yaml.dump(partial_metadata, sort_keys=False)
    new_contents = f"---\n{yaml_block}---\n\n"
    response_path.write_text(new_contents, encoding="utf-8")
    print(f"✅ Response metadata written to {response_path.relative_to(HOME_DIR)}")

    subprocess.run(["git", "add", str(response_path)])
    subprocess.run(["git", "commit", "-m", f"Add response file for: {metadata['title']}"])

def list_by_date():
    for year_dir in sorted(HOME_DIR.glob("*/")):
        for month_dir in sorted(year_dir.glob("*/")):
            print(f"\n📅 {month_dir.relative_to(HOME_DIR)}")
            for file in month_dir.glob("*.prompt.md"):
                print(f"  - {file.name}")

def search_by_tag(tag):
    print(f"🔍 Searching for tag: {tag}\n")
    for md_file in HOME_DIR.rglob("*.prompt.md"):
        with open(md_file, encoding="utf-8") as f:
            content = f.read()
            if content.startswith("---"):
                end = content.find("---", 3)
                if end != -1:
                    front_matter = yaml.safe_load(content[3:end])
                    tags = front_matter.get("tags", [])
                    if tag in tags:
                        print(f"✅ {md_file.relative_to(HOME_DIR)}: {front_matter.get('title')}")

def fuzzy_search_tag(input_tag):
    if not process:
        print("❌ Fuzzy search requires 'thefuzz'. Run: pip install 'thefuzz[speedup]'")
        return

    tag_map = {}
    for md_file in HOME_DIR.rglob("*.prompt.md"):
        with open(md_file, encoding="utf-8") as f:
            content = f.read()
            if content.startswith("---"):
                end = content.find("---", 3)
                if end != -1:
                    front_matter = yaml.safe_load(content[3:end])
                    tags = front_matter.get("tags", [])
                    for tag in tags:
                        tag_map.setdefault(tag, []).append((md_file, front_matter.get("title")))

    all_tags = list(tag_map.keys())
    matches = process.extract(input_tag, all_tags, limit=5)

    for match, score in matches:
        print(f"🔎 Tag: {match} (score {score})")
        for file, title in tag_map[match]:
            print(f"   ✅ {file.relative_to(HOME_DIR)}: {title}")

def inject_metadata_to_file(filepath):
    path = Path(filepath).expanduser().resolve()
    if not path.exists() or not path.is_file():
        print(f"❌ File not found: {path}")
        return
    default_title = path.stem.replace(".prompt", "")
    metadata = prompt_for_metadata(default_title)
    write_metadata_to_md(path, metadata)

def main():
    parser = argparse.ArgumentParser(description="Prompt Journal CLI")
    subparsers = parser.add_subparsers(dest="command")

    subparsers.add_parser("new", help="Create new prompt entry")
    subparsers.add_parser("note", help="Quick note with minimal metadata")
    subparsers.add_parser("list", help="List entries by date")

    search_parser = subparsers.add_parser("search", help="Search prompts by tag")
    search_parser.add_argument("tag", help="Tag to search")

    fuzzy_parser = subparsers.add_parser("fuzzysearch", help="Fuzzy search prompts by approximate tag")
    fuzzy_parser.add_argument("tag", help="Approximate tag to search")

    inject_parser = subparsers.add_parser("inject", help="Inject metadata into an existing markdown file")
    inject_parser.add_argument("filepath", help="Path to the Markdown file")

    args = parser.parse_args()
    ensure_home()

    if args.command == "new":
        folder = create_today_folder()
        filename = questionary.text("Filename (no extension)").ask()
        prompt_path = folder / f"{filename}.prompt.md"
        if not prompt_path.exists():
            prompt_path.touch()
            print(f"📄 Created {prompt_path.relative_to(HOME_DIR)}")
        metadata = prompt_for_metadata(filename)
        write_metadata_to_md(prompt_path, metadata)
        write_response_file(prompt_path, metadata)

    elif args.command == "note":
        folder = create_today_folder()
        write_note(folder)

    elif args.command == "list":
        list_by_date()

    elif args.command == "search":
        search_by_tag(args.tag)

    elif args.command == "fuzzysearch":
        fuzzy_search_tag(args.tag)

    elif args.command == "inject":
        inject_metadata_to_file(args.filepath)

    else:
        parser.print_help()

if __name__ == "__main__":
    main()

