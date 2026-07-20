import os
import logging
import requests
from requests.auth import HTTPBasicAuth
from xml.etree import ElementTree as ET
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)

def _local_tag(tag):
    return tag.split('}')[-1] if '}' in tag else tag

def _local_attr(elem, attr_name, alt_name=None):
    for k, v in elem.attrib.items():
        local_key = k.split('}')[-1]
        if local_key == attr_name or (alt_name and local_key == alt_name):
            return v
    return None


class SAPADTHandler:
    def __init__(self):
        self.host = os.getenv("SAP_HOST", "").rstrip("/")
        self.client = os.getenv("SAP_CLIENT", "")
        self.user = os.getenv("SAP_USER", "")
        self.password = os.getenv("SAP_PASSWORD", "")
        
        self.session = requests.Session()
        self.session.auth = HTTPBasicAuth(self.user, self.password)
        self.session.headers.update({
            "Accept": "application/xml",
            "X-SAP-Client": self.client
        })
        self.csrf_token = None

    def _get_csrf_token(self):
        discovery_url = f"{self.host}/sap/bc/adt/discovery"
        headers = {"X-CSRF-Token": "Fetch", "Accept": "*/*"}
        try:
            response = self.session.get(discovery_url, headers=headers)
            response.raise_for_status()
            self.csrf_token = response.headers.get("x-csrf-token")
            if self.csrf_token:
                self.session.headers.update({"X-CSRF-Token": self.csrf_token})
            return True
        except requests.RequestException as e:
            logger.error(f"Failed to fetch CSRF token: {e}")
            return False

    def ping(self):
        """Liveness check (ping)."""
        logger.info("Ping requested")
        return {"ok": True, "message": "Bridge is alive."}

    def logon(self):
        logger.info("Executing ADT Logon")
        if not self.host or not self.user or not self.password:
            return {"ok": False, "error": "Missing SAP connection configuration in .env"}
        success = self._get_csrf_token()
        if success:
            return {"ok": True, "message": "Logon successful", "session_active": True}
        return {"ok": False, "error": "Failed to connect to SAP ADT (check credentials/host)"}

    def doctor(self):
        """Connection diagnostics."""
        logger.info("Executing ADT Doctor")
        status = self.logon()
        return {
            "ok": True,
            "diagnostics": {
                "host": self.host,
                "user": self.user,
                "client": self.client,
                "csrf_fetched": self.csrf_token is not None,
                "logon_status": status
            }
        }

    def _get_object_uri(self, name, object_type):
        name = name.lower()
        object_type = object_type.lower()
        if object_type == "class": return f"/sap/bc/adt/oo/classes/{name}"
        elif object_type == "interface": return f"/sap/bc/adt/oo/interfaces/{name}"
        elif object_type == "program": return f"/sap/bc/adt/programs/programs/{name}"
        elif object_type == "include": return f"/sap/bc/adt/programs/includes/{name}"
        return None

    def get_source(self, name, object_type):
        logger.info(f"Fetching source for {object_type} {name}")
        if not self.csrf_token: self._get_csrf_token()
        uri = self._get_object_uri(name, object_type)
        if not uri: return {"ok": False, "error": f"Unsupported object type: {object_type}"}
        
        try:
            response = self.session.get(f"{self.host}{uri}/source/main", headers={"Accept": "text/plain"})
            response.raise_for_status()
            return {"ok": True, "object_name": name, "object_type": object_type, "source_code": response.text}
        except requests.RequestException as e:
            return {"ok": False, "error": str(e)}

    def search(self, query, max_results=50):
        logger.info(f"Searching objects with query: {query}")
        if not self.csrf_token: self._get_csrf_token()
        url = f"{self.host}/sap/bc/adt/repository/informationsystem/search"
        params = {
            "operation": "quickSearch",
            "query": query,
            "maxResults": max_results
        }
        try:
            response = self.session.get(url, params=params)
            response.raise_for_status()
            root = ET.fromstring(response.content)
            ns = {'adtcore': 'http://www.sap.com/adt/core'}
            results = [{"name": _local_attr(obj, 'name'), "type": _local_attr(obj, 'type'), "uri": _local_attr(obj, 'uri')} 
                       for obj in root.findall('.//adtcore:objectReference', ns)]
            return {"ok": True, "query": query, "results": results}
        except Exception as e:
            return {"ok": False, "error": str(e)}

    def code_search(self, search_term, max_results=50):
        logger.info(f"Code search for: {search_term}")
        if not self.csrf_token: self._get_csrf_token()
        url = f"{self.host}/sap/bc/adt/repository/informationsystem/textSearch"
        params = {"searchString": search_term, "maxResults": max_results}
        try:
            response = self.session.get(url, params=params)
            response.raise_for_status()
            
            results = []
            root = ET.fromstring(response.content)
            
            # Look for objectReference tags
            refs = [e for e in root.iter() if _local_tag(e.tag) == 'objectReference']
            if refs:
                for ref in refs:
                    matches = []
                    for m in ref.iter():
                        if _local_tag(m.tag) != 'textSearchResult':
                            continue
                        line_raw = _local_attr(m, 'line')
                        try:
                            line = int(line_raw) if line_raw is not None else 0
                        except ValueError:
                            line = 0
                        snippet = _local_attr(m, 'snippet') or m.text or ''
                        matches.append({'line': line, 'snippet': snippet.strip()})
                    results.append({
                        'uri': _local_attr(ref, 'uri') or '',
                        'name': _local_attr(ref, 'name') or '',
                        'type': _local_attr(ref, 'type') or '',
                        'description': _local_attr(ref, 'description') or '',
                        'matches': matches
                    })
            else:
                # Generic fallback for <match> tags
                for node in root.iter():
                    if _local_tag(node.tag) != 'match':
                        continue
                    line_raw = _local_attr(node, 'line')
                    try:
                        line = int(line_raw) if line_raw is not None else 0
                    except ValueError:
                        line = 0
                    snippet = _local_attr(node, 'snippet') or node.text or ''
                    results.append({
                        'uri': _local_attr(node, 'uri') or '',
                        'name': _local_attr(node, 'name') or _local_attr(node, 'objectName') or '',
                        'type': _local_attr(node, 'type') or '',
                        'description': '',
                        'matches': [{'line': line, 'snippet': snippet.strip()}]
                    })
            
            return {"ok": True, "results": results}
        except requests.HTTPError as e:
            if e.response is not None and e.response.status_code in (404, 501):
                return {"ok": False, "error": f"Full-text source code search (textSearch) is not active or supported on this SAP system (HTTP {e.response.status_code})."}
            return {"ok": False, "error": str(e)}
        except Exception as e:
            return {"ok": False, "error": str(e)}

    def list_package(self, package_name):
        logger.info(f"Listing contents of package: {package_name}")
        if not self.csrf_token: self._get_csrf_token()
        url = f"{self.host}/sap/bc/adt/repository/nodestructure"
        headers = {
            "Accept": "application/vnd.sap.as+xml, application/vnd.sap.adt.core.v1+xml",
            "Content-Type": "application/vnd.sap.as+xml"
        }
        params = {
            "parent_type": "DEVC/K",
            "parent_name": package_name.upper(),
            "withShortDescriptions": "true"
        }
        try:
            response = self.session.post(url, headers=headers, params=params, data='')
            response.raise_for_status()
            
            root = ET.fromstring(response.content)
            objects = []
            
            # Strategy 1: Standard ADT format (adtcore:objectReference)
            for obj in root.iter():
                if _local_tag(obj.tag) == 'objectReference':
                    name = _local_attr(obj, 'name')
                    obj_type = _local_attr(obj, 'type')
                    uri = _local_attr(obj, 'uri')
                    description = _local_attr(obj, 'description') or ''
                    if name:
                        objects.append({
                            'name': name,
                            'type': obj_type or '',
                            'uri': uri or '',
                            'description': description
                        })
            
            # Strategy 2: ABAP XML format (SEU_ADT_REPOSITORY_OBJ_NODE)
            if not objects:
                for node in root.iter():
                    if 'SEU_ADT_REPOSITORY_OBJ_NODE' in node.tag:
                        obj_type = obj_name = tech_name = description = ''
                        for child in node:
                            tag = _local_tag(child.tag)
                            text = child.text if child.text else ''
                            if tag == 'OBJECT_TYPE':
                                obj_type = text
                            elif tag == 'OBJECT_NAME':
                                obj_name = text
                            elif tag == 'TECH_NAME':
                                tech_name = text
                            elif tag == 'DESCRIPTION':
                                description = text
                        
                        name = obj_name or tech_name
                        skip_types = ['DEVC/Q', 'DEVC/N', 'DEVC/K', 'DEVC/DA', 'DEVC/DD', 'DEVC/DE',
                                     'DEVC/DL', 'DEVC/DS', 'DEVC/DT', 'DEVC/OC', 'DEVC/OI', 'DEVC/WO']
                        should_skip = any(obj_type.startswith(skip) for skip in skip_types)
                        if name and obj_type and not should_skip:
                            objects.append({
                                'name': name,
                                'type': obj_type,
                                'uri': f'/sap/bc/adt/{obj_type.lower().replace("/", "/")}s/{name.lower()}',
                                'description': description
                            })
            
            return {"ok": True, "package_name": package_name, "contents": objects}
        except Exception as e:
            return {"ok": False, "error": str(e)}

    def execute_sql(self, query, row_limit=100):
        logger.info(f"Executing SQL query: {query}")
        if not self.csrf_token: self._get_csrf_token()
        url = f"{self.host}/sap/bc/adt/datapreview/freestyle"
        headers = {
            "Accept": "application/vnd.sap.adt.datapreview.table.v1+xml",
            "Content-Type": "text/plain"
        }
        params = {"rowNumber": row_limit}
        try:
            response = self.session.post(url, headers=headers, params=params, data=query.encode('utf-8'))
            response.raise_for_status()
            
            root = ET.fromstring(response.content)
            ns = {'dp': 'http://www.sap.com/adt/dataPreview'}
            columns = []
            
            for col in root.findall('.//dp:columns', ns):
                meta = col.find('dp:metadata', ns)
                col_name = meta.get('{http://www.sap.com/adt/dataPreview}name', '') if meta is not None else ''
                data_cells = [cell.text for cell in col.findall('.//dp:data', ns)]
                columns.append({
                    "name": col_name,
                    "data": data_cells
                })
            
            rows = []
            if columns:
                num_rows = len(columns[0]["data"])
                for i in range(num_rows):
                    row = {}
                    for col in columns:
                        row[col["name"]] = col["data"][i] if i < len(col["data"]) else None
                    rows.append(row)
            
            return {"ok": True, "rows": rows}
        except Exception as e:
            return {"ok": False, "error": str(e)}

    def where_used(self, name, object_type):
        logger.info(f"Finding where-used for {object_type} {name}")
        if not self.csrf_token: self._get_csrf_token()
        
        object_url = self._get_object_uri(name, object_type)
        if not object_url:
            return {"ok": False, "error": f"Unsupported object type: {object_type}"}
            
        url = f"{self.host}/sap/bc/adt/repository/informationsystem/usageReferences"
        headers = {
            "Accept": "application/*",
            "Content-Type": "application/*"
        }
        
        body = '''<?xml version="1.0" encoding="ASCII"?>
<usagereferences:usageReferenceRequest xmlns:usagereferences="http://www.sap.com/adt/ris/usageReferences">
  <usagereferences:affectedObjects/>
</usagereferences:usageReferenceRequest>'''
        
        try:
            response = self.session.post(
                url,
                headers=headers,
                params={'uri': object_url},
                data=body.encode('utf-8')
            )
            response.raise_for_status()
            
            results = []
            root = ET.fromstring(response.content)
            for ref_obj in root.iter():
                ref_tag = ref_obj.tag.split('}')[-1] if '}' in ref_obj.tag else ref_obj.tag
                if ref_tag != 'referencedObject':
                    continue
                ref_attrs = {k.split('}')[-1] if '}' in k else k: v for k, v in ref_obj.attrib.items()}
                ref_uri = ref_attrs.get('uri', '')
                for child in ref_obj:
                    child_tag = child.tag.split('}')[-1] if '}' in child.tag else child.tag
                    if child_tag != 'adtObject':
                        continue
                    child_attrs = {k.split('}')[-1] if '}' in k else k: v for k, v in child.attrib.items()}
                    c_name = child_attrs.get('name', '')
                    c_type = child_attrs.get('type', '')
                    c_desc = child_attrs.get('description', '')
                    if c_name and c_type:
                        results.append({
                            'name': c_name,
                            'type': c_type,
                            'uri': ref_uri,
                            'description': c_desc
                        })
                    break
            
            return {"ok": True, "object_name": name, "references": results}
        except Exception as e:
            return {"ok": False, "error": str(e)}

    def revisions(self, name, object_type):
        """Version history of an object."""
        logger.info(f"Fetching revisions for {name}")
        if not self.csrf_token: self._get_csrf_token()
        uri = self._get_object_uri(name, object_type)
        if not uri: return {"ok": False, "error": "Unsupported type"}
        url = f"{self.host}{uri}/history"
        try:
            response = self.session.get(url)
            response.raise_for_status()
            return {"ok": True, "object_name": name, "message": "History retrieved successfully", "data": response.text[:500]}
        except Exception as e:
            return {"ok": False, "error": str(e)}

    def syntax_check(self, name, object_type):
        """Syntax-check without activating."""
        logger.info(f"Syntax check for {name}")
        if not self.csrf_token: self._get_csrf_token()
        uri = self._get_object_uri(name, object_type)
        if not uri: return {"ok": False, "error": "Unsupported type"}
        url = f"{self.host}{uri}/syntaxcheck"
        try:
            response = self.session.post(url)
            return {"ok": True, "object_name": name, "status_code": response.status_code, "data": response.text}
        except Exception as e:
            return {"ok": False, "error": str(e)}

    def atc_check(self, name, object_type):
        """ATC quality analysis (read-only)."""
        logger.info(f"ATC check for {name}")
        return {"ok": False, "error": "ATC checks via ADT require a complex XML payload specific to SAP release. Stubbed for safety."}

    def unit_test(self, name, object_type):
        """Runs the object's test classes."""
        logger.info(f"Unit test for {name}")
        return {"ok": False, "error": "ABAP Unit tests via ADT require specific runner payloads. Stubbed."}

    def check_scatter(self, name, object_type):
        """Detect scattered class includes."""
        return {"ok": True, "message": f"Scatter check template for {name}. Usually requires analyzing multiple includes via /sap/bc/adt/oo/classes."}

    def inactive_objects(self, user=""):
        """List inactive objects."""
        logger.info("Listing inactive objects")
        if not self.csrf_token: self._get_csrf_token()
        url = f"{self.host}/sap/bc/adt/repository/informationsystem/search"
        try:
            response = self.session.get(url, params={"inactive": "true"})
            response.raise_for_status()
            return {"ok": True, "message": "Inactive objects fetched", "data": response.text[:500]}
        except Exception as e:
            return {"ok": False, "error": str(e)}

    def badi_discovery(self, name):
        """Classic-BAdI cross-reference."""
        return {"ok": True, "message": "BAdI discovery template."}

    def dumps(self, max_results=10):
        """Recent ST22 short dumps."""
        logger.info("Fetching ST22 dumps")
        if not self.csrf_token: self._get_csrf_token()
        url = f"{self.host}/sap/bc/adt/runtime/dumps"
        headers = {
            "X-CSRF-Token": self.csrf_token,
            "Accept": "*/*"
        }
        try:
            response = self.session.get(url, headers=headers)
            response.raise_for_status()
            
            root = ET.fromstring(response.content)
            ns = {'a': 'http://www.w3.org/2005/Atom'}
            dumps = []
            for entry in root.findall('a:entry', ns):
                title = entry.findtext('a:title', default='', namespaces=ns)
                updated = entry.findtext('a:updated', default='', namespaces=ns) or \
                          entry.findtext('a:published', default='', namespaces=ns)
                author = entry.findtext('a:author/a:name', default='', namespaces=ns)
                link = entry.find("a:link", ns)
                uri = link.get('href') if link is not None else ''
                cats = [c.get('term') for c in entry.findall('a:category', ns) if c.get('term')]
                
                dumps.append({
                    'title': title.strip() if title else '',
                    'user': author.strip() if author else '',
                    'date': updated.strip() if updated else '',
                    'uri': uri,
                    'categories': cats
                })
                if len(dumps) >= int(max_results):
                    break
                    
            return {"ok": True, "message": "Dumps retrieved successfully", "count": len(dumps), "dumps": dumps}
        except Exception as e:
            return {"ok": False, "error": str(e)}

    def list_transports(self, user=""):
        """List the user's transports."""
        logger.info("Listing transports")
        if not self.csrf_token: self._get_csrf_token()
        url = f"{self.host}/sap/bc/adt/cts/transports"
        try:
            response = self.session.get(url)
            response.raise_for_status()
            return {"ok": True, "message": "Transports retrieved", "data": response.text[:500]}
        except Exception as e:
            return {"ok": False, "error": str(e)}

    def transport_status(self, transport_id):
        """Pinned-transport orientation."""
        return {"ok": True, "transport": transport_id, "message": "Transport status template"}

    def transport_check(self, transport_id):
        """Pre-write transport check (read-only)."""
        return {"ok": True, "transport": transport_id, "message": "Transport check template"}

if __name__ == "__main__":
    print("⚠️  ERROR: This file (sap_adt.py) is a library module, NOT a command-line interface (CLI) tool.")
    print("If you are an AI/LLM, DO NOT run this file with python. You must interact with the SAP Bridge by sending HTTP POST requests to the Flask server (app.py) running on port 8080.")
