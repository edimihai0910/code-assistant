# 🤖 Code Assistant — AI-powered Codebase Explorer

A local AI assistant that reads your entire codebase and helps you understand it through natural language questions. Everything runs **100% locally** — no code leaves your machine.

---

## 🎯 What does it do?

- **Indexes** your entire codebase into a local vector database
- **Answers questions** about the project: architecture, data flow, classes, dependencies
- **Detects changes** when you pull new code and explains what's different
- **Two smart modes**: overview questions (big picture) vs. specific questions (single file/class)

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
├── ingest.py              # 🔨 Initial full indexing of codebase
├── update.py              # 🔄 Incremental smart update
├── query.py               # 💬 Interactive Q&A interface
├── requirements.txt       # Python dependencies
└── README.md              # This file
```

---

## 🔧 Configuration

Before running, edit the **codebase path** in `ingest.py` and `query.py`:

```python
CODEBASE_PATH = r"C:\path\to\your\project"  # ← change this
```

> 💡 Use `r"..."` (raw string) on Windows to avoid backslash issues.

If your project uses a different language than .NET/C#, adjust the file extensions in `INCLUDE_EXTENSIONS`:

```python
INCLUDE_EXTENSIONS = {
    # .NET / C#
    ".cs", ".cshtml", ".razor", ".xaml",
    ".csproj", ".sln", ".props", ".targets",
    # Config
    ".json", ".xml", ".yaml", ".yml", ".config",
    # Database
    ".sql",
    # Frontend
    ".js", ".ts", ".jsx", ".tsx", ".css", ".html",
    # Docs
    ".md", ".txt", ".rst",
}
```

If you chose a different model than `qwen2.5-coder:14b`, update it in `query.py`:

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
📂 Scanning files...
✅ Found 47 relevant files
✅ Loaded 46 files (1 skipped due to errors)
✅ Split into 230 chunks
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
❓ You: How does the RabbitMQ message flow work, step by step?
❓ You: What design patterns are used in this project?
❓ You: What does AlertPopupForm do and who calls it?
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

## 💡 Tips for Best Results

### Good questions to start with

| Goal | Question |
|---|---|
| Big picture | *"Explain the project structure, architecture, and main components"* |
| Tech stack | *"What frameworks, libraries, and NuGet packages are used?"* |
| Entry point | *"How does the application start? Trace from Program.cs"* |
| Data flow | *"How does a message flow from RabbitMQ to the UI? Include method names"* |
| Specific class | *"What does RabbitMQService do? List all its public methods and events"* |
| Dependencies | *"What depends on AudioService? Who calls its methods?"* |
| Patterns | *"What design patterns are used? Give examples with file names"* |
| Testing | *"How is the project tested? What test frameworks are used?"* |

### Pro tips

- **Be specific** — *"What does method X in class Y do?"* works better than *"explain the code"*
- **Ask follow-ups** — dig deeper into anything interesting
- **Ask for diagrams** — *"Generate a Mermaid diagram of the architecture"*
- **Reference files** — *"Explain RabbitMQService.cs line by line"*

---

## 🔄 Re-indexing

| Situation | What to do |
|---|---|
| Pulled a few new files | `python update.py` |
| Major refactor or branch switch | Delete `chroma_db/` folder, then `python ingest.py` |
| Changed indexing settings | Delete `chroma_db/` folder, then `python ingest.py` |
| Something feels off | Delete `chroma_db/` and `index_state.json`, then `python ingest.py` |

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
| Model download stuck | Re-run `ollama pull <model>` — it resumes |
| Empty/vague answers | Delete `chroma_db/`, re-run `python ingest.py` |
| Very slow responses | Check `ollama ps` for GPU usage; try a smaller model |
| `SyntaxWarning: invalid escape sequence` | Use raw strings: `r"C:\path\to\project"` |
| PowerShell ExecutionPolicy error | `Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser` |
| `Connection refused` on Ollama | Make sure Ollama is running: `ollama serve` |

---

## 📦 Dependencies Reference

| Package | Purpose |
|---|---|
| `langchain` | AI application framework |
| `langchain-core` | Core abstractions (prompts, chains) |
| `langchain-community` | Community integrations (file loaders) |
| `langchain-ollama` | Ollama integration (local LLM + embeddings) |
| `langchain-chroma` | ChromaDB vector store integration |
| `langchain-text-splitters` | Intelligent code/text chunking |
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

1. **Ingest**: Code files are split into chunks and converted to vectors (embeddings)
2. **Query**: Your question is also converted to a vector
3. **Search**: The most similar code chunks are retrieved from the vector DB
4. **Answer**: The LLM reads those chunks + your question and generates an answer

---

`
