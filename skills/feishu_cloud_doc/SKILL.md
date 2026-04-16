---
name: feishu_cloud_doc
description: "当用户需要操作飞书/Lark 云文档时使用此 skill。涵盖四大模块：1) 在线文档（Docx）— 创建、读取、编辑飞书文档；2) 电子表格（Sheets）— 创建、读写飞书表格；3) 多维表格（Bitable）— 创建多维表格、管理字段和记录；4) 知识库（Wiki）— 管理知识空间和节点。触发关键词：飞书文档、飞书表格、飞书多维表格、飞书知识库、Feishu doc、Lark doc、云文档、在线文档、在线表格。不适用于本地 .docx/.xlsx 文件操作（那是 docx/xlsx skill 的职责）。"
metadata:
  builtin_skill_version: "1.0"
  qwenpaw:
    emoji: "📝"
    requires:
      envs: ["FEISHU_APP_ID", "FEISHU_APP_SECRET"]
      bins: []
---

> **Important:** All `scripts/` paths are relative to this skill directory.
> Every script requires `--workspace-dir {working_dir}` to locate `agent.json` with Feishu credentials.
> Run with: `cd {this_skill_dir} && python scripts/xxx.py --workspace-dir {working_dir} ...`
> The `{working_dir}` is your workspace directory (from env context "Working directory").

# Feishu Cloud Document Skill

Operate on Feishu/Lark cloud documents via the Open API. Covers **Documents**, **Spreadsheets**, **Bitables** (multi-dimensional tables), and **Wiki** (knowledge base).

## Prerequisites

- **httpx**: HTTP client (already included in QwenPaw dependencies)
- **Feishu App credentials**: `FEISHU_APP_ID` and `FEISHU_APP_SECRET` (env vars or workspace `agent.json` → `channels.feishu`)
- **App permissions** (enable in Feishu developer console):
  - `docx:document` / `docx:document:readonly` — Documents
  - `sheets:spreadsheet` / `sheets:spreadsheet:readonly` — Spreadsheets
  - `bitable:app` / `bitable:app:readonly` — Bitables
  - `wiki:wiki` / `wiki:wiki:readonly` — Wiki
  - `drive:drive` — Cloud space access
  - `drive:permission` — Permission management (sharing)

## Authentication

All scripts auto-obtain `tenant_access_token`. Credentials resolved in order:
1. Env vars: `FEISHU_APP_ID`, `FEISHU_APP_SECRET`, `FEISHU_DOMAIN`
2. Workspace `agent.json` → `channels.feishu` (via `--workspace-dir` argument)

Set `FEISHU_DOMAIN=lark` for international (Lark) endpoints; default is `feishu` (China).

## Default Permission Behavior

Documents created by the app are initially **private** (only the app bot has access). After creating any document/spreadsheet/bitable, you should:

- **If the user has no specific permission requirements**: Set org-wide link sharing to editable so the user can access it immediately:
  ```bash
  python scripts/share.py --workspace-dir {working_dir} --token TOKEN --type docx --public --link-access tenant_editable
  ```
- **If the user explicitly requests specific permissions** (e.g. "only share with me", "make it read-only", "share with xxx@example.com"): Follow the user's instructions using `share.py` accordingly.

---

## Module 1: Documents (Docx)

### Quick Reference

| Task | Command |
|------|---------|
| Create document | `python scripts/doc_create.py --workspace-dir {working_dir} --title "Title" [--folder TOKEN]` |
| Read plain text | `python scripts/doc_read.py --workspace-dir {working_dir} --doc-id ID --format raw` |
| Read block tree | `python scripts/doc_read.py --workspace-dir {working_dir} --doc-id ID --format blocks` |
| Get doc metadata | `python scripts/doc_read.py --workspace-dir {working_dir} --doc-id ID --format info` |
| Add content blocks | `python scripts/doc_edit.py --workspace-dir {working_dir} --doc-id ID --blocks-json '[...]'` |
| Add from file | `python scripts/doc_edit.py --workspace-dir {working_dir} --doc-id ID --blocks-file path.json` |
| Insert at position | `python scripts/doc_edit.py --workspace-dir {working_dir} --doc-id ID --blocks-json '[...]' --index 0` |
| Delete block by ID | `python scripts/doc_edit.py --workspace-dir {working_dir} --doc-id ID --action delete --block-id BID` |
| Delete by text (substring) | `python scripts/doc_edit.py --workspace-dir {working_dir} --doc-id ID --action delete-by-text --text "content"` |
| Delete by text (exact) | `python scripts/doc_edit.py --workspace-dir {working_dir} --doc-id ID --action delete-by-text --text "content" --exact` |

### Block Types

| Type | Name | Content Key |
|------|------|-------------|
| 2 | Text | `text` |
| 3–8 | Heading 1–6 | `heading1`–`heading6` |
| 9 | Bullet list | `bullet` |
| 10 | Ordered list | `ordered` |
| 12 | Code block | `code` |
| 14 | Divider | — |
| 15 | Callout | `callout` |

### Block Element Structure

```json
{"block_type": 3, "heading1": {"elements": [{"text_run": {"content": "Title", "text_element_style": {"bold": true}}}]}}
```

Code block language codes: 1=PlainText, 7=Python, 12=Java, 15=JavaScript, 22=Go, 33=SQL, 40=Bash

### Example: Create doc with content

```bash
python scripts/doc_create.py --workspace-dir {working_dir} --title "Meeting Notes"
# → get document_id from output, then set permissions via share.py

python scripts/doc_edit.py --workspace-dir {working_dir} --doc-id DOC_ID --blocks-json '[
  {"block_type": 3, "heading1": {"elements": [{"text_run": {"content": "Agenda"}}]}},
  {"block_type": 9, "bullet": {"elements": [{"text_run": {"content": "Item 1"}}]}},
  {"block_type": 9, "bullet": {"elements": [{"text_run": {"content": "Item 2"}}]}}
]'
```

---

## Module 2: Spreadsheets (Sheets)

### Quick Reference

| Task | Command |
|------|---------|
| Create spreadsheet | `python scripts/sheet_create.py --workspace-dir {working_dir} --title "Title" [--folder TOKEN]` |
| Get info | `python scripts/sheet_read.py --workspace-dir {working_dir} --token TOKEN --info` |
| List worksheets | `python scripts/sheet_read.py --workspace-dir {working_dir} --token TOKEN --list-sheets` |
| Read range | `python scripts/sheet_read.py --workspace-dir {working_dir} --token TOKEN --range "SHEET_ID!A1:D10"` |
| Write range | `python scripts/sheet_write.py --workspace-dir {working_dir} --token TOKEN --range "SHEET_ID!A1:B2" --values-json '[["a","b"],[1,2]]'` |
| Append rows | `python scripts/sheet_write.py --workspace-dir {working_dir} --token TOKEN --range "SHEET_ID!A1" --append --values-json '[["c",3]]'` |
| Add worksheet | `python scripts/sheet_write.py --workspace-dir {working_dir} --token TOKEN --add-sheet --sheet-title "Sheet2"` |

### Range Format

The `--range` parameter uses the format `<sheet_identifier>!<cell_range>`.

**Recommended**: Use the worksheet's internal `sheet_id` (e.g. `e4731c!A1:B2`). Get it via `--list-sheets`.

Sheet title (e.g. `Sheet1!A1:B2`) is also accepted — the script auto-resolves it to `sheet_id`. However, using `sheet_id` directly is more reliable and avoids an extra API call.

**Workflow**: Always run `--list-sheets` first to get the `sheet_id`, then use it in subsequent read/write commands.

### Value Types

- String: `"text"`, Number: `123`, Boolean: `true`/`false`, Empty: `null`, Formula: `"=SUM(A1:A10)"`

### Example: Create and populate

```bash
python scripts/sheet_create.py --workspace-dir {working_dir} --title "Q1 Report"
# First, get the sheet_id
python scripts/sheet_read.py --workspace-dir {working_dir} --token TOKEN --list-sheets
# Use sheet_id (e.g. e4731c) from the output
python scripts/sheet_write.py --workspace-dir {working_dir} --token TOKEN --range "e4731c!A1:C1" --values-json '[["Date","Revenue","Cost"]]'
python scripts/sheet_write.py --workspace-dir {working_dir} --token TOKEN --range "e4731c!A2" --append --values-json '[["Jan",50000,30000],["Feb",55000,32000]]'
```

---

## Module 3: Bitable (Multi-dimensional Table)

### Quick Reference

| Task | Command |
|------|---------|
| Create bitable | `python scripts/bitable_manage.py --workspace-dir {working_dir} create --name "Tracker" [--folder TOKEN]` |
| List tables | `python scripts/bitable_manage.py --workspace-dir {working_dir} list-tables --app-token TOKEN` |
| Add table | `python scripts/bitable_manage.py --workspace-dir {working_dir} add-table --app-token TOKEN --table-name "Tasks"` |
| List fields | `python scripts/bitable_manage.py --workspace-dir {working_dir} list-fields --app-token TOKEN --table-id TID` |
| Add field | `python scripts/bitable_manage.py --workspace-dir {working_dir} add-field --app-token TOKEN --table-id TID --field-name "Status" --field-type 3` |
| List records | `python scripts/bitable_records.py --workspace-dir {working_dir} list --app-token TOKEN --table-id TID [--page-size 50]` |
| Get record | `python scripts/bitable_records.py --workspace-dir {working_dir} get --app-token TOKEN --table-id TID --record-id RID` |
| Create record | `python scripts/bitable_records.py --workspace-dir {working_dir} create --app-token TOKEN --table-id TID --fields-json '{...}'` |
| Batch create | `python scripts/bitable_records.py --workspace-dir {working_dir} batch-create --app-token TOKEN --table-id TID --records-json '[...]'` |
| Update record | `python scripts/bitable_records.py --workspace-dir {working_dir} update --app-token TOKEN --table-id TID --record-id RID --fields-json '{...}'` |
| Delete record | `python scripts/bitable_records.py --workspace-dir {working_dir} delete --app-token TOKEN --table-id TID --record-id RID` |

### Field Types

| ID | Type | Value Format |
|----|------|-------------|
| 1 | Text | `"text"` |
| 2 | Number | `123.45` (numeric, but may be returned as string in some cases — always convert with `float()` before arithmetic) |
| 3 | SingleSelect | `"Option A"` |
| 4 | MultiSelect | `["A", "B"]` |
| 5 | DateTime | `1704067200000` (Unix ms) |
| 7 | Checkbox | `true`/`false` |
| 13 | Link | `{"text": "t", "link": "url"}` |

**Important**: Use **field names** (e.g. `"文本"`, `"Status"`) as keys in `fields` when creating/updating records. Get field names via `list-fields`. Field IDs (e.g. `fldXXXXXX`) are also accepted but field names are recommended.

---

## Module 4: Wiki (Knowledge Base)

> **Prerequisite**: The app must be added as a **wiki space collaborator** (editor or admin) before it can create/edit nodes. Ask the user to go to the wiki space settings → member settings → add the app as a member. Without this, all write operations will fail with permission denied.

### Architecture: Structure vs Content

Wiki module manages **structure** (nodes, hierarchy), not content. To write content into a wiki page:
1. Create a node with `wiki.py create-node` → get `obj_token` from the response
2. Use the corresponding content module to edit: `doc_edit.py --doc-id <obj_token>` for docx nodes, `sheet_write.py --token <obj_token>` for sheet nodes, etc.

### Quick Reference

| Task | Command |
|------|---------|
| List spaces | `python scripts/wiki.py --workspace-dir {working_dir} list-spaces` |
| Create space | ⚠️ **Not supported via API** — requires `user_access_token` (OAuth). Ask the user to create the space manually in Feishu, then use `list-spaces` to get the `space_id`. |
| List root nodes | `python scripts/wiki.py --workspace-dir {working_dir} list-nodes --space-id SID` |
| List child nodes | `python scripts/wiki.py --workspace-dir {working_dir} list-nodes --space-id SID --parent-node-token TOKEN` |
| Get node info | `python scripts/wiki.py --workspace-dir {working_dir} get-node --space-id SID --node-token TOKEN` |
| Create doc node | `python scripts/wiki.py --workspace-dir {working_dir} create-node --space-id SID --obj-type docx --title "Page"` |
| Create child node | `python scripts/wiki.py --workspace-dir {working_dir} create-node --space-id SID --obj-type docx --title "Sub" --parent-node-token TOKEN` |
| Move node | `python scripts/wiki.py --workspace-dir {working_dir} move-node --space-id SID --node-token TOKEN --target-parent-token PARENT` |

Supported `--obj-type`: `docx`, `sheet`, `bitable`, `mindnote`, `slides`

**Key concept**: `get-node` returns `obj_token` — use it with the corresponding content module to read/edit (e.g. `doc_edit.py --doc-id <obj_token>` for docx, `sheet_write.py --token <obj_token>` for sheets).

---

## Sharing & Permissions

Use `share.py` to manage permissions for any document type:

```bash
# Share with a user by open_id
python scripts/share.py --workspace-dir {working_dir} --token TOKEN --type docx --member-type openid --member-id ou_xxx --perm view

# Share by email
python scripts/share.py --workspace-dir {working_dir} --token TOKEN --type sheet --member-type email --member-id user@example.com --perm edit

# Set org-wide link sharing
python scripts/share.py --workspace-dir {working_dir} --token TOKEN --type bitable --public --link-access tenant_editable

# Transfer ownership to a user (app must be current owner)
python scripts/share.py --workspace-dir {working_dir} --token TOKEN --type docx --transfer --member-type openid --member-id ou_xxx
```

`--type` values: `docx`, `sheet`, `bitable`, `wiki`, `file`, `folder`
`--perm` values: `view`, `edit`, `full_access`
`--link-access` values: `tenant_readable`, `tenant_editable`, `anyone_readable`, `anyone_editable`
`--transfer`: Transfer document ownership to the specified member (requires `--member-type` and `--member-id`)
---

## Error Handling

All scripts output JSON with `"success": true/false`. Common error codes:
- `99991668`: No permission — check app permissions
- `99991672`: Resource not found
- `99991663`: Invalid access token — token expired or wrong type (some Wiki APIs require `user_access_token`)
- `1254043`: Bitable permission error — add app as collaborator
