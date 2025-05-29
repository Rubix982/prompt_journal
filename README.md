# 📝 Prompt Journal

**Prompt Journal** is a command-line tool to help you **log, tag, and organize your AI prompts and notes** with clean YAML metadata, Git versioning, and optional fuzzy search for tag discovery — all stored locally in your `~/.prompt-journal` folder.

Perfect for developers, researchers, and tinkerers who regularly experiment with LLMs and want to **track prompt results, notes, models used, and feedback** over time.

---

## 📦 Features

- 📂 Creates structured folders by date
- 🧠 YAML front matter for each prompt & response
- 🧪 Tracks:

  - models used (ChatGPT, Claude, Gemini, etc.)
  - quality of the response
  - follow-up questions
  - experiment notes

- 🏷️ Tagging with history & fuzzy search
- 💬 Quick notes with minimal metadata
- 🔐 Optional private flag
- 🕵️ Inject metadata into existing `.md` files
- ✅ Git auto-commit for version history

---

## 🚀 Getting Started

### 1. Clone the Repo

```bash
git clone https://github.com/your-username/prompt-journal
cd prompt-journal
```

### 2. Install with Poetry

```bash
poetry install
poetry shell
```

Or install dependencies manually:

```bash
pip install -r requirements.txt
```

---

## ⚙️ Usage

### Create a new prompt

```bash
python prompt_journal.py new
```

### Create a quick note

```bash
python prompt_journal.py note
```

### List all prompt entries

```bash
python prompt_journal.py list
```

### Search by exact tag

```bash
python prompt_journal.py search <tag>
```

### Fuzzy search for a tag

```bash
python prompt_journal.py fuzzysearch <approx-tag>
```

### Inject metadata into an existing file

```bash
python prompt_journal.py inject path/to/file.prompt.md
```

---

## 🗂 Directory Structure

All journal files are stored under `~/.prompt-journal/`, organized as:

```
~/.prompt-journal/
└── 2025/
    └── 05/
        ├── experiment.prompt.md
        └── experiment.response.md
```

Each `.prompt.md` and `.note.md` file contains YAML front matter and user content.

---

## 🧩 Dependencies

- [Python 3.8+](https://www.python.org)
- [questionary](https://github.com/tmbo/questionary)
- [PyYAML](https://github.com/yaml/pyyaml)
- [thefuzz](https://github.com/seatgeek/thefuzz) (optional, for fuzzy tag search)
- Git (used for version tracking)

Install extras:

```bash
pip install "thefuzz[speedup]"
```

---

## 🌱 Roadmap Ideas

- [ ] Export prompts to CSV or JSON
- [ ] GUI or TUI version
- [ ] Cloud sync support
- [ ] Tag/Prompt graph visualization

---

## 🤝 Contributing

Feel free to fork, star, and open issues or PRs. This is a passion project to make LLM experimentation more **reproducible, searchable, and meaningful**.

---

## 📜 License

MIT License. Do whatever you like, but give credit if it helps you!
