# Multitenant FastAPI: Dynamic Schema Engine

A high-performance **Schema-per-Tenant** application built with **FastAPI** and **PostgreSQL**.

This project goes beyond standard CRUD operations by implementing a **Runtime Dynamic Model Engine**. It allows tenants (Countries) to have isolated database schemas and modify their data structures (tables) on the fly, with the API automatically generating corresponding Pydantic validation schemas in real-time.

## 🏗 Architectural Overview

### 1. Schema-Based Multitenancy
Instead of using a shared schema with a `tenant_id` column, this application isolates data by creating a dedicated PostgreSQL schema for each country (e.g., `united_states_us_schema`, `mexico_mx_schema`).

* **Resolution Strategy**: Tenant context is resolved via the URL path: `/country/{country_alias}/...`.
* **Context Switching**: Middleware and Dependencies intercept the request, resolve the alias to a specific schema, and configure the SQLAlchemy session `search_path`. This ensures complete data isolation at the database level.

### 2. Runtime Dynamic Modeling
The core innovation of this API is the ability to handle **Database Schema Evolution** without downtime or manual migrations.

* **Dynamic DDL**: When a user adds a new field via the API, the application executes raw SQL (`ALTER TABLE`) immediately.
* **Dynamic Validation**: Since the table structure changes at runtime, static Pydantic models are insufficient. The application inspects the updated SQLAlchemy table metadata and generates new Pydantic models in memory using `create_model`.

## 🔒 Security & Auth
* **OAuth2 Integration**: Authentication is handled via **Google OAuth** (using Authlib).
* **Role-Based Access Control (RBAC)**: Custom dependencies enforce permissions. Critical operations (like creating new tenants) are restricted to users with the `admin` role.
* **Session Management**: Secure, HTTP-only signed cookies via `SessionMiddleware`.

---

## 💻 Core Logic & Snippets

### A. Dynamic Schema Resolution
The application dynamically switches the PostgreSQL `search_path` based on the request.

```python
# database/models_countries.py

class MultiTenantBase(object):
    """
    Base class that allows swapping schemas at runtime.
    """
    _schema = None

    @declared_attr
    def __table_args__(cls):
        return {'schema': cls._schema}

    @classmethod
    def set_schema(cls, schema):
        cls._schema = schema

def format_schema(country: any):
    """
    Formats the schema name based on country data: 'united_states_us_schema'
    """

    name = clean_string(country.name)
    alias = clean_string(country.alias)
    return f"{name}_{alias}_schema"
```
### B. Dynamic Pydantic Model Generation
The system bridges the gap between flexible SQL tables and API validation by generating Pydantic models on demand. This allows the API to validate and return fields that were created by users at runtime.

```python
# pydantic_models/pydanctic_coutries.py

def generate_pydantic_model(table: Table) -> Type[BaseModel]:
    """
    Dynamically creates a Pydantic model based on the current state of a SQL table.
    Ensures that dynamic 'Extra' fields are included in API validation.
    """
    fields = {}
    for column in table.columns: 
        column_type = column.type.python_type
        # Handle Nullable fields as Optional
        if column.nullable:
            fields[column.name] = (Optional[column_type], None)
        else: 
            fields[column.name] = (column_type, ...)
    
    # Construct the Pydantic class in memory
    model = create_model(
        table.name.capitalize(),
        **fields,
        __config__=Config
    )
    return model
```
### C. Runtime Column Injection (Schema Evolution)
The API allows users to register new "Extra" attributes. When a new attribute is created, the system performs a live DDL operation to alter the physical table structure within the specific tenant's schema.

```python
# router_tenant.py

@router.post('/extra', status_code=201)
async def create_extra(country_alias: str, data: ExtrasCreate, 
                       user: UserResponse = Depends(get_admin_user),
                       db: Session = Depends(get_db_schemas)):
    """
    Demonstrates Dynamic Logic:
    1. Persists field metadata in the 'extras' table of the tenant schema.
    2. Immediately triggers an 'ALTER TABLE' to add the physical column.
    """
    extra_model = Extras(**data.model_dump())
    extra_db = await save_instance(extra_model, db)
    
    # Execute the DDL command to modify the physical database structure
    await add_column(extra_db, db) 
    return extra_db
```
