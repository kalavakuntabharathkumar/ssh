from fastapi.testclient import TestClient
from app import app

client = TestClient(app)

def test_health():
    response = client.get('/health')
    assert response.status_code == 200
    assert response.json()['status'] == 'healthy'

def test_create_incident():
    response = client.post('/incidents', json={"service": "api-gateway", "state": "degraded", "severity": "medium", "message": "Elevated response time"})
    assert response.status_code == 201
    assert response.json()['state'] == 'degraded'
    return response.json()['id']

def test_invalid_state():
    response = client.post('/incidents', json={"service": "worker", "state": "broken", "severity": "high", "message": "Invalid state"})
    assert response.status_code == 422

def test_recovery_flow():
    response = client.post('/incidents', json={"service": "worker", "state": "unavailable", "severity": "high", "message": "Worker unavailable"})
    assert response.status_code == 201
    incident_id = response.json()['id']
    recovered = client.patch(f'/incidents/{incident_id}/recover')
    assert recovered.status_code == 200
    assert recovered.json()['state'] == 'recovered'

def test_service_summary():
    response = client.get('/services/api-gateway/summary')
    assert response.status_code == 200
    assert response.json()['service'] == 'api-gateway'
