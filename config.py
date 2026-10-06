import json
from pathlib import Path

ROOT = Path(__file__).parent
SESSIONS = ROOT / "sessions"
KEYS_FILE = ROOT / "keys.json"
CONFIG_FILE = ROOT / "config.json"
PROVIDERS_FILE = ROOT / "providers.json"

VERSION = "1.0.0"
AUTHOR = "UalfTV/blankengine"
CREDITS_URL = "https://blankengine.pages.dev/"
CREDITS_DISCORD = "blankengine"

DEFAULT_PROVIDERS = {
    "openrouter": {
        "base_url": "https://openrouter.ai/api/v1",
        "key_env": "OPENROUTER_API_KEY",
        "label": "OpenRouter (400+ models, one key)",
        "needs_key": True,
        "dynamic": True,
    },
    "deepseek": {
        "base_url": "https://api.deepseek.com/v1",
        "key_env": "DEEPSEEK_API_KEY",
        "label": "DeepSeek",
        "needs_key": True,
        "models": ["deepseek-chat", "deepseek-reasoner"],
    },
    "openai": {
        "base_url": "https://api.openai.com/v1",
        "key_env": "OPENAI_API_KEY",
        "label": "OpenAI",
        "needs_key": True,
        "models": ["gpt-4o", "gpt-4o-mini", "gpt-4.1", "o3-mini"],
    },
    "gemini": {
        "base_url": "https://generativelanguage.googleapis.com/v1beta/openai",
        "key_env": "GEMINI_API_KEY",
        "label": "Google Gemini",
        "needs_key": True,
        "models": ["gemini-2.5-pro", "gemini-2.5-flash"],
    },
    "groq": {
        "base_url": "https://api.groq.com/openai/v1",
        "key_env": "GROQ_API_KEY",
        "label": "Groq",
        "needs_key": True,
        "dynamic": True,
    },
    "local": {
        "base_url": "http://localhost:11434/v1",
        "key_env": "",
        "label": "Local (ollama/lmstudio/vllm)",
        "needs_key": False,
        "models": ["llama3.1", "qwen2.5", "mistral"],
    },
}

def load_providers():
    if PROVIDERS_FILE.exists():
        try:
            user = json.loads(PROVIDERS_FILE.read_text(encoding="utf-8"))
            merged = dict(DEFAULT_PROVIDERS)
            merged.update(user)
            return merged
        except Exception:
            pass
    return dict(DEFAULT_PROVIDERS)

def save_providers(providers):
    PROVIDERS_FILE.write_text(json.dumps(providers, indent=2), encoding="utf-8")

def load_keys():
    if KEYS_FILE.exists():
        try:
            return json.loads(KEYS_FILE.read_text(encoding="utf-8"))
        except Exception:
            return {}
    return {}

def save_keys(keys):
    KEYS_FILE.write_text(json.dumps(keys, indent=2), encoding="utf-8")

def load_config():
    defaults = {
        "theme": "cyan",
        "last_provider": "openrouter",
        "last_model": "",
        "auto_detect_env": True,
        "temp": 0.7,
    }
    if CONFIG_FILE.exists():
        try:
            cfg = json.loads(CONFIG_FILE.read_text(encoding="utf-8"))
            defaults.update(cfg)
        except Exception:
            pass
    return defaults

def save_config(cfg):
    CONFIG_FILE.write_text(json.dumps(cfg, indent=2), encoding="utf-8")
