import os
import tempfile
import pytest
from workspace import app, CONFIG

@pytest.fixture
def client():
    with tempfile.TemporaryDirectory() as tmpdir:
        CONFIG['base_path'] = tmpdir
        CONFIG['gpt_shared_secret'] = 'test-secret'
        app.config['TESTING'] = True

        # Create .gitignore with ignored pattern
        with open(os.path.join(tmpdir, '.gitignore'), 'w') as f:
            f.write('ignored_file.txt\n')

        # Create a file that should be ignored and a .git directory with a file inside
        os.makedirs(os.path.join(tmpdir, '.git'))
        with open(os.path.join(tmpdir, '.git', 'internal.txt'), 'w') as f:
            f.write('should be ignored')

        with open(os.path.join(tmpdir, 'ignored_file.txt'), 'w') as f:
            f.write('ignore this')

        yield app.test_client()

def test_health(client):
    response = client.get('/health')
    assert response.status_code == 200
    assert response.json == {'status': 'ok'}

def test_auth_required(client):
    response = client.get('/files')
    assert response.status_code == 403

def test_list_files_empty(client):
    response = client.get('/files', headers={"X-GPT-Secret": "test-secret"})
    assert response.status_code == 200
    assert './.gitignore' in response.json

def test_create_and_get_file(client):
    headers = {"X-GPT-Secret": "test-secret"}
    file_path = 'testfile.txt'
    content = 'Hello world!'

    response = client.post('/files', json={"path": file_path, "content": content}, headers=headers)
    assert response.status_code == 200

    response = client.get(f'/files/{file_path}', headers=headers)
    assert response.status_code == 200
    assert response.json['content'] == content

def test_update_file(client):
    headers = {"X-GPT-Secret": "test-secret"}
    file_path = 'updatefile.txt'
    initial_content = 'Initial'
    updated_content = 'Updated'

    client.post('/files', json={"path": file_path, "content": initial_content}, headers=headers)
    response = client.put(f'/files/{file_path}', json={"content": updated_content}, headers=headers)
    assert response.status_code == 200

    response = client.get(f'/files/{file_path}', headers=headers)
    assert response.json['content'] == updated_content

def test_rename_file(client):
    headers = {"X-GPT-Secret": "test-secret"}
    old_path = 'oldname.txt'
    new_path = 'newname.txt'

    client.post('/files', json={"path": old_path, "content": "data"}, headers=headers)
    response = client.post('/files/rename', json={"old_path": old_path, "new_path": new_path}, headers=headers)
    assert response.status_code == 200
    assert response.json['new_path'] == new_path

def test_move_file(client):
    headers = {"X-GPT-Secret": "test-secret"}
    src_path = 'srcfile.txt'
    dest_path = 'subdir/destfile.txt'

    client.post('/files', json={"path": src_path, "content": "data"}, headers=headers)
    response = client.post('/files/move', json={"src_path": src_path, "dest_path": dest_path}, headers=headers)
    assert response.status_code == 200
    assert response.json['dest_path'] == dest_path

def test_delete_file(client):
    headers = {"X-GPT-Secret": "test-secret"}
    file_path = 'deletefile.txt'

    client.post('/files', json={"path": file_path, "content": "bye"}, headers=headers)
    response = client.delete('/files', json={"path": file_path}, headers=headers)
    assert response.status_code == 200

    response = client.get(f'/files/{file_path}', headers=headers)
    assert response.status_code == 404

def test_git_and_gitignore_ignored(client):
    headers = {"X-GPT-Secret": "test-secret"}
    visible_path = os.path.join(CONFIG['base_path'], 'visible.txt')
    with open(visible_path, 'w') as f:
        f.write('I am visible')

    response = client.get('/files', headers=headers)
    assert response.status_code == 200
    files = response.json

    assert './ignored_file.txt' not in files
    assert any('visible.txt' in f for f in files)
    assert not any(f.startswith('./.git/') or '/.git/' in f for f in files)