---
name: sap_adt_connector
description: Interact with SAP ABAP systems through the read-only SAP ADT Python Bridge API.
---

# SAP ADT Connector Skill

This skill allows the AI agent to search, query, and examine SAP ABAP source code, objects, revisions, transports, and system dumps using the local SAP ADT Python Bridge.

## Base Configuration

All requests must be sent to the local bridge server:
- **Base URL:** http://127.0.0.1:8080
- **Headers:** Content-Type: application/json
- **Method:** POST

**⚠️ CRITICAL FOR LLMs / AGENTS:**
Do NOT attempt to run `sap_adt.py` or `app.py` from the command line (e.g. `python sap_adt.py tool/ping`). This is not a CLI tool. You must interact with the SAP bridge EXCLUSIVELY via HTTP POST requests to the Base URL.

---

## 1. System Health & Diagnostics

### Ping
Verify if the bridge server is active.
- **Path:** /tool/ping
- **Payload:** {}
- **Response Template:**
  {
    "ok": true,
    "message": "Bridge is alive."
  }

### Logon
Establish a session and fetch the CSRF token from the SAP system.
- **Path:** /tool/adt_logon
- **Payload:** {}
- **Response Template:**
  {
    "ok": true,
    "message": "Logon successful",
    "session_active": true
  }

### Doctor Diagnostics
Perform full connectivity diagnostics.
- **Path:** /tool/adt_doctor
- **Payload:** {}
- **Response Template:**
  {
    "ok": true,
    "diagnostics": {
      "host": "https://sap-system-host",
      "user": "SAP_DEVELOPER",
      "client": "100",
      "csrf_fetched": true,
      "logon_status": {
        "ok": true,
        "message": "Logon successful",
        "session_active": true
      }
    }
  }

---

## 2. Search & Discovery

### Object Search
Search for SAP development objects (e.g. Classes, Programs, Packages) by name pattern.
- **Path:** /tool/adt_search
- **Payload:**
  {
    "query": "ZCL_CUSTOM_SEARCH*",
    "max_results": 50
  }
- **Response Template:**
  {
    "ok": true,
    "query": "ZCL_CUSTOM_SEARCH*",
    "results": [
      {
        "name": "ZCL_CUSTOM_SEARCH",
        "type": "CLAS/OC",
        "uri": "/sap/bc/adt/oo/classes/zcl_custom_search"
      }
    ]
  }

### Source Code Search
Find source code containing specific keywords (full-text search).
- **Path:** /tool/adt_code_search
- **Payload:**
  {
    "search_term": "SELECT SINGLE",
    "max_results": 50
  }
- **Response Template:**
  {
    "ok": true,
    "message": "Code search executed (results may vary by ADT capability)",
    "status_code": 200
  }

### List Package Contents
Retrieve a list of all objects inside a specific SAP package.
- **Path:** /tool/adt_list_package
- **Payload:**
  {
    "package_name": "ZMY_PACKAGE"
  }
- **Response Template:**
  {
    "ok": true,
    "package_name": "ZMY_PACKAGE",
    "contents": [
      {
        "name": "ZCL_PROCESS_HELPER",
        "type": "CLAS/OC"
      }
    ]
  }

### Where-Used List
Find references and usages of an object in the system.
- **Path:** /tool/adt_where_used
- **Payload:**
  {
    "name": "ZCL_MY_CLASS",
    "object_type": "class"
  }
- **Supported Object Types (object_type):** class, interface, program, include
- **Response Template:**
  {
    "ok": true,
    "object_name": "ZCL_MY_CLASS",
    "references": [
      {
        "name": "ZPROGRAM_RUNNER",
        "type": "PROG/P"
      }
    ]
  }

---

## 3. Source Code Retrieval & History

### Get Active Source Code
Read the current active source code of an ABAP object.
- **Path:** /tool/adt_get_source
- **Payload:**
  {
    "name": "ZCL_MY_CLASS",
    "object_type": "class"
  }
- **Supported Object Types (object_type):** class, interface, program, include
- **Response Template:**
  {
    "ok": true,
    "object_name": "ZCL_MY_CLASS",
    "object_type": "class",
    "source_code": "class ZCL_MY_CLASS definition ... public section. ... endclass. ... implementation. ... endclass."
  }

### Revisions / Version History
Get the version and revision history of an object.
- **Path:** /tool/adt_revisions
- **Payload:**
  {
    "name": "ZCL_MY_CLASS",
    "object_type": "class"
  }
- **Response Template:**
  {
    "ok": true,
    "object_name": "ZCL_MY_CLASS",
    "message": "History retrieved successfully",
    "data": "...XML history payload..."
  }

---

## 4. Diagnostics & System Checks

### Syntax Check
Run a syntax check on an object without activating changes.
- **Path:** /tool/adt_syntax_check
- **Payload:**
  {
    "name": "ZCL_MY_CLASS",
    "object_type": "class"
  }
- **Response Template:**
  {
    "ok": true,
    "object_name": "ZCL_MY_CLASS",
    "status_code": 200,
    "data": "...Syntax check results (XML or plain text)..."
  }

### Inactive Objects
List inactive objects for a specific developer.
- **Path:** /tool/adt_inactive_objects
- **Payload:**
  {
    "user": "DEVELOPER_USER"
  }
- **Response Template:**
  {
    "ok": true,
    "message": "Inactive objects fetched",
    "data": "...Inactive objects list XML..."
  }

### Short Dumps (ST22)
Fetch recent ABAP short dumps for system troubleshooting.
- **Path:** /tool/adt_dumps
- **Payload:**
  {
    "max_results": 10
  }
- **Response Template:**
  {
    "ok": true,
    "message": "Dumps retrieved",
    "data": "...Recent short dumps list XML..."
  }

---

## 5. Transports

### List Transport Requests
List transport requests associated with a user.
- **Path:** /tool/adt_list_transports
- **Payload:**
  {
    "user": "DEVELOPER_USER"
  }
- **Response Template:**
  {
    "ok": true,
    "message": "Transports retrieved",
    "data": "...Transports list XML..."
  }

### Transport Status
Retrieve orientation and status details for a specific Transport ID.
- **Path:** /tool/adt_transport_status
- **Payload:**
  {
    "transport_id": "DEVK900001"
  }
- **Response Template:**
  {
    "ok": true,
    "transport": "DEVK900001",
    "message": "Transport status template"
  }

---

## Important Constraints

1. Read-Only: This API is strictly read-only. Modifying functions (activation, creating, editing) are not supported.
2. XML Responses: Many diagnostic and listing endpoints (/tool/adt_revisions, /tool/adt_dumps, /tool/adt_list_transports) return raw XML or truncated XML payloads that need to be parsed by the LLM client or supporting functions.
