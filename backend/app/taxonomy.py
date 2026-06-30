from dataclasses import dataclass
import re


@dataclass(frozen=True)
class SectorRule:
    id: str
    name: str
    keywords: tuple[str, ...]
    topics: tuple[str, ...]
    languages: tuple[str, ...] = ()


SECTOR_RULES: tuple[SectorRule, ...] = (
    SectorRule(
        "ai-agents",
        "AI agents",
        ("agent", "agents", "autonomous", "tool use", "mcp", "computer use", "workflow automation"),
        ("ai-agent", "agents", "llm-agent", "autonomous-agents", "mcp", "multi-agent"),
        ("Python", "TypeScript"),
    ),
    SectorRule(
        "developer-tools",
        "Developer tools",
        ("cli", "sdk", "debug", "testing", "lint", "formatter", "codegen", "developer"),
        ("devtools", "developer-tools", "cli", "testing", "sdk", "codegen"),
    ),
    SectorRule(
        "data-analytics",
        "Data analytics",
        ("analytics", "dashboard", "visualization", "warehouse", "etl", "metrics"),
        ("analytics", "data-visualization", "etl", "data-engineering", "dashboard"),
        ("Python", "R", "SQL"),
    ),
    SectorRule(
        "ml-ai-infra",
        "ML/AI infrastructure",
        ("llm", "inference", "embedding", "vector", "rag", "model", "eval", "fine-tune"),
        ("machine-learning", "llm", "rag", "inference", "embeddings", "evals", "ai"),
        ("Python", "C++", "Rust"),
    ),
    SectorRule(
        "web-frontend",
        "Web/frontend",
        ("react", "vue", "svelte", "frontend", "ui", "component", "css"),
        ("react", "vue", "svelte", "frontend", "ui", "css", "typescript"),
        ("TypeScript", "JavaScript", "CSS"),
    ),
    SectorRule(
        "backend-api",
        "Backend/API",
        ("api", "server", "backend", "graphql", "rest", "microservice"),
        ("api", "backend", "graphql", "server", "microservices"),
        ("Go", "Python", "Java", "Rust", "TypeScript"),
    ),
    SectorRule(
        "cloud-devops",
        "Cloud/devops",
        ("kubernetes", "docker", "terraform", "observability", "deploy", "ci/cd", "cloud"),
        ("kubernetes", "docker", "terraform", "devops", "observability", "cloud"),
        ("Go", "Shell", "HCL", "Rust"),
    ),
    SectorRule(
        "security",
        "Security",
        ("security", "vulnerability", "auth", "scanner", "privacy", "encryption"),
        ("security", "privacy", "vulnerability", "auth", "encryption", "scanner"),
        ("Go", "Rust", "Python"),
    ),
    SectorRule(
        "databases",
        "Databases",
        ("database", "sql", "postgres", "sqlite", "query", "storage", "index"),
        ("database", "postgresql", "sqlite", "sql", "storage", "search"),
        ("SQL", "Rust", "Go", "C++"),
    ),
    SectorRule(
        "mobile",
        "Mobile",
        ("android", "ios", "react native", "swift", "kotlin", "mobile"),
        ("android", "ios", "react-native", "mobile", "swift", "kotlin"),
        ("Swift", "Kotlin", "Dart", "TypeScript"),
    ),
)


def sector_payload() -> list[dict]:
    return [
        {
            "id": rule.id,
            "name": rule.name,
            "keywords": list(rule.keywords),
            "topics": list(rule.topics),
            "languages": list(rule.languages),
        }
        for rule in SECTOR_RULES
    ]


def classify_repo(
    topics: list[str] | tuple[str, ...],
    description: str | None,
    readme_excerpt: str | None,
    language: str | None,
) -> list[str]:
    topic_set = {topic.lower() for topic in topics}
    text = f"{description or ''} {readme_excerpt or ''}".lower()
    language_name = language or ""
    sectors: list[str] = []

    for rule in SECTOR_RULES:
        topic_hit = any(topic in topic_set for topic in rule.topics)
        keyword_hit = any(_keyword_matches(keyword, text) for keyword in rule.keywords)
        language_hit = bool(language_name and language_name in rule.languages)
        if topic_hit or keyword_hit or (language_hit and keyword_hit):
            sectors.append(rule.id)

    return sectors or ["unclassified"]


def _keyword_matches(keyword: str, text: str) -> bool:
    if " " in keyword or "/" in keyword:
        return keyword in text
    return bool(re.search(rf"\b{re.escape(keyword)}\b", text))


def appears_english(text: str | None) -> bool:
    if not text or len(text.strip()) < 24:
        return True
    sample = text[:600]
    ascii_letters = sum(1 for char in sample if char.isascii() and char.isalpha())
    all_letters = sum(1 for char in sample if char.isalpha())
    if all_letters < 16:
        return True
    common_words = (" the ", " and ", " for ", " with ", " from ", " this ", " that ", " build ", " open ")
    common_hits = sum(1 for word in common_words if word in f" {sample.lower()} ")
    return ascii_letters / all_letters >= 0.85 and common_hits >= 1
