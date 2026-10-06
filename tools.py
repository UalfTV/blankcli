import subprocess
from pathlib import Path

ADDED_FILES = {}

def read_file(path, max_bytes=200_000):
    p = Path(path)
    if not p.exists():
        return f"[error] {path} not found"
    data = p.read_bytes()[:max_bytes]
    try:
        return data.decode("utf-8")
    except UnicodeDecodeError:
        return f"[binary, {len(data)} bytes]"

def write_file(path, content):
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content, encoding="utf-8")
    return f"[wrote {len(content)} bytes to {path}]"

def run_cmd(cmd, timeout=30):
    try:
        r = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=timeout)
        out = r.stdout + r.stderr
        return out[:20_000] if out else "[no output]"
    except subprocess.TimeoutExpired:
        return "[timeout]"

def add_file(path):
    p = Path(path)
    if not p.exists():
        return f"[error] {path} not found"
    ADDED_FILES[str(p)] = p.read_text(encoding="utf-8", errors="replace")
    return f"[added {path}]"

def drop_file(path):
    if path in ADDED_FILES:
        del ADDED_FILES[path]
        return f"[dropped {path}]"
    return f"[not in context: {path}]"

def list_added():
    return list(ADDED_FILES.keys())

def context_block():
    if not ADDED_FILES:
        return ""
    out = ["\n--- files in context ---\n"]
    for path, content in ADDED_FILES.items():
        out.append(f"### {path}\n```\n{content}\n```\n")
    return "\n".join(out)

TOOL_SCHEMAS = [
    {"type": "function", "function": {
        "name": "read_file", "description": "Read a file from disk",
        "parameters": {"type": "object",
            "properties": {"path": {"type": "string"}},
            "required": ["path"]}}},
    {"type": "function", "function": {
        "name": "write_file", "description": "Write content to a file (overwrite)",
        "parameters": {"type": "object",
            "properties": {"path": {"type": "string"}, "content": {"type": "string"}},
            "required": ["path", "content"]}}},
    {"type": "function", "function": {
        "name": "run_cmd", "description": "Run a shell command and return output",
        "parameters": {"type": "object",
            "properties": {"cmd": {"type": "string"}},
            "required": ["cmd"]}}},
]

def dispatch(name, args):
    if name == "read_file":  return read_file(**args)
    if name == "write_file": return write_file(**args)
    if name == "run_cmd":    return run_cmd(**args)
    return f"[unknown tool {name}]"
