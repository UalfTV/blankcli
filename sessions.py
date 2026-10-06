import json
import time
from pathlib import Path
from config import SESSIONS

def save(messages, model):
    SESSIONS.mkdir(parents=True, exist_ok=True)
    ts = time.strftime("%Y%m%d-%H%M%S")
    path = SESSIONS / f"{ts}_{model.replace('/', '_')}.json"
    data = {"timestamp": ts, "model": model, "messages": messages}
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
    return str(path)

def load(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))

def latest():
    files = sorted(SESSIONS.glob("*.json"), reverse=True)
    return load(str(files[0])) if files else None

def list_recent(n=10):
    files = sorted(SESSIONS.glob("*.json"), reverse=True)[:n]
    out = []
    for f in files:
        try:
            d = load(str(f))
            out.append({
                "file": f.name,
                "model": d.get("model", "?"),
                "turns": len([m for m in d.get("messages", []) if m.get("role") == "user"]),
                "time": d.get("timestamp", "?"),
            })
        except Exception:
            continue
    return out

def export_md(messages, out_path):
    lines = []
    for m in messages:
        role = m.get("role", "?")
        content = m.get("content", "")
        if role == "system":
            lines.append(f"### system\n\n{content}\n")
        elif role == "user":
            lines.append(f"### you\n\n{content}\n")
        elif role == "assistant":
            lines.append(f"### assistant\n\n{content}\n")
    Path(out_path).write_text("\n".join(lines), encoding="utf-8")
    return out_path
