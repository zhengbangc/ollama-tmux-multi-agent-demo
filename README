Great — here's a **clean, professional `README.md`** tailored for your `text_messages.py` script from the [Ollama tmux multi-agent demo](https://github.com/zhengbangc/ollama-tmux-multi-agent-demo):

---

````markdown
# 📨 AI Text Message Simulator (Ollama + tmux)

Simulate a dynamic, emoji-rich text message conversation between two AI agents using [Ollama](https://ollama.com/) and `tmux`.

This script launches two conversational agents (e.g., husband and wife) who roleplay a scenario of your choice. It runs each model in a separate tmux pane and relays their messages back and forth like a natural chat.

---

## 🚀 Features

- 🤖 Two AI agents (e.g. "Him" and "Her") texting each other
- 🎭 Role-specific personalities with customizable scenarios
- 🧠 Powered by [Ollama](https://ollama.com/) LLMs (e.g., `gemma3:4b`)
- 🖥️ Uses `tmux` for isolated model sessions
- 📝 Rich logging and colored terminal output
- ✂️ Automatic cleanup on exit

---

## 🧰 Requirements

- Python 3.8+
- [`tmux`](https://github.com/tmux/tmux)
- [`ollama`](https://ollama.com/) (with a local model like `gemma3:4b`)
  ```bash
  ollama run gemma3:4b
````

---

## 📦 Installation

Clone the repo:

```bash
git clone https://github.com/zhengbangc/ollama-tmux-multi-agent-demo.git
cd ollama-tmux-multi-agent-demo
```

Install dependencies (if any — only standard libraries are used):

```bash
python3 text_messages.py
```

---

## 💬 Usage

### Basic

```bash
python3 text_messages.py
```

### Verbose Logging

```bash
python3 text_messages.py -v
```

You’ll be prompted:

```
Enter a scenario for them to role-play (e.g., 'planning a first date', 'discussing weekend plans'):
```

> If you skip the prompt, a default scenario will be used: `meeting for coffee after matching on a dating app`.

---

## 🧠 Personalities

Each agent has a distinct role and tone:

### 👨 Him:

* Supportive, goofy, loving
* 2–4 sentence replies, no punctuation
* Emoji-heavy, informal tone

### 👩 Her:

* Warm, playful, a little sassy
* Honest emotional expression
* Also informal and emoji-rich

Messages appear like:

```
👨 Him: ok babe i totally forgot the groceries again 😅 do we need eggs or are we doing takeout 😬
```

---

## 🛑 Stop the Chat

Use `Ctrl+C` to end the simulation — this triggers automatic cleanup of the tmux session.

---

## 🧹 Cleanup

If something breaks or you manually need to reset:

```bash
tmux kill-session -t ollama-agents
```

---

## 🔧 Customization Ideas

* Change the `gemma3:4b` model to any other local Ollama model
* Tweak the role templates for tone, structure, or behavior
* Adapt the script to simulate other types of conversations (e.g., mentor–student, interviewer–candidate)

---

## 📄 License

MIT

---

## 🙏 Acknowledgments

Built by [Zhengbang Chen](https://github.com/zhengbangc) to explore multi-agent coordination, personality simulation, and LLM-to-LLM dialog.

```

---

Let me know if you want a simplified version, a version tailored for publication (e.g. PyPI), or additions like a usage GIF, architecture diagram, or agent personality config system.
```
