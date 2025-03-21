import os
import json
import pytest
from flask.testing import FlaskClient
from unittest.mock import patch

# Create dummy config before importing anything else
with open("workspace.properties", "w") as f:
    f.write("base_path=./workspace\ngpt_shared_secret=some-magical-key")

from workspace import app, CONFIG

@pytest.fixture(scope="session", autouse=True)
def cleanup_dummy_config():
    yield
    os.remove("workspace.properties")

@pytest.fixture(scope="session")
def client():
    CONFIG['base_path'] = './workspace'
    os.makedirs(CONFIG['base_path'], exist_ok=True)
    yield app.test_client()
    for root, dirs, files in os.walk(CONFIG['base_path'], topdown=False):
        for name in files:
            os.remove(os.path.join(root, name))
        for name in dirs:
            os.rmdir(os.path.join(root, name))

@pytest.fixture
def setup_sample_files():
    os.makedirs("./workspace/sample", exist_ok=True)
    path = "./workspace/sample/example.txt"
    with open(path, "w") as f:
        f.write("""This is a test file.\nAnother line of text.\ndef test_function():\n    pass\nEnd of file.\n""")
    assert os.path.exists(path)
    yield
    if os.path.exists(path):
        os.remove(path)
    if os.path.exists("./workspace/sample"):
        os.rmdir("./workspace/sample")

def test_search_literal_match(client: FlaskClient, setup_sample_files):
    payload = {"query": "Another line", "mode": "literal", "context_lines": 1}
    response = client.post("/files/search", data=json.dumps(payload), content_type='application/json', headers={"Authorization": "Bearer some-magical-key"})
    assert response.status_code == 200
    results = response.get_json()
    assert any("Another line of text." in result['match'] for result in results)

def test_search_regex_match(client: FlaskClient, setup_sample_files):
    payload = {"query": "def .*\\(\\)", "mode": "regex", "context_lines": 2}
    response = client.post("/files/search", data=json.dumps(payload), content_type='application/json', headers={"Authorization": "Bearer some-magical-key"})
    assert response.status_code == 200
    results = response.get_json()
    assert any("def test_function()" in result['match'] for result in results)
    for result in results:
        assert 'context_before' in result
        assert 'context_after' in result

def test_list_files(client: FlaskClient, setup_sample_files):
    response = client.get("/files", headers={"Authorization": "Bearer some-magical-key"})
    assert response.status_code == 200
    files = response.get_json()
    expected_path = os.path.join("sample", "example.txt")
    assert any(expected_path in f for f in files)

def test_read_file(client: FlaskClient, setup_sample_files):
    response = client.get("/files/sample/example.txt", headers={"Authorization": "Bearer some-magical-key"})
    assert response.status_code == 200
    content = response.get_json()
    assert "test file" in content['content']

def test_create_and_update_file(client: FlaskClient):
    create_payload = {"path": "test_file.txt", "content": "Initial content."}
    response = client.post("/files", data=json.dumps(create_payload), content_type='application/json', headers={"Authorization": "Bearer some-magical-key"})
    assert response.status_code == 200
    update_payload = {"content": "Updated content."}
    response = client.put("/files/test_file.txt", data=json.dumps(update_payload), content_type='application/json', headers={"Authorization": "Bearer some-magical-key"})
    assert response.status_code == 200
    response = client.get("/files/test_file.txt", headers={"Authorization": "Bearer some-magical-key"})
    assert "Updated content." in response.get_json()['content']

def test_rename_and_move_file(client: FlaskClient):
    with open("./workspace/rename_me.txt", "w") as f:
        f.write("dummy")
    rename_payload = {"old_path": "rename_me.txt", "new_path": "renamed.txt"}
    response = client.post("/files/rename", data=json.dumps(rename_payload), content_type='application/json', headers={"Authorization": "Bearer some-magical-key"})
    assert response.status_code == 200
    move_payload = {"src_path": "renamed.txt", "dest_path": "moved/renamed.txt"}
    response = client.post("/files/move", data=json.dumps(move_payload), content_type='application/json', headers={"Authorization": "Bearer some-magical-key"})
    assert response.status_code == 200
    assert os.path.exists("./workspace/moved/renamed.txt")

def test_delete_file(client: FlaskClient):
    with open("./workspace/delete_me.txt", "w") as f:
        f.write("delete me")
    delete_payload = {"path": "delete_me.txt"}
    response = client.delete("/files", data=json.dumps(delete_payload), content_type='application/json', headers={"Authorization": "Bearer some-magical-key"})
    assert response.status_code == 200
    assert not os.path.exists("./workspace/delete_me.txt")

@patch("subprocess.run")
def test_commit_endpoint(mock_run, client: FlaskClient):
    mock_run.return_value = None  # Simulate successful git add/commit
    response = client.post("/commit", data=json.dumps({"message": "test commit"}), content_type='application/json', headers={"Authorization": "Bearer some-magical-key"})
    assert response.status_code == 200
    assert "commit_message" in response.get_json()
    assert mock_run.call_count == 2

def test_health_check(client: FlaskClient):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.get_json()["status"] == "ok"