import os
import litellm
from config import load_providers, load_keys

litellm.drop_params = True
litellm.suppress_debug_info = True

class ProviderError(Exception):
    pass

def _resolve(provider_alias, model_id, providers, keys):
    if provider_alias not in providers:
        raise ProviderError(f"unknown provider: {provider_alias}")
    p = providers[provider_alias]
    base = p.get("base_url", "")
    key_env = p.get("key_env", "")
    needs = p.get("needs_key", True)
    key = keys.get(key_env, "") or (os.environ.get(key_env, "") if key_env else "")
    if needs and not key:
        raise ProviderError(f"{provider_alias}: missing key ({key_env})")
    route = f"openai/{model_id}" if provider_alias != "openai" else model_id
    return {"model": route, "api_base": base, "api_key": key or "sk-none"}

def _clean_err(e):
    s = str(e)
    for marker in ["Give Feedback / Get Help", "LiteLLM.Info"]:
        if marker in s:
            s = s.split(marker)[0].strip()
    return s

def stream_chat(provider_alias, model_id, messages, temperature=0.7, max_tokens=4096):
    providers = load_providers()
    keys = load_keys()
    cfg = _resolve(provider_alias, model_id, providers, keys)
    try:
        resp = litellm.completion(
            model=cfg["model"],
            api_base=cfg["api_base"],
            api_key=cfg["api_key"],
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            stream=True,
            stream_options={"include_usage": True},
        )
    except Exception as e:
        raise ProviderError(_clean_err(e))
    usage = {"prompt_tokens": 0, "completion_tokens": 0}
    for chunk in resp:
        try:
            if hasattr(chunk, "usage") and chunk.usage:
                usage["prompt_tokens"] = getattr(chunk.usage, "prompt_tokens", 0) or 0
                usage["completion_tokens"] = getattr(chunk.usage, "completion_tokens", 0) or 0
        except Exception:
            pass
        delta = ""
        try:
            delta = chunk.choices[0].delta.content or ""
        except Exception:
            pass
        if delta:
            yield delta
    yield ("__usage__", usage)

def chat_once(provider_alias, model_id, messages, temperature=0.7, max_tokens=4096):
    providers = load_providers()
    keys = load_keys()
    cfg = _resolve(provider_alias, model_id, providers, keys)
    try:
        resp = litellm.completion(
            model=cfg["model"],
            api_base=cfg["api_base"],
            api_key=cfg["api_key"],
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
        )
    except Exception as e:
        raise ProviderError(_clean_err(e))
    content = resp.choices[0].message.content or ""
    usage = getattr(resp, "usage", None)
    tok = {
        "prompt_tokens": getattr(usage, "prompt_tokens", 0) if usage else 0,
        "completion_tokens": getattr(usage, "completion_tokens", 0) if usage else 0,
    }
    return content, tok

def estimate_cost(provider_alias, model_id, tok):
    rates = {
        "deepseek":   {"in": 0.14, "out": 0.28},
        "openai":     {"in": 2.50, "out": 10.00},
        "groq":       {"in": 0.10, "out": 0.10},
        "openrouter": {"in": 1.00, "out": 3.00},
    }
    r = rates.get(provider_alias, {"in": 0.5, "out": 1.5})
    return (tok["prompt_tokens"] / 1_000_000) * r["in"] \
         + (tok["completion_tokens"] / 1_000_000) * r["out"]

def fetch_openrouter_models():
    import requests
    try:
        r = requests.get("https://openrouter.ai/api/v1/models", timeout=10)
        data = r.json().get("data", [])
        return sorted(m["id"] for m in data)
    except Exception:
        return []

def fetch_groq_models(key):
    import requests
    try:
        r = requests.get("https://api.groq.com/openai/v1/models",
                         headers={"Authorization": f"Bearer {key}"}, timeout=10)
        data = r.json().get("data", [])
        return sorted(m["id"] for m in data)
    except Exception:
        return []
