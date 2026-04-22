"""
Configuration profiles for different project types.
Auto-detects based on files present in the codebase.
"""
import os
from pathlib import Path
from langchain_text_splitters import Language

# ─────────────────────────────────────────────
# Profile definitions
# ─────────────────────────────────────────────

PROFILES = {
    "java": {
        "language": Language.JAVA,
        "extensions": {
            ".java", ".kt", ".scala", ".groovy",
            ".xml", ".gradle", ".properties", ".yml", ".yaml",
            ".json", ".toml", ".jsp", ".html", ".css", ".js",
            ".sql", ".md", ".txt",
        },
        "exclude_dirs": {
            "target", "build", ".gradle", ".mvn", "node_modules",
            ".git", ".idea", ".vscode", ".settings", "out", "bin", "dist",
        },
        "key_patterns": [
            "pom.xml", "build.gradle", "build.gradle.kts", "settings.gradle",
            "application.yml", "application.yaml", "application.properties",
            "*Application.java", "Main.java", "App.java",
            "README.md", "readme.md",
        ],
        "indicators": ["pom.xml", "build.gradle", "build.gradle.kts"],
        "prompt_role": "senior Java developer",
        "tech_hints": "Spring Boot, Maven/Gradle, Hibernate/JPA, JUnit",
    },
    "dotnet": {
        "language": Language.CSHARP,
        "extensions": {
            ".cs", ".cshtml", ".razor", ".xaml",
            ".csproj", ".sln", ".props", ".targets",
            ".json", ".xml", ".yaml", ".yml", ".config",
            ".sql", ".js", ".ts", ".css", ".html", ".md",
        },
        "exclude_dirs": {
            "bin", "obj", "node_modules", ".git", ".vs", ".vscode",
            "packages", "TestResults", "Debug", "Release", ".nuget",
        },
        "key_patterns": [
            "*.sln", "*.csproj", "Program.cs", "Startup.cs", "App.xaml.cs",
            "appsettings.json", "App.config", "Web.config",
            "README.md", "readme.md",
        ],
        "indicators": ["*.sln", "*.csproj"],
        "prompt_role": "senior .NET developer",
        "tech_hints": ".NET, ASP.NET, Entity Framework, NUnit/xUnit",
    },
    "python": {
        "language": Language.PYTHON,
        "extensions": {
            ".py", ".pyi", ".toml", ".cfg", ".ini",
            ".yml", ".yaml", ".json", ".md", ".txt", ".sql",
        },
        "exclude_dirs": {
            "__pycache__", ".venv", "venv", "env", ".git",
            ".pytest_cache", ".mypy_cache", "dist", "build", ".tox",
        },
        "key_patterns": [
            "pyproject.toml", "setup.py", "setup.cfg", "requirements.txt",
            "main.py", "app.py", "__main__.py", "README.md",
        ],
        "indicators": ["pyproject.toml", "setup.py", "requirements.txt"],
        "prompt_role": "senior Python developer",
        "tech_hints": "Django, Flask, FastAPI, pytest",
    },
}

# ─────────────────────────────────────────────
# Auto-detection
# ─────────────────────────────────────────────

def detect_profile(codebase_path):
    """Detect project type by looking for indicator files."""
    base = Path(codebase_path)
    
    for profile_name, profile in PROFILES.items():
        for pattern in profile["indicators"]:
            if "*" in pattern:
                matches = list(base.rglob(pattern))
                if matches:
                    return profile_name, profile
            else:
                if (base / pattern).exists() or list(base.rglob(pattern)):
                    return profile_name, profile
    
    # Fallback: default to java
    print("⚠️  Could not detect project type, defaulting to 'java'")
    return "java", PROFILES["java"]

def get_profile(codebase_path, override=None):
    """Get profile: use override if specified, otherwise auto-detect."""
    if override and override in PROFILES:
        print(f"✅ Using profile (manual): {override}")
        return override, PROFILES[override]
    
    name, profile = detect_profile(codebase_path)
    print(f"✅ Auto-detected profile: {name}")
    return name, profile
