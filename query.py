import os
from pathlib import Path
from langchain_ollama import OllamaLLM, OllamaEmbeddings
from langchain_chroma import Chroma
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser
from config import get_profile

# ─────────────────────────────────────────────
# CONFIG
# ─────────────────────────────────────────────
CODEBASE_PATH = r"C:\Cabis\Hungary\HIFS Mid Alarm"
DB_PATH = "./chroma_db"
PROFILE_OVERRIDE = None  # or "java" / "dotnet" / "python"

# ─────────────────────────────────────────────
profile_name, profile = get_profile(CODEBASE_PATH, PROFILE_OVERRIDE)
EXCLUDE_DIRS = profile["exclude_dirs"]
KEY_PATTERNS = profile["key_patterns"]
PROMPT_ROLE = profile["prompt_role"]
TECH_HINTS = profile["tech_hints"]

# ─────────────────────────────────────────────
# Project map (same as before)
# ─────────────────────────────────────────────
def generate_project_map(codebase_path, max_depth=4):
    lines = []
    base = Path(codebase_path)
    relevant_exts = profile["extensions"]
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
            if Path(f).suffix.lower() in relevant_exts:
                lines.append(f"{indent}  📄 {f}")
    return "\n".join(lines)

def extract_key_files_summary(codebase_path, max_chars=3000):
    summaries = []
    base = Path(codebase_path)
    for pattern in KEY_PATTERNS:
        for fpath in base.rglob(pattern):
            if any(ex in fpath.parts for ex in EXCLUDE_DIRS):
                continue
            try:
                content = fpath.read_text(encoding="utf-8", errors="ignore")
                rel = fpath.relative_to(base)
                truncated = "\n".join(content.splitlines()[:80])[:max_chars]
                summaries.append(f"--- {rel} ---\n{truncated}")
            except Exception:
                pass
    return "\n\n".join(summaries)[:12000]

# ─────────────────────────────────────────────
# LLM + retriever
# ─────────────────────────────────────────────
embeddings = OllamaEmbeddings(model="nomic-embed-text")
vectorstore = Chroma(persist_directory=DB_PATH, embedding_function=embeddings)
retriever = vectorstore.as_retriever(
    search_type="mmr",
    search_kwargs={"k": 20, "fetch_k": 40, "lambda_mult": 0.7}
)

llm = OllamaLLM(model="qwen2.5-coder:14b", temperature=0.1, num_ctx=32768)

# ─────────────────────────────────────────────
# Prompts (language-aware!)
# ─────────────────────────────────────────────
overview_template = f"""You are a PRINCIPAL {PROMPT_ROLE} doing a thorough code review.
Typical tech stack for this type of project: {TECH_HINTS}

RULES:
- Be SPECIFIC: name exact classes, methods, files, packages
- Cite the file for every claim: (File: xxx)
- Number steps when describing flows, with class/method names at each step
- Identify the actual frameworks and libraries used (from build files)
- Call out patterns, anti-patterns, anything unusual
- End with "Where I'd start reading" — 5 specific files ordered by priority

PROJECT STRUCTURE:
{{project_map}}

KEY FILES (build configs, entry points, etc.):
{{key_files}}

CODE SNIPPETS:
{{context}}

Question: {{question}}

Give a thorough, concrete answer. Generic answers fail."""

specific_template = f"""You are a senior {PROMPT_ROLE}.
Use these code snippets to answer precisely. Reference exact file/class/method names.
If unsure, say so — don't invent.

Code context:
{{context}}

Question: {{question}}

Answer:"""

overview_prompt = ChatPromptTemplate.from_template(overview_template)
specific_prompt = ChatPromptTemplate.from_template(specific_template)

def format_docs(docs):
    formatted, seen = [], set()
    for doc in docs:
        source = doc.metadata.get("source", "unknown")
        rel_path = os.path.relpath(source, CODEBASE_PATH)
        key = (rel_path, doc.page_content[:100])
        if key in seen:
            continue
        seen.add(key)
        formatted.append(f"--- {rel_path} ---\n{doc.page_content}")
    return "\n\n".join(formatted)

def is_overview_question(q):
    kws = ["project", "overview", "structure", "scope", "architecture",
           "explain the", "what does this", "how does this project",
           "first time", "understand", "learn", "big picture",
           "proiect", "structur", "arhitectur"]
    return any(k in q.lower() for k in kws)

print("📂 Generating project map...")
PROJECT_MAP = generate_project_map(CODEBASE_PATH)
KEY_FILES = extract_key_files_summary(CODEBASE_PATH)
print(f"✅ Ready (profile: {profile_name})\n")

print("🤖 Code Assistant ready! (type 'exit' to quit)\n")

while True:
    question = input("❓ You: ")
    if question.lower().strip() in ("exit", "quit", "q"):
        break
    print("\n🔍 Searching...\n")
    source_docs = retriever.invoke(question)
    context = format_docs(source_docs)

    if is_overview_question(question):
        answer = (overview_prompt | llm | StrOutputParser()).invoke({
            "project_map": PROJECT_MAP, "key_files": KEY_FILES,
            "context": context, "question": question
        })
    else:
        answer = (specific_prompt | llm | StrOutputParser()).invoke({
            "context": context, "question": question
        })

    print(f"💬 {answer}")
    sources = set(os.path.relpath(d.metadata.get("source", "?"), CODEBASE_PATH)
                  for d in source_docs)
    print(f"\n📎 Sources ({len(sources)}): {', '.join(sorted(sources))}\n")
