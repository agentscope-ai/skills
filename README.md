# Skills

[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](./LICENSE)

A curated collection of **skills** around [AgentScope](https://github.com/agentscope-ai/agentscope) ecosystem and CoPaw applications — ready to be installed into AI coding assistants like Claude Code, Cursor, and more.

Each skill is a self-contained knowledge pack that gives your AI assistant deep, accurate context about AgentScope: its APIs, design patterns, examples, and best practices. Instead of hallucinating APIs or reinventing existing features, your assistant can consult these skills to produce correct, idiomatic AgentScope code.

---

## Quickstart

### Claude Code

Copy the skill into the `~/.claude/skills/` directory to make it available to Claude Code globally:

```bash
# Clone the repository
git clone https://github.com/agentscope-ai/agentscope-skills.git

# Make sure the skills directory exists
mkdir -p ~/.claude/skills/

# Copy the skill to Claude's skills directory
cp -r agentscope-skills/skills/{skill_name} ~/.claude/skills/
```

Optionally, you can copy the skill into a specific project directory (`.claude/skills`) to make it available only within that project:

---

### Cursor

Cursor uses the `.cursor/skills` directory to load skills as context for the coding assistant.

```bash
# Clone the repository
git clone https://github.com/agentscope-ai/agentscope-skills.git

# Make sure the skills directory exists
mkdir -p ~/.cursor/skills/

# Copy the skill as a Cursor rule
cp -r agentscope-skills/skills/{skill_name} ~/.cursor/skills/{skill_name}.md
```

---

## Skills

| Skill            | Path                      | Description                                                      |
|------------------|---------------------------|------------------------------------------------------------------|
| agentscope-skill | `skills/agentscope-skill` | Use this skill when building or working with AgentScope library. |
| Coming soon...   | -                         | -                                                                |

---

## License

This project is licensed under the **Apache License 2.0**. See [LICENSE](./LICENSE) for details.

## Contributors

All thanks to our contributors:

<a href="https://github.com/agentscope-ai/agentscope-skills/graphs/contributors">
  <img src="https://contrib.rocks/image?repo=agentscope-ai/agentscope-skills&max=999&columns=12&anon=1" />
</a>
