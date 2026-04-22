import os
from pathlib import Path
from langchain_community.document_loaders import TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_ollama import OllamaEmbeddings
from langchain_chroma import Chroma

CODEBASE_PATH = r"C:\Cabis\Hungary\HIFS Mid Alarm"
DB_PATH = "./chroma_db"

EXCLUDE_DIRS = {
    "bin", "obj", "node_modules", ".git", ".vs", ".vscode",
    "packages", "TestResults", "Debug", "Release", ".nuget"
}

INCLUDE_EXTENSIONS = {
    ".cs", ".cshtml", ".razor", ".xaml",
    ".csproj", ".sln", ".props", ".targets",
    ".json", ".xml", ".yaml", ".yml", ".config",
    ".sql", ".js", ".ts", ".jsx", ".tsx", ".css", ".html",
    ".md", ".txt", ".rst",
}

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

# 1. Scanează fișierele
print("📂 Scanning files...")
all_files = []
for root, dirs, files in os.walk(CODEBASE_PATH):
    dirs[:] = [d for d in dirs if d not in EXCLUDE_DIRS]
    for f in files:
        full_path = os.path.join(root, f)
        if should_include(full_path):
            all_files.append(full_path)

print(f"✅ Found {len(all_files)} relevant files")

# 2. Încarcă fișierele
docs = []
failed = 0
for fpath in all_files:
    try:
        loader = TextLoader(fpath, autodetect_encoding=True)
        docs.extend(loader.load())
    except Exception as e:
        failed += 1

print(f"✅ Loaded {len(docs)} files ({failed} skipped due to errors)")

# 3. Sparge în bucăți
splitter = RecursiveCharacterTextSplitter(
    chunk_size=2000,
    chunk_overlap=200
)
chunks = splitter.split_documents(docs)
print(f"✅ Split into {len(chunks)} chunks")

# 4. Creează embeddings + stochează local
print("🔢 Creating embeddings (this may take a while)...")
embeddings = OllamaEmbeddings(model="nomic-embed-text")
vectorstore = Chroma.from_documents(
    documents=chunks,
    embedding=embeddings,
    persist_directory=DB_PATH
)
print(f"✅ Done! Indexed in {DB_PATH}")