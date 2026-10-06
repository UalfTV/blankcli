# blankCLI

A blank slate for every model.

Multi-provider LLM CLI. One interface, every model.

by UalfTV/blankengine
https://blankengine.pages.dev/

---

## what it is

blankCLI is a terminal client for talking to any LLM through a single interface.
Bring your own keys, pick a provider, pick a model, go. No lock-in, no accounts,
no telemetry.

## install

    pip install git+https://github.com/UalfTV/blankcli.git

## run

    blankcli

First run opens the key wizard. Paste at least one key and you are in.

## providers

| provider    | notes                                              |
|-------------|----------------------------------------------------|
| OpenRouter  | 400+ models behind one key. Model list fetched live. |
| DeepSeek    | cheap, fast, strong on code                        |
| OpenAI      | gpt-4o, gpt-4o-mini, gpt-4.1, o3-mini              |
| Google      | gemini-2.5-pro, gemini-2.5-flash                   |
| Groq        | fastest inference on the market                    |
| Local       | ollama, lmstudio, vllm - any OpenAI-compatible endpoint |

Add your own by dropping a `providers.json` in the working directory.

## features

- streaming responses, rendered live as markdown
- token count and estimated cost per turn
- session save, resume, export to markdown
- file context: add files, ask about them, drop them
- multi-model compare in one call
- six themes
- keys stored locally, never transmitted anywhere except the provider you chose

## commands

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

## config

`keys.json` and `config.json` live next to the script and are never committed.
Override defaults by editing `config.json`:

    {
      "theme": "cyan",
      "last_provider": "openrouter",
      "last_model": "",
      "auto_detect_env": true,
      "temp": 0.7
    }

## license

MIT - see [LICENSE](LICENSE).

---

built with care. credits to blankengine.
