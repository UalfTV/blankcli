import sys
import os
import time
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.live import Live
from rich.table import Table
from rich import box
from prompt_toolkit import PromptSession
from prompt_toolkit.history import FileHistory
from prompt_toolkit.key_binding import KeyBindings

import ui
import sessions
import tools
from config import (load_providers, load_keys, save_keys,
                    load_config, save_config)
from providers import stream_chat, chat_once, estimate_cost, ProviderError

console = Console()

HELP = """
/help                show commands
/clear               clear conversation
/model               switch model
/provider            switch provider
/system <txt>        set system prompt
/temp <n>            set temperature
/tools               toggle tool use
/add <file>          add file to context
/drop <file>         remove from context
/ls                  list files in context
/diff                git diff
/compare m1,m2 <q>   ask multiple models
/sessions            list sessions
/resume              load latest session
/export <path>       export to markdown
/theme <name>        switch theme
/keys                manage API keys
/about               about blankCLI
/menu                back to menu
/exit                quit
"""

def keybindings():
    kb = KeyBindings()
    @kb.add("c-c")
    def _(event):
        event.app.exit(exception=KeyboardInterrupt)
    @kb.add("c-l")
    def _(event):
        event.app.current_buffer.reset()
        ui.clear()
        ui.banner()
    return kb

def key_wizard(keys):
    providers = load_providers()
    ui.clear()
    ui.banner()
    ui.section("API Keys")
    cfg = load_config()
    if cfg.get("auto_detect_env", True):
        found = []
        for alias, p in providers.items():
            env = p.get("key_env", "")
            if env and os.environ.get(env) and not keys.get(env):
                keys[env] = os.environ[env]
                found.append(alias)
        if found:
            ui.info(f"imported keys from environment: {', '.join(found)}")
            save_keys(keys)
    console.print(f"[{ui.DIM}]keys are stored in keys.json locally.[/]\n")
    t = Table(box=box.SIMPLE, header_style=f"bold {ui.ACCENT}")
    t.add_column("#", width=3)
    t.add_column("Provider")
    t.add_column("Env name", style=ui.DIM)
    t.add_column("Status")
    items = list(providers.items())
    for i, (alias, p) in enumerate(items, 1):
        env = p.get("key_env", "")
        needs = p.get("needs_key", True)
        has = (not needs) or bool(keys.get(env, ""))
        status = f"[{ui.OK}]set[/]" if has else f"[{ui.DIM}]missing[/]"
        t.add_row(str(i), alias, env or "(none)", status)
    console.print(t)
    console.print(f"[{ui.DIM}]enter number to set, [bold]a[/bold] all, [bold]s[/bold] skip, [bold]q[/bold] quit[/]")
    while True:
        try:
            raw = console.input(f"[{ui.ACCENT}]choice > [/]").strip().lower()
        except (EOFError, KeyboardInterrupt):
            return keys
        if raw in ("q", "quit"):
            sys.exit(0)
        if raw in ("s", ""):
            return keys
        if raw == "a":
            for alias, p in items:
                env = p.get("key_env", "")
                if not env:
                    continue
                val = console.input(f"[{ui.ACCENT}]{alias} key > [/]").strip()
                if val:
                    keys[env] = val
            save_keys(keys)
            return keys
        if raw.isdigit():
            idx = int(raw) - 1
            if 0 <= idx < len(items):
                alias, p = items[idx]
                env = p.get("key_env", "")
                if not env:
                    ui.info(f"{alias} needs no key")
                    continue
                val = console.input(f"[{ui.ACCENT}]{alias} key > [/]").strip()
                if val:
                    keys[env] = val
                    save_keys(keys)
                    ui.info(f"saved {env}")
                continue

def compare(provider_alias, models, question):
    ui.section(f"compare: {', '.join(models)}")
    for m in models:
        console.print(f"\n[bold {ui.ACCENT}]{m}[/]")
        try:
            answer, tok = chat_once(provider_alias, m,
                                    [{"role": "user", "content": question}])
            console.print(Markdown(answer))
            ui.info(f"tokens: {tok['prompt_tokens']}+{tok['completion_tokens']}")
        except ProviderError as e:
            ui.error(f"{m}: {e}")

def stream_render(gen, usage_out):
    buf = ""
    with Live(console=console, refresh_per_second=15, transient=False) as live:
        for item in gen:
            if isinstance(item, tuple) and item and item[0] == "__usage__":
                usage_out.update(item[1])
                break
            buf += item
            live.update(Markdown(buf))
    return buf

def repl(provider_alias, model_id, keys):
    cfg = load_config()
    system = cfg.get("system", "")
    use_tools = False
    temperature = cfg.get("temp", 0.7)
    tok_sum = 0
    cost_sum = 0.0
    history = [{"role": "system", "content": system}] if system else []

    ui.clear()
    ui.banner()
    ui.header(provider_alias, model_id, use_tools, temperature, tok_sum, cost_sum)
    ui.info("type /help for commands")
    ui.divider()

    kb = keybindings()
    session = PromptSession(history=FileHistory(f".blankcli_{provider_alias}.history"),
                            key_bindings=kb)

    while True:
        try:
            user = session.prompt("you > ")
        except KeyboardInterrupt:
            console.print(f"[{ui.DIM}]^C[/]")
            continue
        except EOFError:
            ui.info("bye.")
            return None
        if not user.strip():
            continue

        if user.startswith("/"):
            parts = user.strip().split(maxsplit=1)
            cmd = parts[0]
            arg = parts[1] if len(parts) > 1 else ""
            if cmd in ("/exit", "/quit"):
                sessions.save(history, model_id)
                ui.info("saved session")
                return None
            elif cmd == "/help":
                console.print(Panel(HELP.strip(), border_style=ui.ACCENT))
            elif cmd == "/clear":
                history = [{"role": "system", "content": system}] if system else []
                ui.info("history cleared")
            elif cmd == "/model":
                new = ui.model_menu(provider_alias)
                if new:
                    model_id = new
                    ui.info(f"model = {new}")
            elif cmd == "/provider":
                return "menu"
            elif cmd == "/system":
                system = arg
                history = [{"role": "system", "content": system}] if system else []
                c = load_config()
                c["system"] = system
                save_config(c)
                ui.info("system prompt updated")
            elif cmd == "/temp":
                try:
                    temperature = float(arg)
                    c = load_config()
                    c["temp"] = temperature
                    save_config(c)
                    ui.info(f"temp = {temperature}")
                except ValueError:
                    ui.error("usage: /temp 0.7")
            elif cmd == "/tools":
                use_tools = not use_tools
                ui.info(f"tools = {use_tools}")
            elif cmd == "/add":
                ui.info(tools.add_file(arg))
            elif cmd == "/drop":
                ui.info(tools.drop_file(arg))
            elif cmd == "/ls":
                files = tools.list_added()
                if files:
                    for f in files:
                        console.print(f"  {f}")
                else:
                    ui.info("no files in context")
            elif cmd == "/diff":
                import subprocess
                try:
                    r = subprocess.run("git diff --stat", shell=True,
                                       capture_output=True, text=True, timeout=10)
                    console.print(r.stdout or "[no git repo]")
                except Exception as e:
                    ui.error(str(e))
            elif cmd == "/compare":
                sp = arg.split(maxsplit=1)
                if len(sp) < 2:
                    ui.error("usage: /compare model1,model2 your question")
                else:
                    models = [x.strip() for x in sp[0].split(",")]
                    compare(provider_alias, models, sp[1])
            elif cmd == "/sessions":
                for r in sessions.list_recent():
                    console.print(f"  [{ui.ACCENT}]{r['file']}[/]  "
                                  f"{r['model']}  {r['turns']} turns  {r['time']}")
            elif cmd == "/resume":
                d = sessions.latest()
                if not d:
                    ui.info("no sessions")
                else:
                    history = d["messages"]
                    model_id = d.get("model", model_id)
                    ui.info(f"resumed {d['timestamp']} ({len(history)} msgs)")
            elif cmd == "/export":
                if not arg:
                    arg = f"export_{int(time.time())}.md"
                p = sessions.export_md(history, arg)
                ui.info(f"exported to {p}")
            elif cmd == "/theme":
                from themes import names as theme_names
                if arg in theme_names():
                    c = load_config()
                    c["theme"] = arg
                    save_config(c)
                    ui.reload_theme()
                    ui.info(f"theme = {arg}")
                else:
                    ui.error(f"themes: {', '.join(theme_names())}")
            elif cmd == "/keys":
                keys = key_wizard(keys)
            elif cmd == "/about":
                ui.about()
            elif cmd == "/menu":
                return "menu"
            else:
                ui.error(f"unknown: {cmd}")
            continue

        ctx = tools.context_block()
        msg_content = user + (("\n\n" + ctx) if ctx else "")
        history.append({"role": "user", "content": msg_content})
        console.print(f"[bold {ui.USER}]blank[/] ", end="")

        usage = {}
        try:
            if use_tools:
                answer, tok = chat_once(provider_alias, model_id, history, temperature)
                console.print(Markdown(answer))
                history.append({"role": "assistant", "content": answer})
                tok_sum += tok["prompt_tokens"] + tok["completion_tokens"]
                cost_sum += estimate_cost(provider_alias, model_id, tok)
            else:
                gen = stream_chat(provider_alias, model_id, history, temperature)
                answer = stream_render(gen, usage)
                history.append({"role": "assistant", "content": answer})
                tok_sum += usage.get("prompt_tokens", 0) + usage.get("completion_tokens", 0)
                cost_sum += estimate_cost(provider_alias, model_id, usage)
        except ProviderError as e:
            ui.error(str(e))
            history.pop()
        except KeyboardInterrupt:
            console.print(f"\n[{ui.DIM}]interrupted[/]")
            history.pop()
        except Exception as e:
            ui.error(str(e))
            history.pop()

        ui.divider()

def main():
    ui.clear()
    ui.banner()
    ui.boot_sequence()
    keys = load_keys()
    providers = load_providers()
    has_any = any(keys.get(p.get("key_env", ""), "") for p in providers.values() if p.get("key_env"))
    if not has_any:
        ui.info("no keys configured - running setup")
        time.sleep(0.3)
        keys = key_wizard(keys)
    while True:
        ui.clear()
        ui.banner()
        provider_alias = ui.provider_menu()
        if provider_alias == "__keys__":
            keys = key_wizard(keys)
            continue
        if not provider_alias:
            ui.info("bye.")
            return
        model_id = ui.model_menu(provider_alias)
        if not model_id:
            continue
        c = load_config()
        c["last_provider"] = provider_alias
        c["last_model"] = model_id
        save_config(c)
        result = repl(provider_alias, model_id, keys)
        if result != "menu":
            return

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print()
        sys.exit(0)
