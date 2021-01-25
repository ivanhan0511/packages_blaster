from fastapi.testclient import TestClient

from updblaster.main import app


client = TestClient(app)


def get_places():
    resp = client.get('/places/')
    print(f'unit test')
    assert resp.status_code == 200
    assert resp.json() == {'hello': 'world'}
