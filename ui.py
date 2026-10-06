import time
import os
from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from rich.table import Table
from rich.align import Align
from rich.live import Live
from rich.spinner import Spinner
from rich import box
from config import (load_providers, load_keys, load_config,
                    VERSION, AUTHOR, CREDITS_URL, CREDITS_DISCORD)
import themes

console = Console()

BLANK_LOGO = r"""
    ____  __            _     ______ _      _____
   / __ )/ /___ _____  | |  / / ___/ /     /  _/
  / __  / / __ `/ __ \ | | / / /__/ /      / /
 / /_/ / / /_/ / / / / | |/ / ___/ /___  _/ /
/_____/_/\__,_/_/ /_/  |___/_/  /_____//___/
"""

_T = themes.get(load_config().get("theme", "cyan"))
ACCENT = _T["accent"]
DIM = _T["dim"]
OK = _T["ok"]
ERR = _T["err"]
USER = _T["user"]

def reload_theme():
    global _T, ACCENT, DIM, OK, ERR, USER
    _T = themes.get(load_config().get("theme", "cyan"))
    ACCENT = _T["accent"]
    DIM = _T["dim"]
    OK = _T["ok"]
    ERR = _T["err"]
    USER = _T["user"]

def clear():
    console.clear()

def banner():
    console.print(Align.center(Text(BLANK_LOGO, style=f"bold {ACCENT}")))
    console.print(Align.center(Text(f"   v{VERSION}  ·  a blank slate for every model\n", style=DIM)))
    console.print(Align.center(Text(f"   by {AUTHOR}\n", style=DIM)))
    console.print(Align.center(Text(f"   {CREDITS_URL}\n", style=DIM)))

def boot_sequence():
    steps = [
        "initializing runtime",
        "loading providers",
        "checking key vault",
        "ready",
    ]
    with Live(console=console, refresh_per_second=20, transient=True) as live:
        for s in steps:
            live.update(Align.center(Spinner("dots", text=Text(f" {s}...", style=DIM))))
            time.sleep(0.15)
    console.print(Align.center(Text("ready.", style=OK)))
    time.sleep(0.2)

def section(title):
    console.print()
    console.print(Panel.fit(f"[bold {ACCENT}]{title}[/bold {ACCENT}]",
                            border_style=ACCENT, box=box.ROUNDED))

def provider_menu():
    providers = load_providers()
    keys = load_keys()
    section("Choose a provider")
    table = Table(box=box.ROUNDED, border_style=DIM, show_header=False)
    table.add_column("#", width=3, style=f"bold {ACCENT}")
    table.add_column("Provider")
    table.add_column("Endpoint", style=DIM)
    table.add_column("Status")
    items = list(providers.items())
    for i, (alias, cfg) in enumerate(items, 1):
        needs = cfg.get("needs_key", True)
        key_env = cfg.get("key_env", "")
        has = (not needs) or bool(keys.get(key_env, "").strip() or os.environ.get(key_env, ""))
        status = f"[{OK}]ready[/]" if has else f"[{DIM}]no key[/]"
        table.add_row(str(i), f"{alias}  ({cfg.get('label', alias)})",
                      cfg.get("base_url", ""), status)
    console.print(table)
    console.print(f"[{DIM}]enter number, [bold]k[/bold] for keys, [bold]q[/bold] to quit[/]")
    while True:
        try:
            raw = console.input(f"[{ACCENT}]select > [/]").strip().lower()
        except (EOFError, KeyboardInterrupt):
            return ""
        if raw in ("q", "quit", ""):
            return ""
        if raw == "k":
            return "__keys__"
        if raw.isdigit():
            idx = int(raw) - 1
            if 0 <= idx < len(items):
                alias = items[idx][0]
                cfg = items[idx][1]
                needs = cfg.get("needs_key", True)
                env = cfg.get("key_env", "")
                has = (not needs) or bool(keys.get(env, "").strip() or os.environ.get(env, ""))
                if needs and not has:
                    console.print(f"[{ERR}]{alias} needs a key ({env})[/]")
                    try:
                        ans = console.input(f"[{ACCENT}]configure now? (y/n) > [/]").strip().lower()
                    except (EOFError, KeyboardInterrupt):
                        return ""
                    if ans in ("y", "yes", ""):
                        return "__keys__"
                    return ""
                return alias
        console.print(f"[{ERR}]invalid choice[/]")

def model_menu(provider_alias):
    from providers import fetch_openrouter_models, fetch_groq_models
    providers = load_providers()
    keys = load_keys()
    cfg = providers.get(provider_alias, {})
    section(f"Choose a model ({provider_alias})")
    models = []
    if cfg.get("dynamic"):
        if provider_alias == "openrouter":
            console.print(f"[{DIM}]fetching model list...[/]")
            models = fetch_openrouter_models()
        elif provider_alias == "groq":
            env = cfg.get("key_env", "")
            models = fetch_groq_models(keys.get(env, ""))
    if not models:
        models = cfg.get("models", [])
    if not models:
        console.print(f"[{DIM}]no known models - type a model id[/]")
        return console.input(f"[{ACCENT}]model id > [/]").strip()
    table = Table(box=box.ROUNDED, border_style=DIM, show_header=False)
    table.add_column("#", width=4, style=f"bold {ACCENT}")
    table.add_column("Model")
    for i, m in enumerate(models[:60], 1):
        table.add_row(str(i), m)
    if len(models) > 60:
        console.print(f"[{DIM}]{len(models)} models available, showing first 60[/]")
    console.print(table)
    console.print(f"[{DIM}]enter number, or type a custom model id, [bold]q[/bold] back[/]")
    while True:
        try:
            raw = console.input(f"[{ACCENT}]select > [/]").strip()
        except (EOFError, KeyboardInterrupt):
            return ""
        if raw in ("q", "quit", ""):
            return ""
        if raw.isdigit():
            idx = int(raw) - 1
            if 0 <= idx < len(models):
                return models[idx]
        return raw

def header(provider_alias, model_id, has_tools, temp, tok_sum, cost_sum):
    t = Text()
    t.append("provider ", style=DIM)
    t.append(provider_alias, style=f"bold {ACCENT}")
    t.append("  ·  model ", style=DIM)
    t.append(model_id, style=f"bold {ACCENT}")
    t.append("\n")
    t.append("tools ", style=DIM)
    t.append("on" if has_tools else "off", style=OK if has_tools else DIM)
    t.append("  ·  temp ", style=DIM)
    t.append(f"{temp}", style=DIM)
    t.append("  ·  tokens ", style=DIM)
    t.append(f"{tok_sum}", style=DIM)
    t.append("  ·  cost ", style=DIM)
    t.append(f"${cost_sum:.4f}", style=DIM)
    console.print(Panel(t, border_style=DIM, box=box.ROUNDED,
                        title=f"[bold {ACCENT}]blankCLI[/]", title_align="left"))

def about():
    t = Text()
    t.append("blankCLI ", style=f"bold {ACCENT}")
    t.append(f"v{VERSION}\n", style=DIM)
    t.append("\nby ", style=DIM)
    t.append(AUTHOR, style=f"bold {ACCENT}")
    t.append(f"\n{CREDITS_URL}", style=DIM)
    t.append(f"\ndiscord: {CREDITS_DISCORD}", style=DIM)
    t.append("\n\n", style=DIM)
    t.append("a blank slate for every model.\n", style=DIM)
    console.print(Panel(t, border_style=ACCENT, box=box.ROUNDED,
                        title=f"[bold {ACCENT}]about[/]", title_align="left"))

def info(msg):
    console.print(f"[{DIM}]{msg}[/]")

def error(msg):
    console.print(f"[{ERR}]error[/] {msg}")

def divider():
    console.print(f"[{DIM}]{'─' * 60}[/]")
