# 🤖 Code Assistant — AI-powered Codebase Explorer

A local AI assistant that reads your entire codebase and helps you understand it through natural language questions. Everything runs **100% locally** — no code leaves your machine.

Supports **Java**, **.NET/C#**, and **Python** projects with automatic language detection.

---

## 🎯 What does it do?

- **Indexes** your entire codebase into a local vector database
- **Answers questions** about the project: architecture, data flow, classes, dependencies
- **Detects changes** when you pull new code and explains what's different
- **Two smart modes**: overview questions (big picture) vs. specific questions (single file/class)
- **Language-aware chunking**: understands Java/C#/Python code structure for better accuracy

---

## 📋 Prerequisites

| Requirement | Minimum | Recommended |
|---|---|---|
| **Python** | 3.10+ | 3.11 or 3.12 |
| **RAM** | 16 GB | 32 GB |
| **Disk space** | ~10 GB (for models) | ~15 GB |
| **GPU** | Not required | NVIDIA GPU with 8+ GB VRAM (much faster) |
| **OS** | Windows 10/11, Linux, macOS | — |

---

## 🚀 Installation — Step by Step

### 1. Install Ollama (local AI runtime)

Ollama runs AI models locally on your machine.

- **Windows**: Download the installer from [https://ollama.com/download](https://ollama.com/download) and run it.
- **Linux/macOS**:
  ```bash
  curl -fsSL https://ollama.com/install.sh | sh
  ```

Verify installation:
```bash
ollama --version
```

### 2. Download AI models

Open a terminal and run:

```bash
# Embedding model (required — converts code to searchable vectors) ~274 MB
ollama pull nomic-embed-text

# Code LLM (the "brain" that answers your questions)
# Choose ONE based on your RAM:

# 8 GB RAM → small model (~2 GB)
ollama pull qwen2.5-coder:3b

# 16 GB RAM → good balance (~4.5 GB)
ollama pull qwen2.5-coder:7b

# 32 GB RAM → best quality (~8.9 GB) ✅ RECOMMENDED
ollama pull qwen2.5-coder:14b
```

Verify models are downloaded:
```bash
ollama list
```

You should see both `nomic-embed-text` and your chosen `qwen2.5-coder` model listed.

### 3. Set up the Python environment

```bash
# Navigate to this project folder
cd path\to\code-assistant

# Create a virtual environment (isolated Python packages)
python -m venv venv

# Activate it
# Windows CMD:
.\venv\Scripts\activate.bat
# Windows PowerShell:
.\venv\Scripts\Activate.ps1
# Linux/macOS:
source venv/bin/activate

# You should see (venv) at the beginning of your terminal prompt
```

> ⚠️ **PowerShell users**: if you get an ExecutionPolicy error, run this first:
> ```powershell
> Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
> ```

### 4. Install Python dependencies

```bash
pip install langchain langchain-core langchain-community langchain-ollama langchain-chroma langchain-text-splitters chromadb sentence-transformers
```

---

## 📁 Project Structure

```
code-assistant/
├── venv/                  # Python virtual environment (auto-generated)
├── chroma_db/             # Vector database (auto-generated after ingest)
├── changelogs/            # Update history (auto-generated after updates)
├── index_state.json       # File tracking state (auto-generated)
├── config.py              # Language profiles (Java, .NET, Python)
├── ingest.py              # 🔨 Initial full indexing of codebase
├── update.py              # 🔄 Incremental smart update
├── query.py               # 💬 Interactive Q&A interface
└── README.md              # This file
```

---

## 🔧 Configuration

### Point to your codebase

Open **`ingest.py`** AND **`query.py`** and change the path at the top:

```python
CODEBASE_PATH = r"C:\path\to\your\project"  # ← change this
```

> 💡 Use `r"..."` (raw string) on Windows to avoid backslash issues.

### Language profile (auto-detected)

The assistant auto-detects your project type based on build files:

| Detected language | Triggered by these files |
|---|---|
| **Java** | `pom.xml`, `build.gradle`, `build.gradle.kts` |
| **.NET / C#** | `*.sln`, `*.csproj` |
| **Python** | `pyproject.toml`, `setup.py`, `requirements.txt` |

To force a specific profile, set `PROFILE_OVERRIDE` in both `ingest.py` and `query.py`:

```python
PROFILE_OVERRIDE = "java"   # or "dotnet" or "python"  (None = auto-detect)
```

### Change the LLM model (optional)

In `query.py`, if you chose a different model:

```python
llm = OllamaLLM(
    model="qwen2.5-coder:14b",  # ← change to your model
    ...
)
```

---

## 📖 Usage

### First time: Index the codebase

```bash
# Make sure venv is activated!
.\venv\Scripts\activate.bat

# Index the entire codebase (run once)
python ingest.py
```

Expected output:
```
✅ Auto-detected profile: java
📂 Scanning files (profile: java)...
✅ Found 247 relevant files
✅ Loaded 245 files (2 skipped due to errors)
✅ Split into 1823 chunks (language: java)
🔢 Creating embeddings (this may take a while)...
✅ Done! Indexed in ./chroma_db
```

### Ask questions about the code

```bash
python query.py
```

```
🤖 Code Assistant ready! (type 'exit' to quit)

❓ You: Explain the project architecture and main components
❓ You: How does the HTTP request flow work, step by step?
❓ You: What design patterns are used in this project?
❓ You: What does UserService do and who calls it?
❓ You: exit
```

### After pulling new code: Incremental update

```bash
python update.py
```

```
🔍 Changes detected (batch: update_20260422_0900):
   ➕ 2 added
   ✏️  3 modified
   🗑️  0 deleted
✅ Done!
```

Then in `query.py` you can ask:
```
❓ You: What changed in the last update?
❓ You: Explain the new files that were added
```

---

## 🔄 Switching Between Projects

> ⚠️ **This is important!** The assistant keeps **one codebase indexed at a time**. When you switch projects, you MUST reset the index — otherwise you'll get mixed/wrong answers from both codebases.

### ✅ Clean switch procedure (always do all 4 steps)

```bash
# 1. Delete the old vector database
# Windows:
rmdir /s /q chroma_db
# Linux/macOS:
rm -rf chroma_db

# 2. Delete the update tracking state (so the new project starts fresh)
# Windows:
del index_state.json
# Linux/macOS:
rm -f index_state.json

# 3. (Optional) Delete old changelogs
# Windows:
rmdir /s /q changelogs
# Linux/macOS:
rm -rf changelogs

# 4. Update CODEBASE_PATH in ingest.py AND query.py
#    Then re-index:
python ingest.py
```

### One-liner for Windows PowerShell

```powershell
Remove-Item -Recurse -Force chroma_db, changelogs, index_state.json -ErrorAction SilentlyContinue
```

### One-liner for Linux/macOS

```bash
rm -rf chroma_db changelogs index_state.json
```

---

## 🧹 When You MUST Re-index (Delete `chroma_db/`)

| Situation | Action required |
|---|---|
| 🔀 **Switched to a different project** | Full reset (all 4 steps above) |
| 🔄 Pulled a few new files into the same project | Just run `python update.py` |
| 🏗️ Major refactor or branch switch (same project) | Delete `chroma_db/`, run `ingest.py` |
| ⚙️ Changed `INCLUDE_EXTENSIONS` or chunk settings | Delete `chroma_db/`, run `ingest.py` |
| 🤔 Answers feel wrong or mixed with old data | Full reset, then `ingest.py` |
| 🧠 Changed the embedding model in Ollama | Full reset, then `ingest.py` |
| 🎯 Changed `PROFILE_OVERRIDE` (e.g., Java → .NET) | Full reset, then `ingest.py` |

### What each auto-generated item contains

| File/Folder | Purpose | Safe to delete? |
|---|---|---|
| `chroma_db/` | Vector embeddings of your code | ✅ Yes — rebuilt by `ingest.py` |
| `index_state.json` | Tracks file modification times for incremental updates | ✅ Yes — rebuilt by `update.py` |
| `changelogs/` | Human-readable history of code changes | ✅ Yes — purely informational |
| `venv/` | Python packages | ⚠️ Only if you want to reinstall everything |

---

## 💡 Tips for Best Results

### Good questions to start with

| Goal | Question |
|---|---|
| Big picture | *"Explain the project structure, architecture, and main components"* |
| Tech stack | *"What frameworks and libraries are used? Check the build files"* |
| Entry point | *"How does the application start? Trace the initialization flow"* |
| Data flow | *"How does a request flow through the system? Include class and method names"* |
| Specific class | *"What does UserService do? List all its public methods"* |
| Dependencies | *"What depends on AuthService? Who calls its methods?"* |
| Patterns | *"What design patterns are used? Give examples with file names"* |
| Testing | *"How is the project tested? What test frameworks and patterns?"* |

### Pro tips

- **Be specific** — *"What does method X in class Y do?"* works better than *"explain the code"*
- **Ask follow-ups** — dig deeper into anything interesting
- **Ask for diagrams** — *"Generate a Mermaid diagram of the architecture"*
- **Reference files** — *"Explain UserService.java line by line"*

---

## ⚡ Performance

| Setup | Response time | Quality |
|---|---|---|
| CPU only, 3b model | 30–60 sec | Basic |
| CPU only, 14b model | 60–120 sec | Good |
| NVIDIA GPU, 7b model | 2–5 sec | Good |
| NVIDIA GPU, 14b model | 5–15 sec | ✅ Best |

### Check if GPU is being used

```bash
ollama ps
```

Look for `GPU` in the `PROCESSOR` column. If it says `CPU` and you have an NVIDIA GPU, make sure your NVIDIA drivers are up to date.

---

## 🐛 Troubleshooting

| Problem | Solution |
|---|---|
| `ModuleNotFoundError` | Make sure venv is activated: `.\venv\Scripts\activate.bat` |
| `ollama: command not found` | Restart terminal after installing Ollama |
| Model download stuck | Re-run `ollama pull <model>` — it resumes automatically |
| Empty/vague answers | Delete `chroma_db/`, re-run `python ingest.py` |
| **Answers mention files from an old project** | You forgot to reset when switching projects! See "Switching Between Projects" above |
| Very slow responses | Check `ollama ps` for GPU usage; try a smaller model |
| `SyntaxWarning: invalid escape sequence` | Use raw strings: `r"C:\path\to\project"` |
| PowerShell ExecutionPolicy error | `Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser` |
| `Connection refused` on Ollama | Make sure Ollama is running (check system tray on Windows) |
| Wrong language detected | Set `PROFILE_OVERRIDE = "java"` (or `"dotnet"` / `"python"`) manually |

---

## 📦 Dependencies Reference

| Package | Purpose |
|---|---|
| `langchain` | AI application framework |
| `langchain-core` | Core abstractions (prompts, chains) |
| `langchain-community` | Community integrations (file loaders) |
| `langchain-ollama` | Ollama integration (local LLM + embeddings) |
| `langchain-chroma` | ChromaDB vector store integration |
| `langchain-text-splitters` | Language-aware code chunking |
| `chromadb` | Local vector database |
| `sentence-transformers` | Embedding model support |

---

## 🧠 How it works (simplified)

```
┌─────────────┐     ┌──────────┐     ┌────────────┐
│  Your code  │────▶│ Chunking │────▶│ Embeddings │
│  (files)    │     │ (split)  │     │ (vectorize)│
└─────────────┘     └──────────┘     └─────┬──────┘
                                           │
                                           ▼
┌─────────────┐     ┌──────────┐     ┌────────────┐
│  Answer     │◀────│ LLM      │◀────│ Vector DB  │
│  (text)     │     │ (reason) │     │ (search)   │
└─────────────┘     └──────────┘     └─────┬──────┘
                                           ▲
                                           │
                                    ┌──────┴──────┐
                                    │ Your        │
                                    │ question    │
                                    └─────────────┘
```

1. **Ingest**: Code files are split into chunks (respecting code structure) and converted to vectors
2. **Query**: Your question is also converted to a vector
3. **Search**: The most similar code chunks are retrieved from the vector DB
4. **Answer**: The LLM reads those chunks + your question and generates an answer

---

## 📝 Quick Reference — Common Workflows

### Index a new project from scratch
```bash
.\venv\Scripts\activate.bat
# Update CODEBASE_PATH in ingest.py and query.py
python ingest.py
python query.py
```

### Switch from project A to project B
```bash
.\venv\Scripts\activate.bat
rmdir /s /q chroma_db
del index_state.json
rmdir /s /q changelogs
# Update CODEBASE_PATH in ingest.py and query.py
python ingest.py
python query.py
```

### Daily work — after `git pull`
```bash
.\venv\Scripts\activate.bat
python update.py
python query.py
```

### Something feels wrong — full reset
```bash
.\venv\Scripts\activate.bat
rmdir /s /q chroma_db changelogs
del index_state.json
python ingest.py
```

---

*Built with ❤️ using Ollama, LangChain, and ChromaDB — 100% local, 100% private.*
`
