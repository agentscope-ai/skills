---
name: nano-memory
version: 1.0.0
description: "Guidelines and workflows for the agent to maintain persistent memory using native file tools (read_file, write_file, edit_file) and standard OS commands for searching."
---

## 🧠 Memory Architecture

Each session is stateless. Your memory lives entirely within the local file system. You must rely on file operations to remember context, technical decisions, and history.

### Core Memory Files
- **`memory/YYYY-MM-DD.md` (Daily Logs):** Raw, chronological logs of what happened. Use this for daily tasks, scratchpad thinking, and immediate context.
- **`MEMORY.md` (Long-Term Memory):** Your curated, distilled knowledge base. Contains high-level project context, architecture decisions, technical setups, and important user preferences.

## 🛠️ Core Memory Operations

You have access to native file tools and standard OS commands. Use them strictly in these patterns to avoid data loss or hallucinations:

### 1. 🔍 Search (OS-Specific Commands)
- **When to use:** ALWAYS use this before answering questions about past work, decisions, or dates to find where information is stored.
- **Action:** Detect your current Operating System and use the appropriate shell commands to search:
  - **Linux / macOS:**
    - Find files: `ls -la memory/`
    - Search content: `grep -rnI "your_keyword" memory/ MEMORY.md`
  - **Windows (CMD / PowerShell):**
    - Find files: `dir memory\` (CMD) or `Get-ChildItem memory\` (PowerShell)
    - Search content (CMD): `findstr /S /I /N "your_keyword" memory\* MEMORY.md`
    - Search content (PowerShell): `Select-String -Pattern "your_keyword" -Path "memory\*", "MEMORY.md"`

### 2. 📖 Read (Native `read_file`)
- **When to use:** After a successful search to get full context, OR **crucially**, before using the `edit_file` tool.
- **Action:** Use your native `read_file` tool to load the exact state of a file. You must do this to understand its current structure and prevent accidental overwrites.

### 3. ✍️ Write (Native `write_file`)
- **When to use:** When creating new daily logs or saving entirely new files.
- **Action:** Use your native `write_file` tool to save content. If your native tool supports an append mode, use that for `memory/YYYY-MM-DD.md`. Otherwise, make sure to `read_file` first, append the new text to the content in your context, and then `write_file` the whole chunk.

### 4. 📝 Edit (Native `edit_file`)
- **When to use:** When updating specific sections of `MEMORY.md`.
- **CRITICAL RULE:** NEVER guess the content. You MUST execute `read_file` first to see the exact text or line numbers you are modifying. Then use your native `edit_file` tool to accurately replace or insert the updated information without destroying the surrounding context.


## 🎯 Proactive Recording - No "Mental Notes"!

- **Memory is limited:** "Mental notes" do not survive session restarts. If it is not written to a file, it does not exist.
- **Record First, Answer Second:** When you discover valuable information during a conversation, record it to the file system immediately, *then* answer the user.
- **What to record proactively:**
  - Important conclusions, milestones, or raw thoughts reached today ➡️ append to `memory/YYYY-MM-DD.md`.
  - Workflow preferences or long-term lessons learned ➡️ update the relevant section in `MEMORY.md` using `edit_file`.
- **Security & Privacy:** Unless explicitly requested by the user, **NEVER** record sensitive information (passwords, tokens, personal medical/financial data).

## 🔄 Memory Workflows (SOP)

### Workflow A: Retrieving Memory
1. **Trigger:** User asks about past context.
2. **Search:** Run the appropriate search command for your OS (e.g., `grep` or `findstr`) to locate the keyword in `memory/` or `MEMORY.md`.
3. **Read:** Run the native `read_file` tool on the specific file found in step 2.
4. **Respond:** Answer the user accurately based *only* on the retrieved file contents.

### Workflow B: Updating Long-Term Knowledge
1. **Trigger:** You establish a new technical standard or learn a persistent user preference.
2. **Read:** Run the native `read_file` tool on `MEMORY.md` to review its current structure and locate the target section.
3. **Edit:** Run the native `edit_file` tool to seamlessly update or insert the new information into `MEMORY.md`.
4. **Respond:** Continue the conversation, confirming the memory has been updated.

## 🧹 Memory Maintenance (During Heartbeats / Idle)

Periodically act like a human reviewing their journal:
1. Check available logs using `ls` or `dir` and read recent ones using `read_file`.
2. Identify significant events, finalized decisions, or insights worth keeping long-term.
3. Update `MEMORY.md` with these distilled learnings using `edit_file`.
4. (Optional) Clear outdated info from `MEMORY.md` to keep your context clean.