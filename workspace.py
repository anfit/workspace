from flask import Flask, request, jsonify, abort, send_file
import os
import shutil
import fnmatch

app = Flask(__name__)

CONFIG = {}
GITIGNORE_PATTERNS = []
ALWAYS_EXCLUDE_DIRS = {'.git', 'venv', 'node_modules', 'target'}

def load_config(path='workspace.properties'):
    if not os.path.exists(path):
        raise RuntimeError(f'Configuration file {path} not found.')
    with open(path, 'r') as file:
        for line in file:
            if line.strip() and not line.startswith('#'):
                key, sep, value = line.partition('=')
                CONFIG[key.strip()] = value.strip()
    if 'base_path' not in CONFIG:
        raise RuntimeError("'base_path' configuration is required.")

    load_gitignore_patterns()

def load_gitignore_patterns():
    GITIGNORE_PATTERNS.clear()
    gitignore_path = os.path.join(CONFIG['base_path'], '.gitignore')
    if os.path.exists(gitignore_path):
        with open(gitignore_path) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#'):
                    GITIGNORE_PATTERNS.append(line)

def is_gitignored(path):
    rel_path = os.path.relpath(path, CONFIG['base_path'])
    for pattern in GITIGNORE_PATTERNS:
        if fnmatch.fnmatch(rel_path, pattern):
            return True
    return False

def check_auth():
    secret = request.headers.get("X-GPT-Secret")
    if not secret or secret != CONFIG["gpt_shared_secret"]:
        abort(403, description="Forbidden: Invalid GPT shared secret")

def safe_path(relative_path):
    full_path = os.path.abspath(os.path.join(CONFIG['base_path'], relative_path))
    if not full_path.startswith(os.path.abspath(CONFIG['base_path'])):
        abort(400, 'Invalid path traversal attempt.')
    return full_path

def resolve_or_create_path(relative_path):
    full_path = safe_path(relative_path=relative_path)
    os.makedirs(os.path.dirname(full_path), exist_ok=True)
    return full_path

@app.route('/files', methods=['GET'])
def list_files():
    check_auth()
    load_gitignore_patterns()
    files = []
    for root, dirs, filenames in os.walk(CONFIG['base_path']):
        dirs[:] = [d for d in dirs if d not in ALWAYS_EXCLUDE_DIRS]
        rel_root = os.path.relpath(root, CONFIG['base_path'])
        for fname in filenames:
            fpath = os.path.join(rel_root, fname)
            full_fpath = os.path.join(root, fname)
            if not is_gitignored(full_fpath):
                files.append(fpath)
    return jsonify(files)

@app.route('/files/<path:filename>', methods=['GET'])
def get_file(filename):
    check_auth()
    full_path = safe_path(filename)
    if not os.path.isfile(full_path):
        abort(404, 'File not found.')
    with open(full_path, 'r') as f:
        content = f.read()
    return jsonify({'path': filename, 'content': content})

@app.route('/files', methods=['POST'])
def create_file():
    check_auth()
    data = request.get_json()
    filename = data.get('path')
    content = data.get('content', '')
    full_path = resolve_or_create_path(filename)
    if os.path.exists(full_path):
        abort(409, 'File already exists.')
    with open(full_path, 'w') as f:
        f.write(content)
    return jsonify({'message': 'File created.', 'path': filename})

@app.route('/files/<path:filename>', methods=['PUT'])
def update_file(filename):
    check_auth()
    full_path = safe_path(filename)
    if not os.path.isfile(full_path):
        abort(404, 'File not found.')
    content = request.get_json().get('content', '')
    with open(full_path, 'w') as f:
        f.write(content)
    return jsonify({'message': 'File updated.', 'path': filename})

@app.route('/files/rename', methods=['POST'])
def rename_file():
    check_auth()
    data = request.get_json()
    old_path = safe_path(data['old_path'])
    new_path = safe_path(data['new_path'])
    if not os.path.exists(old_path):
        abort(404, 'File not found.')
    os.rename(old_path, new_path)
    return jsonify({'message': 'File renamed.', 'old_path': data['old_path'], 'new_path': data['new_path']})

@app.route('/files/move', methods=['POST'])
def move_file():
    check_auth()
    data = request.get_json()
    src_path = safe_path(data['src_path'])
    dest_path = resolve_or_create_path(data['dest_path'])
    if not os.path.exists(src_path):
        abort(404, 'Source file not found.')
    shutil.move(src_path, dest_path)
    return jsonify({'message': 'File moved.', 'src_path': data['src_path'], 'dest_path': data['dest_path']})

@app.route('/files', methods=['DELETE'])
def delete_file():
    check_auth()
    data = request.get_json()
    full_path = safe_path(data['path'])
    if not os.path.isfile(full_path):
        abort(404, 'File not found.')
    os.remove(full_path)
    return jsonify({'message': 'File deleted.', 'path': data['path']})

@app.route('/health', methods=['GET'])
def api_health():
    return jsonify({'status': 'ok'})

@app.route('/openapi.json', methods=['GET'])
def openapi_schema():
    return send_file('openapi.json', mimetype='application/json')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000)
