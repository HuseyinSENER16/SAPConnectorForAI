from flask import Flask, request, jsonify
import logging
from sap_adt import SAPADTHandler

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

app = Flask(__name__)
adt_handler = SAPADTHandler()

def get_json_or_error():
    data = request.get_json(silent=True)
    if data is None:
        data = {}
    return data

@app.route('/health', methods=['GET'])
def health_check():
    return jsonify(adt_handler.ping())

@app.route('/tool/ping', methods=['GET', 'POST'])
def ping():
    return jsonify(adt_handler.ping())

@app.route('/tool/adt_doctor', methods=['POST'])
def adt_doctor():
    return jsonify(adt_handler.doctor())

@app.route('/tool/adt_logon', methods=['POST'])
def adt_logon():
    return jsonify(adt_handler.logon())

@app.route('/tool/adt_get_source', methods=['POST'])
def adt_get_source():
    data = get_json_or_error()
    return jsonify(adt_handler.get_source(data.get("name"), data.get("object_type")))

@app.route('/tool/adt_search', methods=['POST'])
def adt_search():
    data = get_json_or_error()
    return jsonify(adt_handler.search(data.get("query"), data.get("max_results", 50)))

@app.route('/tool/adt_code_search', methods=['POST'])
def adt_code_search():
    data = get_json_or_error()
    return jsonify(adt_handler.code_search(data.get("search_term"), data.get("max_results", 50)))

@app.route('/tool/adt_list_package', methods=['POST'])
def adt_list_package():
    data = get_json_or_error()
    return jsonify(adt_handler.list_package(data.get("package_name")))

@app.route('/tool/adt_sql', methods=['POST'])
def adt_sql():
    data = get_json_or_error()
    return jsonify(adt_handler.execute_sql(data.get("query"), data.get("row_limit", 100)))

@app.route('/tool/adt_where_used', methods=['POST'])
def adt_where_used():
    data = get_json_or_error()
    return jsonify(adt_handler.where_used(data.get("name"), data.get("object_type")))

@app.route('/tool/adt_revisions', methods=['POST'])
def adt_revisions():
    data = get_json_or_error()
    return jsonify(adt_handler.revisions(data.get("name"), data.get("object_type")))

@app.route('/tool/adt_syntax_check', methods=['POST'])
def adt_syntax_check():
    data = get_json_or_error()
    return jsonify(adt_handler.syntax_check(data.get("name"), data.get("object_type")))

@app.route('/tool/adt_atc_check', methods=['POST'])
def adt_atc_check():
    data = get_json_or_error()
    return jsonify(adt_handler.atc_check(data.get("name"), data.get("object_type")))

@app.route('/tool/adt_unit_test', methods=['POST'])
def adt_unit_test():
    data = get_json_or_error()
    return jsonify(adt_handler.unit_test(data.get("name"), data.get("object_type")))

@app.route('/tool/adt_check_scatter', methods=['POST'])
def adt_check_scatter():
    data = get_json_or_error()
    return jsonify(adt_handler.check_scatter(data.get("name"), data.get("object_type")))

@app.route('/tool/adt_inactive_objects', methods=['POST'])
def adt_inactive_objects():
    data = get_json_or_error()
    return jsonify(adt_handler.inactive_objects(data.get("user", "")))

@app.route('/tool/adt_badi_discovery', methods=['POST'])
def adt_badi_discovery():
    data = get_json_or_error()
    return jsonify(adt_handler.badi_discovery(data.get("name")))

@app.route('/tool/adt_dumps', methods=['POST'])
def adt_dumps():
    data = get_json_or_error()
    return jsonify(adt_handler.dumps(data.get("max_results", 10)))

@app.route('/tool/adt_list_transports', methods=['POST'])
def adt_list_transports():
    data = get_json_or_error()
    return jsonify(adt_handler.list_transports(data.get("user", "")))

@app.route('/tool/adt_transport_status', methods=['POST'])
def adt_transport_status():
    data = get_json_or_error()
    return jsonify(adt_handler.transport_status(data.get("transport_id")))

@app.route('/tool/adt_transport_check', methods=['POST'])
def adt_transport_check():
    data = get_json_or_error()
    return jsonify(adt_handler.transport_check(data.get("transport_id")))

if __name__ == '__main__':
    logger.info("Starting SAP ADT Python Bridge on http://127.0.0.1:8080")
    app.run(host='127.0.0.1', port=8080, debug=True)
