"""
    Test for tenant endpoint's
"""
import random
from sqlalchemy import inspect
from main import app
from database.database import get_db
from database.models_countries import clean_string
from database.services import (get_current_user, get_admin_user)
from database.services_tenant import get_db_schemas
from test.utils import *
# Override dependencies
app.dependency_overrides[get_db] = override_get_db
app.dependency_overrides[get_current_user] = override_get_current_user
app.dependency_overrides[get_admin_user] = override_get_admin_user
app.dependency_overrides[get_db_schemas] = override_get_db_schema
country_alias = COUNTRY['alias']

def test_create_extras(initial_state):
    """
        Test for create extra endpoint
    """
    extra_data = {
        'name': 'test field',
        'display_name': "Testing field",
        'type_id': 1, # Type text
        'brand_id': 1 # toyota
    }
    url = f'/country/{country_alias}/extra'
    resp = client.post(url, json=extra_data)
    assert resp.status_code == 201
    # Check the table of toyota has this new field
    inspector = inspect(initial_state[1].bind)
    columns = inspector.get_columns('toyota') # brand 1
    flag = False
    column_name = clean_string(extra_data['name'])
    for col in columns:
        if col['name'] == column_name:
            flag = True
    assert flag

def test_delete_extra(initial_state):
    """
        Check delete new extra field
    """
    extra_data = {
        'name': 'test field',
        'display_name': "Testing field",
        'type_id': 1, # Type text
        'brand_id': 1 # toyota
    }
    url = f'/country/{country_alias}/extra'
    resp = client.post(url, json=extra_data)
    assert resp.status_code == 201
    # Check the table of toyota has this new field
    inspector = inspect(initial_state[1].bind)
    columns = inspector.get_columns('toyota') # brand 1
    flag = False
    column_name = clean_string(extra_data['name'])
    for col in columns:
        if col['name'] == column_name:
            flag = True
    assert flag
    extra_id = resp.json()['id']
    url = f'/country/{country_alias}/extra/{extra_id}'
    resp = client.delete(url)
    assert resp.status_code == 204
    inspector = inspect(initial_state[1].bind)
    columns = inspector.get_columns('toyota') # brand 1
    flag = False
    column_name = clean_string(extra_data['name'])
    for col in columns:
        if col['name'] == column_name:
            flag = True
    assert flag == False

def test_create_brand(initial_state):
    """
        Create elements for specify brand's
    """
    types_choices = [1,2,3,4,5,6,7,8]
    types_default = {1: 'Default long text',
                        2: "Default short text",
                        3: 1,
                        4: 10000000000,
                        5: 1.01,
                        6: '2024-12-01',
                        7: '00:00:00',
                        8: '2024-12-10T08:51:11'}
    brand_choices = [1,2,3]
    for brand_id in brand_choices:
        type_id = random.choice(types_choices)
        # Create custom field
        extra_data = {
            'name': 'test',
            'display_name': "Testing field",
            'type_id': type_id, # Type text
            'brand_id': brand_id
        }
        url = f'/country/{country_alias}/extra'
        resp = client.post(url, json=extra_data)
        assert resp.status_code == 201
        model_data = {
            'model': "Some model",
            'test': types_default[type_id]
        }
        url = f'/country/{country_alias}/brand/{brand_id}/element'
        resp = client.post(url, json=model_data)
        assert resp.status_code==201
        json_resp = resp.json()
        flag = 'test' in json_resp
        assert flag == True
        assert json_resp['test'] == types_default[type_id]