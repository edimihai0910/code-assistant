import os
from pathlib import Path
from langchain_community.document_loaders import TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_ollama import OllamaEmbeddings
from langchain_chroma import Chroma
from config import get_profile

# ─────────────────────────────────────────────
# CONFIG — schimbă doar asta!
# ─────────────────────────────────────────────
CODEBASE_PATH = r"FULL_PATH"
DB_PATH = "./chroma_db"

# Opțional: force a profile ("java", "dotnet", "python")
PROFILE_OVERRIDE = None

# ─────────────────────────────────────────────
# Setup based on profile
# ─────────────────────────────────────────────
profile_name, profile = get_profile(CODEBASE_PATH, PROFILE_OVERRIDE)

EXCLUDE_DIRS = profile["exclude_dirs"]
INCLUDE_EXTENSIONS = profile["extensions"]
LANGUAGE = profile["language"]

def should_include(file_path):
    path = Path(file_path)
    if any(excluded in path.parts for excluded in EXCLUDE_DIRS):
        return False
    if path.suffix.lower() not in INCLUDE_EXTENSIONS:
        return False
    try:
        if path.stat().st_size > 500_000:
            return False
    except OSError:
        return False
    return True

# 1. Scan
print(f"📂 Scanning files (profile: {profile_name})...")
all_files = []
for root, dirs, files in os.walk(CODEBASE_PATH):
    dirs[:] = [d for d in dirs if d not in EXCLUDE_DIRS]
    for f in files:
        full_path = os.path.join(root, f)
        if should_include(full_path):
            all_files.append(full_path)
print(f"✅ Found {len(all_files)} relevant files")

# 2. Load
docs = []
failed = 0
for fpath in all_files:
    try:
        loader = TextLoader(fpath, autodetect_encoding=True)
        docs.extend(loader.load())
    except Exception:
        failed += 1
print(f"✅ Loaded {len(docs)} files ({failed} skipped)")

# 3. Smart chunking (language-aware!)
splitter = RecursiveCharacterTextSplitter.from_language(
    language=LANGUAGE,
    chunk_size=3000,
    chunk_overlap=400
)
chunks = splitter.split_documents(docs)
print(f"✅ Split into {len(chunks)} chunks (language: {LANGUAGE.value})")

# 4. Embed + store
print("🔢 Creating embeddings...")
embeddings = OllamaEmbeddings(model="nomic-embed-text")
vectorstore = Chroma.from_documents(
    documents=chunks,
    embedding=embeddings,
    persist_directory=DB_PATH
)
print(f"✅ Done! Indexed in {DB_PATH}")
