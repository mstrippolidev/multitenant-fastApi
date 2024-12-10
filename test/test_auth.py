"""
    Testing authentication apis
"""
from main import app
from database.database import get_db
from database.services import (get_current_user, get_admin_user)
from database.models_countries import clean_string
from test.utils import *

app.dependency_overrides[get_db] = override_get_db
app.dependency_overrides[get_current_user] = override_get_current_user
app.dependency_overrides[get_admin_user] = override_get_admin_user

def test_default():
    """
        Test health endpoint
    """
    response = client.get('/')
    assert response.status_code == 200
    assert response.json() == {"message": "Hello"}

def test_user_create(initial_state):
    """
        Test api endpoint for creating a user.
    """
    data_user = {
        'email': "Some invalid email",
        'first_name': "some",
        'last_name': 'some',
        'is_admin': False,
        'password': 'my_own_password'
    }
    resp = client.post('/administration/users', json=data_user)
    assert resp.status_code == 422
    data_user['email'] = 'valid@email.com'
    resp = client.post('/administration/users', json=data_user)
    assert resp.status_code == 201
    response = resp.json()
    assert response['role_id'] == ROL_GUESTS_MOCK['id']
    data_user['is_admin'] = True
    data_user['email'] ='valid2@email.com'
    resp = client.post('/administration/users', json=data_user)
    #print(resp.text, resp.status_code)
    assert resp.status_code == 201
    response = resp.json()
    assert response['role_id'] == ROL_ADMIN_MOCK['id']

def test_login(initial_state):
    """
        Test login user endpoint.
    """
    data = {
        'username': USER_MOCK['email'],
        'password': PASSWORD
    }
    resp = client.post('/administration/users/login', data=data)
    assert resp.status_code == 200
    data['password'] = 'some wrong password'
    resp = client.post('/administration/users/login', data=data)
    assert resp.status_code == 422


def test_edit_user(initial_state):
    """
        Test get endpoint
    """
    user_id = initial_state[0]['id']
    data = {'first_name': "test edit", 'email': "someinvalidEmail@email.com",
            'number': "10343"}
    resp = client.put(f'/administration/user/{user_id}', json=data)
    assert resp.status_code == 200
    assert resp.json()['first_name'] == data['first_name']
    assert resp.json()['number'] == data['number']
    assert resp.json()['email'] != data['email']
    assert resp.json()['email'] == USER_MOCK['email']

def test_delete_user(initial_state):
    """
        Test get endpoint
    """
    user_id = initial_state[0]['id']
    resp = client.delete(f'/administration/user/{user_id}')
    assert resp.status_code == 204
    
def test_create_country(initial_state):
    """
        Test to create a new country
    """
    data = {
        'name': 'United State of America',
        'official_name': 'United State of America',
        'alias': 'USA',
        'area_code': '1'
    }
    resp = client.post('/administration/country', json=data)
    assert resp.status_code == 201
    assert resp.json()['name'] == data['name']
    schema_name = f"{clean_string(data['name'])}_{clean_string(data['alias'])}_schema"
    result = initial_state[1].execute(text(f"SELECT schema_name FROM information_schema.schemata WHERE schema_name = '{schema_name}'"))
    assert result.rowcount > 0

def test_delete_country(initial_state):
    """
        Test to create a new country
    """
    data = {
        'name': 'United State of America',
        'official_name': 'United State of America',
        'alias': 'USA',
        'area_code': '1'
    }
    resp = client.post('/administration/country', json=data)
    assert resp.status_code == 201
    assert resp.json()['name'] == data['name']
    schema_name = f"{clean_string(data['name'])}_{clean_string(data['alias'])}_schema"
    result = initial_state[1].execute(text(f"SELECT schema_name FROM information_schema.schemata WHERE schema_name = '{schema_name}'"))
    assert result.rowcount > 0
    country_id = resp.json()['id']
    resp = client.delete(f'/administration/country/{country_id}')
    assert resp.status_code == 204
    result = initial_state[1].execute(text(f"SELECT schema_name FROM information_schema.schemata WHERE schema_name = '{schema_name}'"))
    assert result.rowcount == 0

