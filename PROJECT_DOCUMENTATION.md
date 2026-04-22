

## Bug Fixes & Enhancements

### [enhancement] Changes in server.py

- **File**: `api\server.py`
- **Captured**: 4/22/2026, 11:10:48 PM
- **Category**: enhancement
**Summary:** Modified server.py: 16 lines added, 0 lines removed.
**Files Modified:**
  - `api\server.py` (+16 / -0)
**API Endpoints** (`server.py`):

| Method | Route | Handler | Middleware |
|--------|-------|---------|------------|
| `GET` | `/{full_path:path}` | get | - |
**Schema: `ChatRequest`** (pydantic)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `query` | `str` | ✓ | - |
| `conversation_id` | `Optional[str]` | ✓ | - |
| `user_id` | `str` | ✓ | - |

**Schema: `WhatIfRequest`** (pydantic)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `scenario` | `str` | ✓ | - |

**Schema: `ReportRequest`** (pydantic)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `query` | `str` | ✓ | - |

**Schema: `DataImportRequest`** (pydantic)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `table_name` | `str` | ✓ | - |
| `if_exists` | `str` | ✓ | - |

**Schema: `ConversationUpdate`** (pydantic)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `title` | `str` | ✓ | - |
| `from` | `unknown` | ✓ | - |
| `from` | `unknown` | ✓ | - |
| `healthy` | `unknown` | ✓ | - |
| `return` | `unknown` | ✓ | - |
| `from` | `unknown` | ✓ | - |
| `from` | `unknown` | ✓ | - |
| `from` | `unknown` | ✓ | - |
| `from` | `unknown` | ✓ | - |
| `try` | `kb` | ✓ | - |
| `except` | `unknown` | ✓ | - |
| `return` | `unknown` | ✓ | - |
| `from` | `unknown` | ✓ | - |
| `from` | `unknown` | ✓ | - |
| `from` | `unknown` | ✓ | - |
| `start` | `unknown` | ✓ | - |
| `conv_id` | `unknown` | ✓ | - |
| `if` | `unknown` | ✓ | - |
| `try` | `result_state` | ✓ | - |
| `except` | `unknown` | ✓ | - |
| `duration_ms` | `unknown` | ✓ | - |
| `answer` | `unknown` | ✓ | - |
| `tools` | `unknown` | ✓ | - |
| `user_msg` | `unknown` | ✓ | - |
| `assistant_msg` | `unknown` | ✓ | - |
| `existing` | `unknown` | ✓ | - |
| `existing` | `unknown` | ✓ | - |
| `save_full_conversation` | `unknown` | ✓ | - |
| `try` | `log_query` | ✓ | - |
| `except` | `unknown` | ✓ | - |
| `return` | `unknown` | ✓ | - |
| `if` | `unknown` | ✓ | - |
| `result` | `unknown` | ✓ | - |
| `df` | `unknown` | ✓ | - |
| `if` | `unknown` | ✓ | - |
| `return` | `unknown` | ✓ | - |
| `await` | `unknown` | ✓ | - |
| `try` | `while True` | ✓ | - |
| `except` | `unknown` | ✓ | - |
| `except` | `unknown` | ✓ | - |
| `req` | `unknown` | ✓ | - |
| `return` | `unknown` | ✓ | - |
| `from` | `unknown` | ✓ | - |
| `return` | `unknown` | ✓ | - |
| `from` | `unknown` | ✓ | - |
| `info` | `unknown` | ✓ | - |
| `if` | `unknown` | ✓ | - |
| `return` | `unknown` | ✓ | - |
| `from` | `unknown` | ✓ | - |
| `update_title` | `unknown` | ✓ | - |
| `return` | `unknown` | ✓ | - |
| `from` | `unknown` | ✓ | - |
| `dc` | `unknown` | ✓ | - |
| `return` | `unknown` | ✓ | - |
| `from` | `unknown` | ✓ | - |
| `conv_id` | `unknown` | ✓ | - |
| `return` | `unknown` | ✓ | - |
| `import` | `unknown` | ✓ | - |
| `import` | `unknown` | ✓ | - |
| `from` | `unknown` | ✓ | - |
| `conn` | `unknown` | ✓ | - |
| `tables` | `unknown` | ✓ | - |
| `result` | `unknown` | ✓ | - |
| `for` | `unknown` | ✓ | - |
| `conn` | `unknown` | ✓ | - |
| `return` | `unknown` | ✓ | - |
| `import` | `unknown` | ✓ | - |
| `import` | `unknown` | ✓ | - |
| `from` | `unknown` | ✓ | - |
| `conn` | `unknown` | ✓ | - |
| `cols` | `unknown` | ✓ | - |
| `fks` | `unknown` | ✓ | - |
| `row_count` | `unknown` | ✓ | - |
| `df` | `unknown` | ✓ | - |
| `stats` | `unknown` | ✓ | - |
| `for` | `unknown` | ✓ | - |
| `conn` | `unknown` | ✓ | - |
| `return` | `unknown` | ✓ | - |
| `import` | `unknown` | ✓ | - |
| `from` | `unknown` | ✓ | - |
| `suffix` | `unknown` | ✓ | - |
| `with` | `unknown` | ✓ | - |
| `preview` | `unknown` | ✓ | - |
| `if` | `unknown` | ✓ | - |
| `name` | `unknown` | ✓ | - |
| `full_df` | `unknown` | ✓ | - |
| `result` | `unknown` | ✓ | - |
| `Path` | `unknown` | ✓ | - |
| `if` | `unknown` | ✓ | - |
| `try` | `from sql_agent` | ✓ | - |
| `except` | `unknown` | ✓ | - |
| `return` | `unknown` | ✓ | - |
| `import` | `unknown` | ✓ | - |
| `from` | `unknown` | ✓ | - |
| `suffix` | `unknown` | ✓ | - |
| `with` | `unknown` | ✓ | - |
| `preview` | `unknown` | ✓ | - |
| `Path` | `unknown` | ✓ | - |
| `if` | `unknown` | ✓ | - |
| `preview` | `unknown` | ✓ | - |
| `df` | `unknown` | ✓ | - |
| `if` | `unknown` | ✓ | - |
| `return` | `unknown` | ✓ | - |
| `from` | `unknown` | ✓ | - |
| `result` | `unknown` | ✓ | - |
| `pdf_path` | `unknown` | ✓ | - |
| `if` | `unknown` | ✓ | - |
| `raise` | `unknown` | ✓ | - |
| `from` | `unknown` | ✓ | - |
| `return` | `unknown` | ✓ | - |
| `from` | `unknown` | ✓ | - |
| `path` | `unknown` | ✓ | - |
| `if` | `unknown` | ✓ | - |
| `return` | `unknown` | ✓ | - |
| `from` | `unknown` | ✓ | - |
| `result` | `unknown` | ✓ | - |
| `for` | `unknown` | ✓ | - |
| `return` | `unknown` | ✓ | - |
| `search` | `Optional[str]` | ✓ | - |
| `intent` | `Optional[str]` | ✓ | - |
| `starred` | `bool` | ✓ | - |
| `limit` | `int` | ✓ | - |
| `from` | `unknown` | ✓ | - |
| `return` | `unknown` | ✓ | - |
| `from` | `unknown` | ✓ | - |
| `return` | `unknown` | ✓ | - |
| `from` | `unknown` | ✓ | - |
| `delete_query` | `unknown` | ✓ | - |
| `return` | `unknown` | ✓ | - |
| `from` | `unknown` | ✓ | - |
| `count` | `unknown` | ✓ | - |
| `return` | `unknown` | ✓ | - |
| `from` | `unknown` | ✓ | - |
| `from` | `unknown` | ✓ | - |
| `try` | `stats` | ✓ | - |
| `except` | `unknown` | ✓ | - |
| `return` | `unknown` | ✓ | - |
| `from` | `unknown` | ✓ | - |
| `from` | `unknown` | ✓ | - |
| `from` | `unknown` | ✓ | - |
| `from` | `unknown` | ✓ | - |
| `dest` | `unknown` | ✓ | - |
| `content` | `unknown` | ✓ | - |
| `dest` | `unknown` | ✓ | - |
| `docs` | `unknown` | ✓ | - |
| `if` | `unknown` | ✓ | - |
| `raise` | `unknown` | ✓ | - |
| `from` | `unknown` | ✓ | - |
| `return` | `unknown` | ✓ | - |
| `from` | `unknown` | ✓ | - |
| `return` | `unknown` | ✓ | - |
| `from` | `unknown` | ✓ | - |
| `return` | `unknown` | ✓ | - |
| `from` | `unknown` | ✓ | - |
| `path` | `unknown` | ✓ | - |
| `if` | `unknown` | ✓ | - |
| `raise` | `unknown` | ✓ | - |
| `from` | `unknown` | ✓ | - |

### [bugfix] Changes in Chat.jsx

- **File**: `frontend\src\pages\Chat.jsx`
- **Captured**: 4/22/2026, 11:09:50 PM
- **Category**: bugfix
**Summary:** Modified Chat.jsx: 291 lines added, 142 lines removed.
**Files Modified:**
  - `frontend\src\pages\Chat.jsx` (+291 / -142)

### [bugfix] Changes in scheduler.py

- **File**: `workflows\scheduler.py`
- **Captured**: 4/22/2026, 11:07:54 PM
- **Category**: bugfix
**Summary:** Modified scheduler.py: 191 lines added, 0 lines removed.
**Files Modified:**
  - `workflows\scheduler.py` (+191 / -0)

### [bugfix] Changes in email_tool.py

- **File**: `action_tools\email_tool.py`
- **Captured**: 4/22/2026, 11:07:40 PM
- **Category**: bugfix
**Summary:** Modified email_tool.py: 184 lines added, 0 lines removed.
**Files Modified:**
  - `action_tools\email_tool.py` (+184 / -0)

### [bugfix] Changes in server.py

- **File**: `api\server.py`
- **Captured**: 4/22/2026, 11:07:11 PM
- **Category**: bugfix
**Summary:** Modified server.py: 149 lines added, 1 lines removed.
**Files Modified:**
  - `api\server.py` (+149 / -1)
**API Endpoints** (`server.py`):

| Method | Route | Handler | Middleware |
|--------|-------|---------|------------|
| `POST` | `/api/voice/transcribe` | post | - |
| `POST` | `/api/email/send` | post | - |
| `POST` | `/api/webhooks/{webhook_path:path}` | post | - |
| `POST` | `/api/settings/update` | post | - |
**Schema: `ChatRequest`** (pydantic)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `query` | `str` | ✓ | - |
| `conversation_id` | `Optional[str]` | ✓ | - |
| `user_id` | `str` | ✓ | - |

**Schema: `WhatIfRequest`** (pydantic)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `scenario` | `str` | ✓ | - |

**Schema: `ReportRequest`** (pydantic)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `query` | `str` | ✓ | - |

**Schema: `DataImportRequest`** (pydantic)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `table_name` | `str` | ✓ | - |
| `if_exists` | `str` | ✓ | - |

**Schema: `ConversationUpdate`** (pydantic)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `title` | `str` | ✓ | - |
| `from` | `unknown` | ✓ | - |
| `from` | `unknown` | ✓ | - |
| `healthy` | `unknown` | ✓ | - |
| `return` | `unknown` | ✓ | - |
| `from` | `unknown` | ✓ | - |
| `from` | `unknown` | ✓ | - |
| `from` | `unknown` | ✓ | - |
| `from` | `unknown` | ✓ | - |
| `try` | `kb` | ✓ | - |
| `except` | `unknown` | ✓ | - |
| `return` | `unknown` | ✓ | - |
| `from` | `unknown` | ✓ | - |
| `from` | `unknown` | ✓ | - |
| `from` | `unknown` | ✓ | - |
| `start` | `unknown` | ✓ | - |
| `conv_id` | `unknown` | ✓ | - |
| `if` | `unknown` | ✓ | - |
| `try` | `result_state` | ✓ | - |
| `except` | `unknown` | ✓ | - |
| `duration_ms` | `unknown` | ✓ | - |
| `answer` | `unknown` | ✓ | - |
| `tools` | `unknown` | ✓ | - |
| `user_msg` | `unknown` | ✓ | - |
| `assistant_msg` | `unknown` | ✓ | - |
| `existing` | `unknown` | ✓ | - |
| `existing` | `unknown` | ✓ | - |
| `save_full_conversation` | `unknown` | ✓ | - |
| `try` | `log_query` | ✓ | - |
| `except` | `unknown` | ✓ | - |
| `return` | `unknown` | ✓ | - |
| `if` | `unknown` | ✓ | - |
| `result` | `unknown` | ✓ | - |
| `df` | `unknown` | ✓ | - |
| `if` | `unknown` | ✓ | - |
| `return` | `unknown` | ✓ | - |
| `await` | `unknown` | ✓ | - |
| `try` | `while True` | ✓ | - |
| `except` | `unknown` | ✓ | - |
| `except` | `unknown` | ✓ | - |
| `req` | `unknown` | ✓ | - |
| `return` | `unknown` | ✓ | - |
| `from` | `unknown` | ✓ | - |
| `return` | `unknown` | ✓ | - |
| `from` | `unknown` | ✓ | - |
| `info` | `unknown` | ✓ | - |
| `if` | `unknown` | ✓ | - |
| `return` | `unknown` | ✓ | - |
| `from` | `unknown` | ✓ | - |
| `update_title` | `unknown` | ✓ | - |
| `return` | `unknown` | ✓ | - |
| `from` | `unknown` | ✓ | - |
| `dc` | `unknown` | ✓ | - |
| `return` | `unknown` | ✓ | - |
| `from` | `unknown` | ✓ | - |
| `conv_id` | `unknown` | ✓ | - |
| `return` | `unknown` | ✓ | - |
| `import` | `unknown` | ✓ | - |
| `import` | `unknown` | ✓ | - |
| `from` | `unknown` | ✓ | - |
| `conn` | `unknown` | ✓ | - |
| `tables` | `unknown` | ✓ | - |
| `result` | `unknown` | ✓ | - |
| `for` | `unknown` | ✓ | - |
| `conn` | `unknown` | ✓ | - |
| `return` | `unknown` | ✓ | - |
| `import` | `unknown` | ✓ | - |
| `import` | `unknown` | ✓ | - |
| `from` | `unknown` | ✓ | - |
| `conn` | `unknown` | ✓ | - |
| `cols` | `unknown` | ✓ | - |
| `fks` | `unknown` | ✓ | - |
| `row_count` | `unknown` | ✓ | - |
| `df` | `unknown` | ✓ | - |
| `stats` | `unknown` | ✓ | - |
| `for` | `unknown` | ✓ | - |
| `conn` | `unknown` | ✓ | - |
| `return` | `unknown` | ✓ | - |
| `import` | `unknown` | ✓ | - |
| `from` | `unknown` | ✓ | - |
| `suffix` | `unknown` | ✓ | - |
| `with` | `unknown` | ✓ | - |
| `preview` | `unknown` | ✓ | - |
| `if` | `unknown` | ✓ | - |
| `name` | `unknown` | ✓ | - |
| `full_df` | `unknown` | ✓ | - |
| `result` | `unknown` | ✓ | - |
| `Path` | `unknown` | ✓ | - |
| `if` | `unknown` | ✓ | - |
| `try` | `from sql_agent` | ✓ | - |
| `except` | `unknown` | ✓ | - |
| `return` | `unknown` | ✓ | - |
| `import` | `unknown` | ✓ | - |
| `from` | `unknown` | ✓ | - |
| `suffix` | `unknown` | ✓ | - |
| `with` | `unknown` | ✓ | - |
| `preview` | `unknown` | ✓ | - |
| `Path` | `unknown` | ✓ | - |
| `if` | `unknown` | ✓ | - |
| `preview` | `unknown` | ✓ | - |
| `df` | `unknown` | ✓ | - |
| `if` | `unknown` | ✓ | - |
| `return` | `unknown` | ✓ | - |
| `from` | `unknown` | ✓ | - |
| `result` | `unknown` | ✓ | - |
| `pdf_path` | `unknown` | ✓ | - |
| `if` | `unknown` | ✓ | - |
| `raise` | `unknown` | ✓ | - |
| `from` | `unknown` | ✓ | - |
| `return` | `unknown` | ✓ | - |
| `from` | `unknown` | ✓ | - |
| `path` | `unknown` | ✓ | - |
| `if` | `unknown` | ✓ | - |
| `return` | `unknown` | ✓ | - |
| `from` | `unknown` | ✓ | - |
| `result` | `unknown` | ✓ | - |
| `for` | `unknown` | ✓ | - |
| `return` | `unknown` | ✓ | - |
| `search` | `Optional[str]` | ✓ | - |
| `intent` | `Optional[str]` | ✓ | - |
| `starred` | `bool` | ✓ | - |
| `limit` | `int` | ✓ | - |
| `from` | `unknown` | ✓ | - |
| `return` | `unknown` | ✓ | - |
| `from` | `unknown` | ✓ | - |
| `return` | `unknown` | ✓ | - |
| `from` | `unknown` | ✓ | - |
| `delete_query` | `unknown` | ✓ | - |
| `return` | `unknown` | ✓ | - |
| `from` | `unknown` | ✓ | - |
| `count` | `unknown` | ✓ | - |
| `return` | `unknown` | ✓ | - |
| `from` | `unknown` | ✓ | - |
| `from` | `unknown` | ✓ | - |
| `try` | `stats` | ✓ | - |
| `except` | `unknown` | ✓ | - |
| `return` | `unknown` | ✓ | - |
| `from` | `unknown` | ✓ | - |
| `from` | `unknown` | ✓ | - |
| `from` | `unknown` | ✓ | - |
| `from` | `unknown` | ✓ | - |
| `dest` | `unknown` | ✓ | - |
| `content` | `unknown` | ✓ | - |
| `dest` | `unknown` | ✓ | - |
| `docs` | `unknown` | ✓ | - |
| `if` | `unknown` | ✓ | - |
| `raise` | `unknown` | ✓ | - |
| `from` | `unknown` | ✓ | - |
| `return` | `unknown` | ✓ | - |
| `from` | `unknown` | ✓ | - |
| `return` | `unknown` | ✓ | - |
| `from` | `unknown` | ✓ | - |
| `return` | `unknown` | ✓ | - |
| `from` | `unknown` | ✓ | - |
| `path` | `unknown` | ✓ | - |
| `if` | `unknown` | ✓ | - |
| `raise` | `unknown` | ✓ | - |
| `from` | `unknown` | ✓ | - |

### [bugfix] Changes in Workflows.jsx

- **File**: `frontend\src\pages\Workflows.jsx`
- **Captured**: 4/22/2026, 10:18:39 PM
- **Category**: bugfix
**Summary:** Modified Workflows.jsx: 344 lines added, 292 lines removed.
**Files Modified:**
  - `frontend\src\pages\Workflows.jsx` (+344 / -292)

### [bugfix] Changes in templates.py

- **File**: `workflows\templates.py`
- **Captured**: 4/22/2026, 10:17:07 PM
- **Category**: bugfix
**Summary:** Modified templates.py: 363 lines added, 0 lines removed.
**Files Modified:**
  - `workflows\templates.py` (+363 / -0)

### [bugfix] Changes in Workflows.jsx

- **File**: `frontend\src\pages\Workflows.jsx`
- **Captured**: 4/22/2026, 10:05:35 PM
- **Category**: bugfix
**Summary:** Modified Workflows.jsx: 371 lines added, 0 lines removed.
**Files Modified:**
  - `frontend\src\pages\Workflows.jsx` (+371 / -0)

### [enhancement] Changes in server.py

- **File**: `api\server.py`
- **Captured**: 4/22/2026, 10:04:12 PM
- **Category**: enhancement
**Summary:** Modified server.py: 78 lines added, 1 lines removed.
**Files Modified:**
  - `api\server.py` (+78 / -1)
**API Endpoints** (`server.py`):

| Method | Route | Handler | Middleware |
|--------|-------|---------|------------|
| `GET` | `/api/workflows` | get | - |
| `GET` | `/api/workflows/node-types` | get | - |
| `GET` | `/api/workflows/templates` | get | - |
| `GET` | `/api/workflows/{wf_id}` | get | - |
| `POST` | `/api/workflows` | post | - |
| `DELETE` | `/api/workflows/{wf_id}` | delete | - |
| `POST` | `/api/workflows/{wf_id}/toggle` | post | - |
| `POST` | `/api/workflows/{wf_id}/run` | post | - |
| `POST` | `/api/workflows/run-preview` | post | - |
| `GET` | `/api/workflows/scheduler/jobs` | get | - |
| `GET` | `/api/workflows/scheduler/history` | get | - |
**Schema: `ChatRequest`** (pydantic)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `query` | `str` | ✓ | - |
| `conversation_id` | `Optional[str]` | ✓ | - |
| `user_id` | `str` | ✓ | - |

**Schema: `WhatIfRequest`** (pydantic)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `scenario` | `str` | ✓ | - |

**Schema: `ReportRequest`** (pydantic)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `query` | `str` | ✓ | - |

**Schema: `DataImportRequest`** (pydantic)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `table_name` | `str` | ✓ | - |
| `if_exists` | `str` | ✓ | - |

**Schema: `ConversationUpdate`** (pydantic)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `title` | `str` | ✓ | - |
| `from` | `unknown` | ✓ | - |
| `from` | `unknown` | ✓ | - |
| `healthy` | `unknown` | ✓ | - |
| `return` | `unknown` | ✓ | - |
| `from` | `unknown` | ✓ | - |
| `from` | `unknown` | ✓ | - |
| `from` | `unknown` | ✓ | - |
| `from` | `unknown` | ✓ | - |
| `try` | `kb` | ✓ | - |
| `except` | `unknown` | ✓ | - |
| `return` | `unknown` | ✓ | - |
| `from` | `unknown` | ✓ | - |
| `from` | `unknown` | ✓ | - |
| `from` | `unknown` | ✓ | - |
| `start` | `unknown` | ✓ | - |
| `conv_id` | `unknown` | ✓ | - |
| `if` | `unknown` | ✓ | - |
| `try` | `result_state` | ✓ | - |
| `except` | `unknown` | ✓ | - |
| `duration_ms` | `unknown` | ✓ | - |
| `answer` | `unknown` | ✓ | - |
| `tools` | `unknown` | ✓ | - |
| `user_msg` | `unknown` | ✓ | - |
| `assistant_msg` | `unknown` | ✓ | - |
| `existing` | `unknown` | ✓ | - |
| `existing` | `unknown` | ✓ | - |
| `save_full_conversation` | `unknown` | ✓ | - |
| `try` | `log_query` | ✓ | - |
| `except` | `unknown` | ✓ | - |
| `return` | `unknown` | ✓ | - |
| `if` | `unknown` | ✓ | - |
| `result` | `unknown` | ✓ | - |
| `df` | `unknown` | ✓ | - |
| `if` | `unknown` | ✓ | - |
| `return` | `unknown` | ✓ | - |
| `await` | `unknown` | ✓ | - |
| `try` | `while True` | ✓ | - |
| `except` | `unknown` | ✓ | - |
| `except` | `unknown` | ✓ | - |
| `req` | `unknown` | ✓ | - |
| `return` | `unknown` | ✓ | - |
| `from` | `unknown` | ✓ | - |
| `return` | `unknown` | ✓ | - |
| `from` | `unknown` | ✓ | - |
| `info` | `unknown` | ✓ | - |
| `if` | `unknown` | ✓ | - |
| `return` | `unknown` | ✓ | - |
| `from` | `unknown` | ✓ | - |
| `update_title` | `unknown` | ✓ | - |
| `return` | `unknown` | ✓ | - |
| `from` | `unknown` | ✓ | - |
| `dc` | `unknown` | ✓ | - |
| `return` | `unknown` | ✓ | - |
| `from` | `unknown` | ✓ | - |
| `conv_id` | `unknown` | ✓ | - |
| `return` | `unknown` | ✓ | - |
| `import` | `unknown` | ✓ | - |
| `import` | `unknown` | ✓ | - |
| `from` | `unknown` | ✓ | - |
| `conn` | `unknown` | ✓ | - |
| `tables` | `unknown` | ✓ | - |
| `result` | `unknown` | ✓ | - |
| `for` | `unknown` | ✓ | - |
| `conn` | `unknown` | ✓ | - |
| `return` | `unknown` | ✓ | - |
| `import` | `unknown` | ✓ | - |
| `import` | `unknown` | ✓ | - |
| `from` | `unknown` | ✓ | - |
| `conn` | `unknown` | ✓ | - |
| `cols` | `unknown` | ✓ | - |
| `fks` | `unknown` | ✓ | - |
| `row_count` | `unknown` | ✓ | - |
| `df` | `unknown` | ✓ | - |
| `stats` | `unknown` | ✓ | - |
| `for` | `unknown` | ✓ | - |
| `conn` | `unknown` | ✓ | - |
| `return` | `unknown` | ✓ | - |
| `import` | `unknown` | ✓ | - |
| `from` | `unknown` | ✓ | - |
| `suffix` | `unknown` | ✓ | - |
| `with` | `unknown` | ✓ | - |
| `preview` | `unknown` | ✓ | - |
| `if` | `unknown` | ✓ | - |
| `name` | `unknown` | ✓ | - |
| `full_df` | `unknown` | ✓ | - |
| `result` | `unknown` | ✓ | - |
| `Path` | `unknown` | ✓ | - |
| `if` | `unknown` | ✓ | - |
| `try` | `from sql_agent` | ✓ | - |
| `except` | `unknown` | ✓ | - |
| `return` | `unknown` | ✓ | - |
| `import` | `unknown` | ✓ | - |
| `from` | `unknown` | ✓ | - |
| `suffix` | `unknown` | ✓ | - |
| `with` | `unknown` | ✓ | - |
| `preview` | `unknown` | ✓ | - |
| `Path` | `unknown` | ✓ | - |
| `if` | `unknown` | ✓ | - |
| `preview` | `unknown` | ✓ | - |
| `df` | `unknown` | ✓ | - |
| `if` | `unknown` | ✓ | - |
| `return` | `unknown` | ✓ | - |
| `from` | `unknown` | ✓ | - |
| `result` | `unknown` | ✓ | - |
| `pdf_path` | `unknown` | ✓ | - |
| `if` | `unknown` | ✓ | - |
| `raise` | `unknown` | ✓ | - |
| `from` | `unknown` | ✓ | - |
| `return` | `unknown` | ✓ | - |
| `from` | `unknown` | ✓ | - |
| `path` | `unknown` | ✓ | - |
| `if` | `unknown` | ✓ | - |
| `return` | `unknown` | ✓ | - |
| `from` | `unknown` | ✓ | - |
| `result` | `unknown` | ✓ | - |
| `for` | `unknown` | ✓ | - |
| `return` | `unknown` | ✓ | - |
| `search` | `Optional[str]` | ✓ | - |
| `intent` | `Optional[str]` | ✓ | - |
| `starred` | `bool` | ✓ | - |
| `limit` | `int` | ✓ | - |
| `from` | `unknown` | ✓ | - |
| `return` | `unknown` | ✓ | - |
| `from` | `unknown` | ✓ | - |
| `return` | `unknown` | ✓ | - |
| `from` | `unknown` | ✓ | - |
| `delete_query` | `unknown` | ✓ | - |
| `return` | `unknown` | ✓ | - |
| `from` | `unknown` | ✓ | - |
| `count` | `unknown` | ✓ | - |
| `return` | `unknown` | ✓ | - |
| `from` | `unknown` | ✓ | - |
| `from` | `unknown` | ✓ | - |
| `try` | `stats` | ✓ | - |
| `except` | `unknown` | ✓ | - |
| `return` | `unknown` | ✓ | - |
| `from` | `unknown` | ✓ | - |
| `from` | `unknown` | ✓ | - |
| `from` | `unknown` | ✓ | - |
| `from` | `unknown` | ✓ | - |
| `dest` | `unknown` | ✓ | - |
| `content` | `unknown` | ✓ | - |
| `dest` | `unknown` | ✓ | - |
| `docs` | `unknown` | ✓ | - |
| `if` | `unknown` | ✓ | - |
| `raise` | `unknown` | ✓ | - |
| `from` | `unknown` | ✓ | - |
| `return` | `unknown` | ✓ | - |
| `from` | `unknown` | ✓ | - |
| `return` | `unknown` | ✓ | - |
| `from` | `unknown` | ✓ | - |
| `return` | `unknown` | ✓ | - |
| `from` | `unknown` | ✓ | - |
| `path` | `unknown` | ✓ | - |
| `if` | `unknown` | ✓ | - |
| `raise` | `unknown` | ✓ | - |
| `from` | `unknown` | ✓ | - |

### [bugfix] Changes in data_import.py

- **File**: `sql_agent\data_import.py`
- **Captured**: 4/22/2026, 9:47:36 PM
- **Category**: bugfix
**Summary:** Modified data_import.py: 45 lines added, 263 lines removed.
**Files Modified:**
  - `sql_agent\data_import.py` (+45 / -263)

### [bugfix] Changes in index-BsJbQkw1.js

- **File**: `frontend\dist\assets\index-BsJbQkw1.js`
- **Captured**: 4/22/2026, 9:39:14 PM
- **Category**: bugfix
**Summary:** Modified index-BsJbQkw1.js: 24 lines added, 0 lines removed.
**Files Modified:**
  - `frontend\dist\assets\index-BsJbQkw1.js` (+24 / -0)

### [bugfix] Changes in Settings.jsx

- **File**: `frontend\src\pages\Settings.jsx`
- **Captured**: 4/22/2026, 9:39:02 PM
- **Category**: bugfix
**Summary:** Modified Settings.jsx: 46 lines added, 87 lines removed.
**Files Modified:**
  - `frontend\src\pages\Settings.jsx` (+46 / -87)

### [bugfix] Changes in History.jsx

- **File**: `frontend\src\pages\History.jsx`
- **Captured**: 4/22/2026, 9:38:41 PM
- **Category**: bugfix
**Summary:** Modified History.jsx: 59 lines added, 108 lines removed.
**Files Modified:**
  - `frontend\src\pages\History.jsx` (+59 / -108)

### [bugfix] Changes in Reports.jsx

- **File**: `frontend\src\pages\Reports.jsx`
- **Captured**: 4/22/2026, 9:38:21 PM
- **Category**: bugfix
**Summary:** Modified Reports.jsx: 38 lines added, 61 lines removed.
**Files Modified:**
  - `frontend\src\pages\Reports.jsx` (+38 / -61)

### [bugfix] Changes in WhatIf.jsx

- **File**: `frontend\src\pages\WhatIf.jsx`
- **Captured**: 4/22/2026, 9:38:06 PM
- **Category**: bugfix
**Summary:** Modified WhatIf.jsx: 42 lines added, 85 lines removed.
**Files Modified:**
  - `frontend\src\pages\WhatIf.jsx` (+42 / -85)

### [bugfix] Changes in Database.jsx

- **File**: `frontend\src\pages\Database.jsx`
- **Captured**: 4/22/2026, 9:37:48 PM
- **Category**: bugfix
**Summary:** Modified Database.jsx: 101 lines added, 175 lines removed.
**Files Modified:**
  - `frontend\src\pages\Database.jsx` (+101 / -175)

### [bugfix] Changes in Chat.jsx

- **File**: `frontend\src\pages\Chat.jsx`
- **Captured**: 4/22/2026, 9:37:16 PM
- **Category**: bugfix
**Summary:** Modified Chat.jsx: 68 lines added, 154 lines removed.
**Files Modified:**
  - `frontend\src\pages\Chat.jsx` (+68 / -154)

### [enhancement] Changes in Layout.jsx

- **File**: `frontend\src\components\Layout.jsx`
- **Captured**: 4/22/2026, 9:36:46 PM
- **Category**: enhancement
**Summary:** Modified Layout.jsx: 33 lines added, 37 lines removed.
**Files Modified:**
  - `frontend\src\components\Layout.jsx` (+33 / -37)

### [bugfix] Changes in data_import.py

- **File**: `sql_agent\data_import.py`
- **Captured**: 4/22/2026, 9:28:51 PM
- **Category**: bugfix
**Summary:** Modified data_import.py: 63 lines added, 215 lines removed.
**Files Modified:**
  - `sql_agent\data_import.py` (+63 / -215)

### [bugfix] Changes in index-DwQRvi4P.js

- **File**: `frontend\dist\assets\index-DwQRvi4P.js`
- **Captured**: 4/22/2026, 9:25:05 PM
- **Category**: bugfix
**Summary:** Modified index-DwQRvi4P.js: 24 lines added, 0 lines removed.
**Files Modified:**
  - `frontend\dist\assets\index-DwQRvi4P.js` (+24 / -0)

### [bugfix] Changes in Settings.jsx

- **File**: `frontend\src\pages\Settings.jsx`
- **Captured**: 4/22/2026, 9:12:41 PM
- **Category**: bugfix
**Summary:** Modified Settings.jsx: 121 lines added, 0 lines removed.
**Files Modified:**
  - `frontend\src\pages\Settings.jsx` (+121 / -0)

### [bugfix] Changes in History.jsx

- **File**: `frontend\src\pages\History.jsx`
- **Captured**: 4/22/2026, 9:12:18 PM
- **Category**: bugfix
**Summary:** Modified History.jsx: 124 lines added, 0 lines removed.
**Files Modified:**
  - `frontend\src\pages\History.jsx` (+124 / -0)

### [bugfix] Changes in Reports.jsx

- **File**: `frontend\src\pages\Reports.jsx`
- **Captured**: 4/22/2026, 9:11:54 PM
- **Category**: bugfix
**Summary:** Modified Reports.jsx: 86 lines added, 0 lines removed.
**Files Modified:**
  - `frontend\src\pages\Reports.jsx` (+86 / -0)

### [bugfix] Changes in WhatIf.jsx

- **File**: `frontend\src\pages\WhatIf.jsx`
- **Captured**: 4/22/2026, 9:11:36 PM
- **Category**: bugfix
**Summary:** Modified WhatIf.jsx: 110 lines added, 0 lines removed.
**Files Modified:**
  - `frontend\src\pages\WhatIf.jsx` (+110 / -0)

### [bugfix] Changes in Database.jsx

- **File**: `frontend\src\pages\Database.jsx`
- **Captured**: 4/22/2026, 9:11:10 PM
- **Category**: bugfix
**Summary:** Modified Database.jsx: 214 lines added, 0 lines removed.
**Files Modified:**
  - `frontend\src\pages\Database.jsx` (+214 / -0)

### [bugfix] Changes in Chat.jsx

- **File**: `frontend\src\pages\Chat.jsx`
- **Captured**: 4/22/2026, 9:10:31 PM
- **Category**: bugfix
**Summary:** Modified Chat.jsx: 229 lines added, 0 lines removed.
**Files Modified:**
  - `frontend\src\pages\Chat.jsx` (+229 / -0)

### [bugfix] Changes in Layout.jsx

- **File**: `frontend\src\components\Layout.jsx`
- **Captured**: 4/22/2026, 9:09:50 PM
- **Category**: bugfix
**Summary:** Modified Layout.jsx: 104 lines added, 0 lines removed.
**Files Modified:**
  - `frontend\src\components\Layout.jsx` (+104 / -0)

### [bugfix] Changes in api.js

- **File**: `frontend\src\services\api.js`
- **Captured**: 4/22/2026, 9:09:08 PM
- **Category**: bugfix
**Summary:** Modified api.js: 100 lines added, 0 lines removed.
**Files Modified:**
  - `frontend\src\services\api.js` (+100 / -0)

### [enhancement] Changes in vite.config.js

- **File**: `frontend\vite.config.js`
- **Captured**: 4/22/2026, 9:08:06 PM
- **Category**: enhancement
**Summary:** Modified vite.config.js: 9 lines added, 2 lines removed.
**Files Modified:**
  - `frontend\vite.config.js` (+9 / -2)
**Config change** in `vite.config.js`: 9 lines added, 2 lines removed
Changed keys: `plugins`, `server`, `port`, `proxy`, `api`, `http`, `localhost`, `ws`, `target`, `https`

### [enhancement] Changes in main.jsx

- **File**: `frontend\src\main.jsx`
- **Captured**: 4/22/2026, 9:05:50 PM
- **Category**: enhancement
**Summary:** Modified main.jsx: 11 lines added, 0 lines removed.
**Files Modified:**
  - `frontend\src\main.jsx` (+11 / -0)

### [bugfix] Changes in server.py

- **File**: `api\server.py`
- **Captured**: 4/22/2026, 9:04:09 PM
- **Category**: bugfix
**Summary:** Modified server.py: 612 lines added, 0 lines removed.
**Files Modified:**
  - `api\server.py` (+612 / -0)
**API Endpoints** (`server.py`):

| Method | Route | Handler | Middleware |
|--------|-------|---------|------------|
| `GET` | `/api/health` | get | - |
| `GET` | `/api/stats` | get | - |
| `POST` | `/api/chat` | post | - |
| `GET` | `/api/conversations` | get | - |
| `GET` | `/api/conversations/{conv_id}` | get | - |
| `PATCH` | `/api/conversations/{conv_id}` | patch | - |
| `DELETE` | `/api/conversations/{conv_id}` | delete | - |
| `POST` | `/api/conversations` | post | - |
| `GET` | `/api/database/tables` | get | - |
| `GET` | `/api/database/tables/{table_name}` | get | - |
| `POST` | `/api/database/import` | post | - |
| `POST` | `/api/database/import/preview` | post | - |
| `POST` | `/api/reports/generate` | post | - |
| `GET` | `/api/reports` | get | - |
| `GET` | `/api/reports/download/{filename}` | get | - |
| `POST` | `/api/whatif` | post | - |
| `GET` | `/api/history` | get | - |
| `POST` | `/api/history/{query_id}/star` | post | - |
| `DELETE` | `/api/history/{query_id}` | delete | - |
| `DELETE` | `/api/history` | delete | - |
| `GET` | `/api/knowledge` | get | - |
| `POST` | `/api/knowledge/upload` | post | upload |
| `GET` | `/api/monitor/status` | get | - |
| `POST` | `/api/monitor/run` | post | - |
| `POST` | `/api/export/markdown` | post | - |
| `POST` | `/api/export/pdf` | post | - |
| `GET` | `/api/settings` | get | - |
| `POST` | `/api/settings/reset-llm` | post | - |
| `POST` | `/api/settings/clear-cache` | post | cache |
**Schema: `ChatRequest`** (pydantic)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `query` | `str` | ✓ | - |
| `conversation_id` | `Optional[str]` | ✓ | - |
| `user_id` | `str` | ✓ | - |

**Schema: `WhatIfRequest`** (pydantic)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `scenario` | `str` | ✓ | - |

**Schema: `ReportRequest`** (pydantic)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `query` | `str` | ✓ | - |

**Schema: `DataImportRequest`** (pydantic)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `table_name` | `str` | ✓ | - |
| `if_exists` | `str` | ✓ | - |

**Schema: `ConversationUpdate`** (pydantic)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `title` | `str` | ✓ | - |
| `from` | `unknown` | ✓ | - |
| `from` | `unknown` | ✓ | - |
| `healthy` | `unknown` | ✓ | - |
| `return` | `unknown` | ✓ | - |
| `from` | `unknown` | ✓ | - |
| `from` | `unknown` | ✓ | - |
| `from` | `unknown` | ✓ | - |
| `from` | `unknown` | ✓ | - |
| `try` | `kb` | ✓ | - |
| `except` | `unknown` | ✓ | - |
| `return` | `unknown` | ✓ | - |
| `from` | `unknown` | ✓ | - |
| `from` | `unknown` | ✓ | - |
| `from` | `unknown` | ✓ | - |
| `start` | `unknown` | ✓ | - |
| `conv_id` | `unknown` | ✓ | - |
| `if` | `unknown` | ✓ | - |
| `try` | `result_state` | ✓ | - |
| `except` | `unknown` | ✓ | - |
| `duration_ms` | `unknown` | ✓ | - |
| `answer` | `unknown` | ✓ | - |
| `tools` | `unknown` | ✓ | - |
| `user_msg` | `unknown` | ✓ | - |
| `assistant_msg` | `unknown` | ✓ | - |
| `existing` | `unknown` | ✓ | - |
| `existing` | `unknown` | ✓ | - |
| `save_full_conversation` | `unknown` | ✓ | - |
| `try` | `log_query` | ✓ | - |
| `except` | `unknown` | ✓ | - |
| `return` | `unknown` | ✓ | - |
| `if` | `unknown` | ✓ | - |
| `result` | `unknown` | ✓ | - |
| `df` | `unknown` | ✓ | - |
| `if` | `unknown` | ✓ | - |
| `return` | `unknown` | ✓ | - |
| `await` | `unknown` | ✓ | - |
| `try` | `while True` | ✓ | - |
| `except` | `unknown` | ✓ | - |
| `except` | `unknown` | ✓ | - |
| `req` | `unknown` | ✓ | - |
| `return` | `unknown` | ✓ | - |
| `from` | `unknown` | ✓ | - |
| `return` | `unknown` | ✓ | - |
| `from` | `unknown` | ✓ | - |
| `info` | `unknown` | ✓ | - |
| `if` | `unknown` | ✓ | - |
| `return` | `unknown` | ✓ | - |
| `from` | `unknown` | ✓ | - |
| `update_title` | `unknown` | ✓ | - |
| `return` | `unknown` | ✓ | - |
| `from` | `unknown` | ✓ | - |
| `dc` | `unknown` | ✓ | - |
| `return` | `unknown` | ✓ | - |
| `from` | `unknown` | ✓ | - |
| `conv_id` | `unknown` | ✓ | - |
| `return` | `unknown` | ✓ | - |
| `import` | `unknown` | ✓ | - |
| `import` | `unknown` | ✓ | - |
| `from` | `unknown` | ✓ | - |
| `conn` | `unknown` | ✓ | - |
| `tables` | `unknown` | ✓ | - |
| `result` | `unknown` | ✓ | - |
| `for` | `unknown` | ✓ | - |
| `conn` | `unknown` | ✓ | - |
| `return` | `unknown` | ✓ | - |
| `import` | `unknown` | ✓ | - |
| `import` | `unknown` | ✓ | - |
| `from` | `unknown` | ✓ | - |
| `conn` | `unknown` | ✓ | - |
| `cols` | `unknown` | ✓ | - |
| `fks` | `unknown` | ✓ | - |
| `row_count` | `unknown` | ✓ | - |
| `df` | `unknown` | ✓ | - |
| `stats` | `unknown` | ✓ | - |
| `for` | `unknown` | ✓ | - |
| `conn` | `unknown` | ✓ | - |
| `return` | `unknown` | ✓ | - |
| `import` | `unknown` | ✓ | - |
| `from` | `unknown` | ✓ | - |
| `suffix` | `unknown` | ✓ | - |
| `with` | `unknown` | ✓ | - |
| `preview` | `unknown` | ✓ | - |
| `if` | `unknown` | ✓ | - |
| `name` | `unknown` | ✓ | - |
| `full_df` | `unknown` | ✓ | - |
| `result` | `unknown` | ✓ | - |
| `Path` | `unknown` | ✓ | - |
| `if` | `unknown` | ✓ | - |
| `try` | `from sql_agent` | ✓ | - |
| `except` | `unknown` | ✓ | - |
| `return` | `unknown` | ✓ | - |
| `import` | `unknown` | ✓ | - |
| `from` | `unknown` | ✓ | - |
| `suffix` | `unknown` | ✓ | - |
| `with` | `unknown` | ✓ | - |
| `preview` | `unknown` | ✓ | - |
| `Path` | `unknown` | ✓ | - |
| `if` | `unknown` | ✓ | - |
| `preview` | `unknown` | ✓ | - |
| `df` | `unknown` | ✓ | - |
| `if` | `unknown` | ✓ | - |
| `return` | `unknown` | ✓ | - |
| `from` | `unknown` | ✓ | - |
| `result` | `unknown` | ✓ | - |
| `pdf_path` | `unknown` | ✓ | - |
| `if` | `unknown` | ✓ | - |
| `raise` | `unknown` | ✓ | - |
| `from` | `unknown` | ✓ | - |
| `return` | `unknown` | ✓ | - |
| `from` | `unknown` | ✓ | - |
| `path` | `unknown` | ✓ | - |
| `if` | `unknown` | ✓ | - |
| `return` | `unknown` | ✓ | - |
| `from` | `unknown` | ✓ | - |
| `result` | `unknown` | ✓ | - |
| `for` | `unknown` | ✓ | - |
| `return` | `unknown` | ✓ | - |
| `search` | `Optional[str]` | ✓ | - |
| `intent` | `Optional[str]` | ✓ | - |
| `starred` | `bool` | ✓ | - |
| `limit` | `int` | ✓ | - |
| `from` | `unknown` | ✓ | - |
| `return` | `unknown` | ✓ | - |
| `from` | `unknown` | ✓ | - |
| `return` | `unknown` | ✓ | - |
| `from` | `unknown` | ✓ | - |
| `delete_query` | `unknown` | ✓ | - |
| `return` | `unknown` | ✓ | - |
| `from` | `unknown` | ✓ | - |
| `count` | `unknown` | ✓ | - |
| `return` | `unknown` | ✓ | - |
| `from` | `unknown` | ✓ | - |
| `from` | `unknown` | ✓ | - |
| `try` | `stats` | ✓ | - |
| `except` | `unknown` | ✓ | - |
| `return` | `unknown` | ✓ | - |
| `from` | `unknown` | ✓ | - |
| `from` | `unknown` | ✓ | - |
| `from` | `unknown` | ✓ | - |
| `from` | `unknown` | ✓ | - |
| `dest` | `unknown` | ✓ | - |
| `content` | `unknown` | ✓ | - |
| `dest` | `unknown` | ✓ | - |
| `docs` | `unknown` | ✓ | - |
| `if` | `unknown` | ✓ | - |
| `raise` | `unknown` | ✓ | - |
| `from` | `unknown` | ✓ | - |
| `return` | `unknown` | ✓ | - |
| `from` | `unknown` | ✓ | - |
| `return` | `unknown` | ✓ | - |
| `from` | `unknown` | ✓ | - |
| `return` | `unknown` | ✓ | - |
| `from` | `unknown` | ✓ | - |
| `path` | `unknown` | ✓ | - |
| `if` | `unknown` | ✓ | - |
| `raise` | `unknown` | ✓ | - |
| `from` | `unknown` | ✓ | - |

### [bugfix] Changes in utils.py

- **File**: `venv\Lib\site-packages\fastapi\utils.py`
- **Captured**: 4/22/2026, 9:02:29 PM
- **Category**: bugfix
**Summary:** Modified utils.py: 137 lines added, 0 lines removed.
**Files Modified:**
  - `venv\Lib\site-packages\fastapi\utils.py` (+137 / -0)

## Features & Implementation

### [feature] Changes in Settings.jsx

- **File**: `frontend\src\pages\Settings.jsx`
- **Captured**: 4/22/2026, 11:10:10 PM
- **Category**: feature
**Summary:** Modified Settings.jsx: 46 lines added, 10 lines removed.
**Files Modified:**
  - `frontend\src\pages\Settings.jsx` (+46 / -10)

### [feature] Changes in api.js

- **File**: `frontend\src\services\api.js`
- **Captured**: 4/22/2026, 10:04:24 PM
- **Category**: feature
**Summary:** Modified api.js: 13 lines added, 0 lines removed.
**Files Modified:**
  - `frontend\src\services\api.js` (+13 / -0)

### [UI] NexusAgent

- **File**: `frontend\dist\index.html`
- **Captured**: 4/22/2026, 9:57:27 PM
- **Category**: feature
**Summary:** **Page:** NexusAgent
**Libraries:** `index-BsJbQkw1.js`
**Files Modified:**
  - `frontend\dist\index.html` (+17 / -0)

### [feature] Changes in export_conversation.py

- **File**: `utils\export_conversation.py`
- **Captured**: 4/22/2026, 9:47:36 PM
- **Category**: feature
**Summary:** Modified export_conversation.py: 41 lines added, 258 lines removed.
**Files Modified:**
  - `utils\export_conversation.py` (+41 / -258)

### [UI] NexusAgent

- **File**: `frontend\dist\index.html`
- **Captured**: 4/22/2026, 9:39:13 PM
- **Category**: feature
**Summary:** **Page:** NexusAgent
**Libraries:** `index-BsJbQkw1.js`
**Files Modified:**
  - `frontend\dist\index.html` (+17 / -0)

### [UI] index-BA7szKqL

- **File**: `frontend\dist\assets\index-BA7szKqL.css`
- **Captured**: 4/22/2026, 9:39:13 PM
- **Category**: feature
**Summary:** **CSS Variables:**

| Variable | Value |
|----------|-------|
| `--tw-rotate-x` | `initial` |
| `--tw-rotate-y` | `initial` |
| `--tw-rotate-z` | `initial` |
| `--tw-skew-x` | `initial` |
| `--tw-skew-y` | `initial` |
| `--tw-border-style` | `solid` |
| `--tw-outline-style` | `solid` |
| `--tw-blur` | `initial` |
| `--tw-brightness` | `initial` |
| `--tw-contrast` | `initial` |
| `--tw-grayscale` | `initial` |
| `--tw-hue-rotate` | `initial` |
| `--tw-invert` | `initial` |
| `--tw-opacity` | `initial` |
| `--tw-saturate` | `initial` |

**Animations/Keyframes:** `pulse-dot`, `spin`

**Breakpoints:** `(width<=768px)`
**Files Modified:**
  - `frontend\dist\assets\index-BA7szKqL.css` (+3 / -0)

### [UI] index

- **File**: `frontend\src\index.css`
- **Captured**: 4/22/2026, 9:36:24 PM
- **Category**: feature
**Summary:** **CSS Variables:**

| Variable | Value |
|----------|-------|
| `--color-dark-900` | `#06080f` |
| `--color-dark-800` | `#0c1222` |
| `--color-dark-700` | `#0f172a` |
| `--color-dark-600` | `#1e293b` |
| `--color-dark-500` | `#334155` |
| `--color-dark-400` | `#475569` |
| `--color-text` | `#e2e8f0` |
| `--color-text-muted` | `#94a3b8` |
| `--color-text-dim` | `#64748b` |
| `--color-accent` | `#3b82f6` |
| `--color-accent-soft` | `#3b82f620` |
| `--color-purple` | `#8b5cf6` |

**Animations/Keyframes:** `pulse-dot`

**Breakpoints:** `(max-width: 768px)`

**Component classes:** `.sidebar`, `.sidebar-logo`, `.sidebar-logo-icon`, `.nav-section`, `.nav-item`, `.conv-section`, `.conv-label`, `.conv-item`, `.status-bar`, `.status-dot`
**Files Modified:**
  - `frontend\src\index.css` (+192 / -0)

### [feature] Changes in export_conversation.py

- **File**: `utils\export_conversation.py`
- **Captured**: 4/22/2026, 9:29:09 PM
- **Category**: feature
**Summary:** Modified export_conversation.py: 58 lines added, 214 lines removed.
**Files Modified:**
  - `utils\export_conversation.py` (+58 / -214)

### [feature] Changes in conversation_store.py

- **File**: `memory\conversation_store.py`
- **Captured**: 4/22/2026, 9:28:27 PM
- **Category**: feature
**Summary:** Modified conversation_store.py: 107 lines added, 219 lines removed.
**Files Modified:**
  - `memory\conversation_store.py` (+107 / -219)

### [UI] NexusAgent

- **File**: `frontend\dist\index.html`
- **Captured**: 4/22/2026, 9:25:01 PM
- **Category**: feature
**Summary:** **Page:** NexusAgent
**Libraries:** `index-DwQRvi4P.js`
**Files Modified:**
  - `frontend\dist\index.html` (+17 / -0)

### [UI] index-rjaV5uxO

- **File**: `frontend\dist\assets\index-rjaV5uxO.css`
- **Captured**: 4/22/2026, 9:25:01 PM
- **Category**: feature
**Summary:** **CSS Variables:**

| Variable | Value |
|----------|-------|
| `--tw-rotate-x` | `initial` |
| `--tw-rotate-y` | `initial` |
| `--tw-rotate-z` | `initial` |
| `--tw-skew-x` | `initial` |
| `--tw-skew-y` | `initial` |
| `--tw-space-y-reverse` | `0` |
| `--tw-border-style` | `solid` |
| `--tw-gradient-position` | `initial` |
| `--tw-gradient-from` | `#0000` |
| `--tw-gradient-via` | `#0000` |
| `--tw-gradient-to` | `#0000` |
| `--tw-gradient-stops` | `initial` |
| `--tw-gradient-via-stops` | `initial` |
| `--tw-gradient-from-position` | `0%` |
| `--tw-gradient-via-position` | `50%` |

**Animations/Keyframes:** `pulse-dot`, `spin`

**Breakpoints:** `(hover:hover)`
**Files Modified:**
  - `frontend\dist\assets\index-rjaV5uxO.css` (+3 / -0)

### [UI] NexusAgent

- **File**: `frontend\index.html`
- **Captured**: 4/22/2026, 9:12:50 PM
- **Category**: feature
**Summary:** **Page:** NexusAgent
**Libraries:** `main.jsx`
**Files Modified:**
  - `frontend\index.html` (+16 / -0)

### [UI] App

- **File**: `frontend\src\App.css`
- **Captured**: 4/22/2026, 9:09:26 PM
- **Category**: feature
**Files Modified:**
  - `frontend\src\App.css` (+2 / -0)

### [feature] Changes in App.jsx

- **File**: `frontend\src\App.jsx`
- **Captured**: 4/22/2026, 9:09:23 PM
- **Category**: feature
**Summary:** Modified App.jsx: 23 lines added, 119 lines removed.
**Files Modified:**
  - `frontend\src\App.jsx` (+23 / -119)

### [UI] index

- **File**: `frontend\src\index.css`
- **Captured**: 4/22/2026, 9:08:46 PM
- **Category**: feature
**Summary:** **Animations/Keyframes:** `pulse-dot`

**Component classes:** `.thinking-dot`
**Files Modified:**
  - `frontend\src\index.css` (+37 / -0)

### [UI] frontend

- **File**: `frontend\index.html`
- **Captured**: 4/22/2026, 9:05:49 PM
- **Category**: feature
**Summary:** **Page:** frontend
**Libraries:** `main.jsx`
**Files Modified:**
  - `frontend\index.html` (+14 / -0) `#08060d` |
| `--bg` | `#fff` |
| `--border` | `#e5e4e7` |
| `--code-bg` | `#f4f3ec` |
| `--accent` | `#aa3bff` |
| `--accent-bg` | `rgba(170, 59, 255, 0.1)` |
| `--accent-border` | `rgba(170, 59, 255, 0.5)` |
| `--social-bg` | `rgba(244, 243, 236, 0.5)` |
| `--shadow` | `rgba(0, 0, 0, 0.1) 0 10px 15px -3px, rgba(0, 0, 0, 0.05) 0 4px 6px -2px` |
| `--sans` | `system-ui, 'Segoe UI', Roboto, sans-serif` |
| `--heading` | `system-ui, 'Segoe UI', Roboto, sans-serif` |
| `--mono` | `ui-monospace, Consolas, monospace` |

**Breakpoints:** `(max-width: 1024px)`, `(prefers-color-scheme: dark)`

**Component classes:** `.counter`
**Files Modified:**
  - `frontend\src\index.css` (+112 / -0)

## Recent Changes

### [unknown] Changes in conversation_store.py

- **File**: `memory\conversation_store.py`
- **Captured**: 4/22/2026, 9:47:36 PM
- **Category**: unknown
**Summary:** Modified conversation_store.py: 75 lines added, 281 lines removed.
**Files Modified:**
  - `memory\conversation_store.py` (+75 / -281)

### [unknown] Changes in query_history.py

- **File**: `memory\query_history.py`
- **Captured**: 4/22/2026, 9:47:36 PM
- **Category**: unknown
**Summary:** Modified query_history.py: 42 lines added, 214 lines removed.
**Files Modified:**
  - `memory\query_history.py` (+42 / -214)

### [unknown] Changes in query_history.py

- **File**: `memory\query_history.py`
- **Captured**: 4/22/2026, 9:28:36 PM
- **Category**: unknown
**Summary:** Modified query_history.py: 62 lines added, 171 lines removed.
**Files Modified:**
  - `memory\query_history.py` (+62 / -171)