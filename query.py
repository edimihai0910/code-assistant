import os
from pathlib import Path
from langchain_ollama import OllamaLLM, OllamaEmbeddings
from langchain_chroma import Chroma
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser

DB_PATH = "./chroma_db"
CODEBASE_PATH = r"C:\Cabis\Hungary\HIFS Mid Alarm"

EXCLUDE_DIRS = {
    "bin", "obj", "node_modules", ".git", ".vs", ".vscode",
    "packages", "TestResults", "Debug", "Release", ".nuget"
}

# ─────────────────────────────────────────────
# 1. Generează o hartă a proiectului (tree)
# ─────────────────────────────────────────────
def generate_project_map(codebase_path, max_depth=4):
    """Creează un tree text al proiectului — foldere + fișiere."""
    lines = []
    base = Path(codebase_path)
    
    for root, dirs, files in os.walk(codebase_path):
        dirs[:] = sorted([d for d in dirs if d not in EXCLUDE_DIRS])
        rel = Path(root).relative_to(base)
        depth = len(rel.parts)
        
        if depth > max_depth:
            continue
        
        indent = "  " * depth
        folder_name = rel.name if rel.name else base.name
        lines.append(f"{indent}📁 {folder_name}/")
        
        for f in sorted(files):
            ext = Path(f).suffix.lower()
            if ext in {".cs", ".cshtml", ".razor", ".xaml", ".csproj", ".sln",
                       ".json", ".xml", ".yaml", ".yml", ".config", ".sql",
                       ".js", ".ts", ".css", ".html", ".md"}:
                lines.append(f"{indent}  📄 {f}")
    
    return "\n".join(lines)

# ─────────────────────────────────────────────
# 2. Extrage un rezumat din fișierele cheie
# ─────────────────────────────────────────────
def extract_key_files_summary(codebase_path, max_chars=3000):
    """Citește primele N linii din fișierele cheie (.csproj, Program.cs, etc.)."""
    key_patterns = [
        "*.sln", "*.csproj", "Program.cs", "Startup.cs", "App.xaml.cs",
        "appsettings.json", "App.config", "Web.config",
        "README.md", "readme.md"
    ]
    
    summaries = []
    base = Path(codebase_path)
    
    for pattern in key_patterns:
        for fpath in base.rglob(pattern):
            # Skip excluded dirs
            if any(ex in fpath.parts for ex in EXCLUDE_DIRS):
                continue
            try:
                content = fpath.read_text(encoding="utf-8", errors="ignore")
                rel = fpath.relative_to(base)
                # Primele 80 linii sau max_chars
                truncated = "\n".join(content.splitlines()[:80])[:max_chars]
                summaries.append(f"--- {rel} ---\n{truncated}")
            except Exception:
                pass
    
    return "\n\n".join(summaries)[:12000]

# ─────────────────────────────────────────────
# 3. Setup vector store + LLM
# ─────────────────────────────────────────────
embeddings = OllamaEmbeddings(model="nomic-embed-text")
vectorstore = Chroma(persist_directory=DB_PATH, embedding_function=embeddings)
retriever = vectorstore.as_retriever(search_kwargs={"k": 22})  # mai multe chunks

llm = OllamaLLM(
    model="qwen2.5-coder:14b",
    temperature=0.1,
    num_ctx=32768
)

# ─────────────────────────────────────────────
# 4. Două moduri de prompt: overview vs. specific
# ─────────────────────────────────────────────

# Prompt pentru întrebări GENERALE (overview, structură, "ce face proiectul")
overview_template = """You are a senior .NET developer analyzing a codebase for the first time.
You have access to the complete project structure and key configuration files, 
plus relevant code snippets.

Be SPECIFIC and CONCRETE:
- Name actual classes, namespaces, files, and folders
- Describe actual data flow with real class/method names
- Identify the tech stack, frameworks, NuGet packages
- Explain the architecture pattern used (MVC, MVVM, layered, etc.)
- List the main entry points and how the app starts
- Describe inter-component communication (events, messaging, DI, etc.)

PROJECT STRUCTURE:
{project_map}

KEY FILES (csproj, config, Program.cs, etc.):
{key_files}

ADDITIONAL CODE SNIPPETS:
{context}

Question: {question}

Provide a thorough, concrete answer with real names from the codebase:"""

# Prompt pentru întrebări SPECIFICE (despre un fișier, o clasă, o funcție)
specific_template = """You are a senior .NET developer analyzing a codebase.
Use the following code snippets to answer the question precisely.
Always reference actual file names, class names, method names.
If you don't know, say so — don't make things up.

Code context:
{context}

Question: {question}

Answer:"""

overview_prompt = ChatPromptTemplate.from_template(overview_template)
specific_prompt = ChatPromptTemplate.from_template(specific_template)

# ─────────────────────────────────────────────
# 5. Helpers
# ─────────────────────────────────────────────
def format_docs(docs):
    formatted = []
    seen = set()
    for doc in docs:
        source = doc.metadata.get("source", "unknown")
        rel_path = os.path.relpath(source, CODEBASE_PATH)
        # Evită duplicatele
        key = (rel_path, doc.page_content[:100])
        if key in seen:
            continue
        seen.add(key)
        formatted.append(f"--- {rel_path} ---\n{doc.page_content}")
    return "\n\n".join(formatted)

def is_overview_question(question):
    """Detectează dacă întrebarea e despre proiect în general."""
    overview_keywords = [
        "project", "overview", "structure", "scope", "architecture",
        "explain the", "what does this", "how does this project",
        "first time", "understand", "learn", "big picture",
        "what is this", "describe the", "how is it organized",
        "entry point", "main components", "tech stack",
        "proiect", "structur", "arhitectur", "scopul",
    ]
    q_lower = question.lower()
    return any(kw in q_lower for kw in overview_keywords)

# Pre-generează harta proiectului (o singură dată)
print("📂 Generating project map...")
PROJECT_MAP = generate_project_map(CODEBASE_PATH)
KEY_FILES = extract_key_files_summary(CODEBASE_PATH)
print(f"✅ Project map ready ({PROJECT_MAP.count(chr(10))+1} entries)")

# ─────────────────────────────────────────────
# 6. Loop interactiv
# ─────────────────────────────────────────────
print("\n🤖 Code Assistant ready! (type 'exit' to quit)")
print("   💡 Tip: ask 'overview' questions or specific ones — I adapt!\n")

while True:
    question = input("❓ You: ")
    if question.lower().strip() in ("exit", "quit", "q"):
        break

    print("\n🔍 Searching codebase...\n")

    # Decide modul
    if is_overview_question(question):
        # MOD OVERVIEW — dă-i toată structura + key files + chunks
        source_docs = retriever.invoke(question)
        context = format_docs(source_docs)
        
        answer = (
            overview_prompt 
            | llm 
            | StrOutputParser()
        ).invoke({
            "project_map": PROJECT_MAP,
            "key_files": KEY_FILES,
            "context": context,
            "question": question
        })
    else:
        # MOD SPECIFIC — doar chunks relevante
        source_docs = retriever.invoke(question)
        context = format_docs(source_docs)
        
        answer = (
            specific_prompt 
            | llm 
            | StrOutputParser()
        ).invoke({
            "context": context,
            "question": question
        })

    print(f"💬 {answer}")

    # Afișează sursele
    sources = set()
    for doc in source_docs:
        src = os.path.relpath(doc.metadata.get("source", "?"), CODEBASE_PATH)
        sources.add(src)
    print(f"\n📎 Sources ({len(sources)} files): {', '.join(sorted(sources))}\n")