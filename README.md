# SAP ADT Python Bridge

This local Python bridge connects AI tools (LLMs, agents) to an SAP ABAP system using read-only ABAP Development Tools (ADT) HTTP services.

---

## 🤖 LLM System Instructions

If you are an AI model or Agent, use these instructions to interact with SAP:

- **Base URL:** `http://127.0.0.1:8080`
- **Method & Header:** `POST` with `Content-Type: application/json` or `GET`
- **Format:** Request payload and Responses are always JSON.
- **Rule:** This bridge is strictly **READ-ONLY**.
- **⚠️ CRITICAL:** Do NOT attempt to run `sap_adt.py` or `app.py` as CLI commands. You must interact with the bridge via HTTP GET or POST requests.

---

## 🔌 Agent Skill Configuration

If you are using this repository with an AI agent or LLM system that supports local agent customizations (Skills), you can register the pre-configured skill:
- **Skill Path:** `.agents/skills/SKILL.md`
- This file provides structured system instructions, input/output schemas, and endpoint definitions specifically tailored for LLM consumption.

---

## 🛠️ Available Endpoints

All endpoints are prefixed with `/tool/`. They support both **GET** and **POST**. Send JSON payloads in the body for POST, or use URL query parameters for GET.

### Diagnostics & Connection
- **`/tool/ping`**: Check bridge liveness. (Body: `{}`)
- **`/tool/adt_logon`**: Initialize session/CSRF. (Body: `{}`)
- **`/tool/adt_doctor`**: Connection diagnostics. (Body: `{}`)

### Search & Discovery
- **`/tool/adt_search`**: Search objects by name. (Body: `{"query": "Z*", "max_results": 50}`)
- **`/tool/adt_code_search`**: Full-text source search. (Body: `{"search_term": "keyword"}`)
- **`/tool/adt_list_package`**: List package contents. (Body: `{"package_name": "ZPKG"}`)
- **`/tool/adt_where_used`**: Find references. (Body: `{"name": "OBJ", "object_type": "class"}`)
- **`/tool/adt_inactive_objects`**: List inactive objects. (Body: `{"user": "developer"}`)
- **`/tool/adt_badi_discovery`**: BAdI cross-reference. (Body: `{"name": "Z_BADI"}`)

### Source Code & History
- **`/tool/adt_get_source`**: Read active source code. (Body: `{"name": "OBJ", "object_type": "class"}`)
- **`/tool/adt_revisions`**: Get version history. (Body: `{"name": "OBJ", "object_type": "class"}`)

### Quality & Testing
- **`/tool/adt_syntax_check`**: Syntax-check (no activate). (Body: `{"name": "OBJ", "object_type": "class"}`)
- **`/tool/adt_atc_check`**: Run ATC quality analysis. (Body: `{"name": "OBJ", "object_type": "class"}`)
- **`/tool/adt_unit_test`**: Run object's test classes. (Body: `{"name": "OBJ", "object_type": "class"}`)
- **`/tool/adt_check_scatter`**: Detect scattered includes. (Body: `{"name": "OBJ", "object_type": "class"}`)
- **`/tool/adt_dumps`**: Fetch recent ST22 short dumps. (Body: `{"max_results": 10}`)

### Transports
- **`/tool/adt_list_transports`**: List user transports. (Body: `{"user": "developer"}`)
- **`/tool/adt_transport_status`**: Transport orientation. (Body: `{"transport_id": "TRK90001"}`)
- **`/tool/adt_transport_check`**: Pre-write transport check. (Body: `{"transport_id": "TRK90001"}`)

### Database
- **`/tool/adt_sql`**: Read-only freestyle ABAP SQL SELECT query execution. (Body: `{"query": "SELECT * FROM...", "row_limit": 100}`)

---

## 🚀 Setup & Running

1. **Configure:** Copy `.env.example` to `.env` and enter your SAP credentials.
2. **Install:** `pip install -r requirements.txt`
3. **Run:** `python app.py` (Starts on `http://127.0.0.1:8080`)
