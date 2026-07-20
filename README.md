# SAP ADT Python Bridge

This local Python bridge connects AI tools (LLMs, agents) to an SAP ABAP system using read-only ABAP Development Tools (ADT) HTTP services.

---

## 🤖 LLM System Instructions

If you are an AI model or Agent, use these instructions to interact with SAP:

- **Base URL:** `http://127.0.0.1:8080`
- **Method & Header:** `POST` with `Content-Type: application/json` or `GET`
- **Format:** Request payload and Responses are always JSON.
- **Rule:** This bridge is strictly **READ-ONLY**.
- **⚠️ CRITICAL FOR PARAMETERS:** When using GET requests, you MUST use the exact parameter names specified. Do NOT guess or invent parameter names (e.g., never use `object_name`, always use `name` if specified).
- **⚠️ CRITICAL:** Do NOT attempt to run `sap_adt.py` or `app.py` as CLI commands. You must interact with the bridge via HTTP GET or POST requests.

---

## 🔌 Agent Skill Configuration

If you are using this repository with an AI agent or LLM system that supports local agent customizations (Skills), you can register the pre-configured skill:
- **Skill Path:** `.agents/skills/SKILL.md`
- This file provides structured system instructions, input/output schemas, and endpoint definitions specifically tailored for LLM consumption.

---

## 🛠️ Available Endpoints

All endpoints are prefixed with `/tool/`. They support both **GET** and **POST**. Send JSON payloads in the body for POST, or use URL query parameters for GET.

> [!WARNING]
> **LLM INSTRUCTION:** When constructing GET URLs, use the EXACT link provided in the "GET Example" below. Do not alter the parameter keys (e.g., use `name=` not `object_name=`).

### Diagnostics & Connection
- **`/tool/ping`**: Check bridge liveness.
  - POST Body: `{}`
  - GET Example: `http://127.0.0.1:8080/tool/ping`
- **`/tool/adt_logon`**: Initialize session/CSRF.
  - POST Body: `{}`
  - GET Example: `http://127.0.0.1:8080/tool/adt_logon`
- **`/tool/adt_doctor`**: Connection diagnostics.
  - POST Body: `{}`
  - GET Example: `http://127.0.0.1:8080/tool/adt_doctor`

### Search & Discovery
- **`/tool/adt_search`**: Search objects by name.
  - POST Body: `{"query": "Z*", "max_results": 50}`
  - GET Example: `http://127.0.0.1:8080/tool/adt_search?query=Z*&max_results=50`
- **`/tool/adt_code_search`**: Full-text source search.
  - POST Body: `{"search_term": "keyword", "max_results": 50}`
  - GET Example: `http://127.0.0.1:8080/tool/adt_code_search?search_term=keyword&max_results=50`
- **`/tool/adt_list_package`**: List package contents.
  - POST Body: `{"package_name": "ZPKG"}`
  - GET Example: `http://127.0.0.1:8080/tool/adt_list_package?package_name=ZPKG`
- **`/tool/adt_where_used`**: Find references.
  - POST Body: `{"name": "OBJ", "object_type": "class"}`
  - GET Example: `http://127.0.0.1:8080/tool/adt_where_used?name=OBJ&object_type=class`
- **`/tool/adt_inactive_objects`**: List inactive objects.
  - POST Body: `{"user": "developer"}`
  - GET Example: `http://127.0.0.1:8080/tool/adt_inactive_objects?user=developer`
- **`/tool/adt_badi_discovery`**: BAdI cross-reference.
  - POST Body: `{"name": "Z_BADI"}`
  - GET Example: `http://127.0.0.1:8080/tool/adt_badi_discovery?name=Z_BADI`

### Source Code & History
- **`/tool/adt_get_source`**: Read active source code.
  - POST Body: `{"name": "OBJ", "object_type": "class"}`
  - GET Example: `http://127.0.0.1:8080/tool/adt_get_source?name=OBJ&object_type=class`
- **`/tool/adt_revisions`**: Get version history.
  - POST Body: `{"name": "OBJ", "object_type": "class"}`
  - GET Example: `http://127.0.0.1:8080/tool/adt_revisions?name=OBJ&object_type=class`

### Quality & Testing
- **`/tool/adt_syntax_check`**: Syntax-check (no activate).
  - POST Body: `{"name": "OBJ", "object_type": "class"}`
  - GET Example: `http://127.0.0.1:8080/tool/adt_syntax_check?name=OBJ&object_type=class`
- **`/tool/adt_atc_check`**: Run ATC quality analysis.
  - POST Body: `{"name": "OBJ", "object_type": "class"}`
  - GET Example: `http://127.0.0.1:8080/tool/adt_atc_check?name=OBJ&object_type=class`
- **`/tool/adt_unit_test`**: Run object's test classes.
  - POST Body: `{"name": "OBJ", "object_type": "class"}`
  - GET Example: `http://127.0.0.1:8080/tool/adt_unit_test?name=OBJ&object_type=class`
- **`/tool/adt_check_scatter`**: Detect scattered includes.
  - POST Body: `{"name": "OBJ", "object_type": "class"}`
  - GET Example: `http://127.0.0.1:8080/tool/adt_check_scatter?name=OBJ&object_type=class`
- **`/tool/adt_dumps`**: Fetch recent ST22 short dumps.
  - POST Body: `{"max_results": 10}`
  - GET Example: `http://127.0.0.1:8080/tool/adt_dumps?max_results=10`

### Transports
- **`/tool/adt_list_transports`**: List user transports.
  - POST Body: `{"user": "developer"}`
  - GET Example: `http://127.0.0.1:8080/tool/adt_list_transports?user=developer`
- **`/tool/adt_transport_status`**: Transport orientation.
  - POST Body: `{"transport_id": "TRK90001"}`
  - GET Example: `http://127.0.0.1:8080/tool/adt_transport_status?transport_id=TRK90001`
- **`/tool/adt_transport_check`**: Pre-write transport check.
  - POST Body: `{"transport_id": "TRK90001"}`
  - GET Example: `http://127.0.0.1:8080/tool/adt_transport_check?transport_id=TRK90001`

### Database
- **`/tool/adt_sql`**: Read-only freestyle ABAP SQL SELECT query execution.
  - POST Body: `{"query": "SELECT * FROM...", "row_limit": 100}`
  - GET Example: `http://127.0.0.1:8080/tool/adt_sql?query=SELECT+*+FROM...&row_limit=100`

---

## 🚀 Setup & Running

1. **Configure:** Copy `.env.example` to `.env` and enter your SAP credentials.
2. **Install:** `pip install -r requirements.txt`
3. **Run:** `python app.py` (Starts on `http://127.0.0.1:8080`)
