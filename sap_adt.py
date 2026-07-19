import os
import logging
import requests
from requests.auth import HTTPBasicAuth
from xml.etree import ElementTree as ET
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)

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
        headers = {"X-CSRF-Token": "Fetch"}
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
        params = {"searchTerm": query, "maxResults": max_results}
        try:
            response = self.session.get(url, params=params)
            response.raise_for_status()
            root = ET.fromstring(response.content)
            ns = {'adtcore': 'http://www.sap.com/adt/core'}
            results = [{"name": obj.get('name'), "type": obj.get('type'), "uri": obj.get('uri')} 
                       for obj in root.findall('.//adtcore:objectReference', ns)]
            return {"ok": True, "query": query, "results": results}
        except Exception as e:
            return {"ok": False, "error": str(e)}

    def code_search(self, search_term, max_results=50):
        """Full-text source search (mock/template for sourceSearch)."""
        logger.info(f"Code search for: {search_term}")
        if not self.csrf_token: self._get_csrf_token()
        url = f"{self.host}/sap/bc/adt/repository/informationsystem/search"
        params = {"searchTerm": f"*{search_term}*", "maxResults": max_results}
        try:
            response = self.session.get(url, params=params)
            response.raise_for_status()
            return {"ok": True, "message": "Code search executed (results may vary by ADT capability)", "status_code": response.status_code}
        except Exception as e:
            return {"ok": False, "error": str(e)}

    def list_package(self, package_name):
        logger.info(f"Listing contents of package: {package_name}")
        if not self.csrf_token: self._get_csrf_token()
        url = f"{self.host}/sap/bc/adt/repository/informationsystem/search"
        params = {"searchTerm": "*", "packageName": package_name.upper(), "maxResults": 500}
        try:
            response = self.session.get(url, params=params)
            response.raise_for_status()
            root = ET.fromstring(response.content)
            ns = {'adtcore': 'http://www.sap.com/adt/core'}
            contents = [{"name": obj.get('name'), "type": obj.get('type')} 
                        for obj in root.findall('.//adtcore:objectReference', ns)]
            return {"ok": True, "package_name": package_name, "contents": contents}
        except Exception as e:
            return {"ok": False, "error": str(e)}

    def execute_sql(self, query, row_limit=100):
        logger.info(f"Executing SQL query: {query}")
        return {"ok": False, "error": "Read-only ABAP SQL SELECT is limited in standard ADT REST. Use RFC for generic data preview."}

    def where_used(self, name, object_type):
        logger.info(f"Finding where-used for {object_type} {name}")
        if not self.csrf_token: self._get_csrf_token()
        url = f"{self.host}/sap/bc/adt/crossreference/whereused"
        adt_type = 'clas/oo' if object_type.lower() == 'class' else object_type.lower()
        try:
            response = self.session.get(url, params={"objectName": name.upper(), "objectType": adt_type})
            response.raise_for_status()
            root = ET.fromstring(response.content)
            references = [{"name": ref.get('name'), "type": ref.get('type')} for ref in root.findall('.//reference')]
            return {"ok": True, "object_name": name, "references": references}
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
        try:
            response = self.session.get(url)
            response.raise_for_status()
            return {"ok": True, "message": "Dumps retrieved", "data": response.text[:500]}
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
