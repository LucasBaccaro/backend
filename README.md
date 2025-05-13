# Services API

API backend para una plataforma de servicios entre trabajadores y clientes, construida con FastAPI y Supabase.

## Características Principales

- Autenticación de usuarios (clientes y trabajadores)
- Verificación manual de trabajadores
- Gestión de ubicaciones y categorías
- API RESTful con respuestas estandarizadas
- Documentación automática con Swagger/ReDoc
- Manejo de errores consistente
- Validación de datos con Pydantic

## Requisitos

- Python 3.8+
- Supabase (base de datos y autenticación)
- Variables de entorno configuradas

## Configuración

1. Clonar el repositorio:
   ```bash
   git clone <repository-url>
   cd <repository-name>
   ```

2. Crear y activar entorno virtual:
   ```bash
   python -m venv .venv
   # Windows
   .venv\Scripts\activate
   # Unix/MacOS
   source .venv/bin/activate
   ```

3. Instalar dependencias:
   ```bash
   pip install -r requirements.txt
   ```

4. Configurar variables de entorno:
   Crear un archivo `.env` en la raíz del proyecto con:
   ```env
   SUPABASE_URL=your_supabase_url
   SUPABASE_KEY=your_supabase_anon_key
   SUPABASE_SERVICE_KEY=your_supabase_service_key
   SECRET_KEY=your_jwt_secret_key
   ALGORITHM=HS256
   ACCESS_TOKEN_EXPIRE_MINUTES=1440
   ```

## Ejecución

Para iniciar el servidor de desarrollo:
```bash
uvicorn main:app --reload
```

La API estará disponible en `http://localhost:8000`

## Documentación API

- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## Endpoints

### Autenticación (`/api/v1/auth`)

#### Registro de Cliente
- `POST /register/client`
- Body:
  ```json
  {
    "email": "string",
    "password": "string",
    "first_name": "string",
    "last_name": "string",
    "dni": "string",
    "phone_number": "string",
    "address": "string",
    "location_id": "string"
  }
  ```

#### Registro de Trabajador
- `POST /register/worker`
- Body:
  ```json
  {
    "email": "string",
    "password": "string",
    "first_name": "string",
    "last_name": "string",
    "dni": "string",
    "phone_number": "string",
    "location_id": "string",
    "category_id": "string",
    "address": "string (opcional)"
  }
  ```

#### Login
- `POST /token`
- Body (form-urlencoded):
  ```
  grant_type=password
  username=email
  password=password
  ```

#### Perfil de Usuario
- `GET /me`
- Requiere token de autenticación

### Referencias (`/api/v1/references`)

#### Categorías
- `GET /categories`
- Retorna lista de categorías disponibles

#### Ubicaciones
- `GET /locations`
- Retorna lista de ubicaciones disponibles

#### Búsqueda de Trabajadores
- `GET /workers/search`
- Query Parameters:
  - `category_id`: ID de la categoría
  - `location_id`: ID de la ubicación
- Requiere autenticación (solo clientes)
- Retorna lista de trabajadores verificados que:
  - Pertenezcan a la categoría especificada
  - Estén en la ubicación especificada
  - Estén verificados (`is_verified = true`)
- Ejemplo de respuesta:
  ```json
  {
    "success": true,
    "data": [
      {
        "id": "worker_id",
        "email": "worker@example.com",
        "first_name": "Juan",
        "last_name": "Pérez",
        "dni": "12345678",
        "phone_number": "+5491122334455",
        "role": "worker",
        "location_id": "loc_001",
        "category_id": "cat_001",
        "is_verified": true,
        "address": "Calle 123"
      }
    ],
    "error": null
  }
  ```

## Endpoints de Servicios

### Crear solicitud de servicio (cliente)
- `POST /api/v1/services/request`
- Headers: `Authorization: Bearer <token del cliente>`
- Body:
  ```json
  {
    "worker_id": "uuid-del-worker",
    "description": "Detalle del trabajo a realizar"
  }
  ```
- Respuesta: objeto ServiceRequestResponse

### Listar solicitudes de servicio (worker)
- `GET /api/v1/services/requests`
- Headers: `Authorization: Bearer <token del worker>`
- Respuesta: lista de ServiceRequestResponse

### Acción sobre solicitud (worker)
- `POST /api/v1/services/request/{request_id}/action`
- Headers: `Authorization: Bearer <token del worker>`
- Body:
  ```json
  { "action": "accepted" } // o "rejected", "cancelled"
  ```
- Respuesta: objeto ServiceRequestResponse actualizado

## Modelos de Datos

### Usuario
```python
class UserBase:
    email: EmailStr
    first_name: str
    last_name: str
    dni: str
    phone_number: str
    role: UserRole
    location_id: Optional[str]

class UserInDB(UserBase):
    id: str
    is_active: bool
    is_verified: Optional[bool]
    category_id: Optional[str]
    address: Optional[str]
    average_rating: float  # Promedio de calificaciones recibidas (solo workers)
    ratings_count: int    # Cantidad de calificaciones recibidas (solo workers)
```

### Cliente
```python
class ClientBase(UserBase):
    address: str  # Requerido
```

### Trabajador
```python
class WorkerBase(UserBase):
    address: Optional[str]
    category_id: str
    is_verified: bool  # Requiere verificación manual
```

### Respuesta API
```python
class APIResponse:
    success: bool
    data: Optional[T]
    error: Optional[ErrorDetail]
```

### Modelo de ServiceRequest
```python
class ServiceRequestBase(BaseModel):
    worker_id: str
    description: str

class ServiceRequestCreate(ServiceRequestBase):
    pass

class ServiceRequestInDB(ServiceRequestBase):
    id: str
    client_id: str
    status: ServiceRequestStatus
    created_at: datetime
    updated_at: datetime

class ServiceRequestResponse(ServiceRequestInDB):
    class Config:
        from_attributes = True

class ServiceRequestStatus(str, Enum):
    pending = "pending"
    accepted = "accepted"
    rejected = "rejected"
    cancelled = "cancelled"
    completed = "completed"
```

## Flujo de Autenticación

1. **Registro de Cliente**:
   - Email auto-confirmado
   - No requiere verificación manual
   - Debe proporcionar dirección y ubicación

2. **Registro de Trabajador**:
   - Email auto-confirmado
   - Requiere verificación manual (`is_verified`)
   - Debe seleccionar categoría y ubicación
   - Dirección opcional

3. **Login**:
   - Usa OAuth2 con password grant
   - Trabajadores no verificados no pueden iniciar sesión
   - Retorna JWT token para autenticación

## Manejo de Errores

La API utiliza un formato de respuesta consistente para errores:
```json
{
    "success": false,
    "data": null,
    "error": {
        "code": "ERROR_CODE",
        "message": "Descripción del error",
        "details": null
    }
}
```

Códigos de error comunes:
- `VALIDATION_ERROR`: Error en validación de datos
- `USER_EXISTS`: Email ya registrado
- `INVALID_CREDENTIALS`: Credenciales incorrectas
- `WORKER_NOT_VERIFIED`: Trabajador pendiente de verificación
- `INVALID_LOCATION`: Ubicación no válida
- `INVALID_REFERENCE`: Referencia (categoría/ubicación) no válida

## Colecciones Postman

El proyecto incluye colecciones Postman para pruebas:
- `postman/clients-api.json`: Endpoints para clientes
- `postman/workers-api.json`: Endpoints para trabajadores

## Desarrollo

### Estructura del Proyecto
```
.
├── app/
│   ├── api/
│   │   └── v1/
│   │       ├── auth.py
│   │       └── references.py
│   │   
│   ├── core/
│   │   ├── auth.py
│   │   ├── config.py
│   │   └── supabase.py
│   │   
│   ├── middleware/
│   │   └── error_handler.py
│   │   
│   └── models/
│   │   ├── user.py
│   │   ├── category.py
│   │   └── location.py
│   │   
│   ├── postman/
│   │   ├── clients-api.json
│   │   └── workers-api.json
│   │   
│   └── main.py
│   
├── requirements.txt
└── README.md 
```

### Próximos Pasos
- Implementar endpoints para gestión de servicios
- Añadir sistema de calificaciones
- Implementar búsqueda de trabajadores
- Añadir sistema de notificaciones
- Implementar gestión de pagos 

## Chat en Servicios (WebSocket)

- El chat entre cliente y worker solo está habilitado cuando el service request está en estado `accepted`.
- Los mensajes se almacenan en la tabla `service_messages` con los campos: `service_request_id`, `sender_id`, `message`, `created_at`.
- Al conectarse al WebSocket, el usuario recibe solo el historial de mensajes de ese servicio.
- Si el status del servicio cambia a otro distinto de `accepted`, el chat se cierra automáticamente.

### Endpoint WebSocket
- URL: `ws://localhost:8080/ws/services/{service_request_id}/chat?token={JWT}`
- Solo pueden conectarse el cliente y el worker del servicio.
- El historial se envía al conectar, y los mensajes nuevos se transmiten en tiempo real.

### Probar el chat
1. Levanta el backend en el puerto 8080.
2. Sirve el archivo `service_chat_test.html` desde un servidor estático (por ejemplo, `python -m http.server 8081`).
3. Abre el HTML en el navegador y completa:
   - Service Request ID (debe estar en estado `accepted`)
   - JWT Token (del cliente o worker)
4. Haz clic en "Conectar" y prueba enviar/recibir mensajes.

## Sistema de Calificaciones

- Solo los clientes pueden calificar a los workers, una vez por servicio completado.
- El endpoint es: `POST /api/v1/services/request/{service_request_id}/rate` con body `{ "rating": 1-5 }`.
- Cada vez que un worker recibe una calificación, se actualizan automáticamente los campos `average_rating` y `ratings_count` en la tabla `users`.
- Cuando se consulta un worker (en búsquedas o perfil), estos campos ya vienen incluidos en la respuesta.
- No se permiten comentarios, solo puntaje.

**Ejemplo de respuesta de worker:**
```json
{
  "id": "...",
  "email": "worker@example.com",
  ...
  "average_rating": 4.5,
  "ratings_count": 12
}
```

# Services API Documentation

## Base URL
```
https://your-render-url.onrender.com
```

## Authentication
All endpoints except `/api/v1/auth/register/*` and `/api/v1/auth/login` require a Bearer token in the Authorization header:
```
Authorization: Bearer <your_token>
```

## Common Response Format
All endpoints return responses in the following format:
```json
{
  "success": true/false,
  "data": { ... },  // when success is true
  "error": {        // when success is false
    "code": "ERROR_CODE",
    "message": "Error message"
  }
}
```

## Authentication Endpoints

### Register Client
```http
POST /api/v1/auth/register/client
```
Request:
```json
{
  "email": "client@example.com",
  "password": "your_password",
  "first_name": "John",
  "last_name": "Doe",
  "dni": "12345678",
  "phone_number": "+1234567890",
  "address": "123 Main St",
  "location_id": "location_uuid"
}
```
Response:
```json
{
  "success": true,
  "data": {
    "id": "user_uuid",
    "email": "client@example.com",
    "first_name": "John",
    "last_name": "Doe",
    "dni": "12345678",
    "phone_number": "+1234567890",
    "role": "client",
    "location_id": "location_uuid",
    "address": "123 Main St",
    "is_verified": null,
    "created_at": "2024-03-21T12:00:00Z"
  }
}
```

### Register Worker
```http
POST /api/v1/auth/register/worker
```
Request:
```json
{
  "email": "worker@example.com",
  "password": "your_password",
  "first_name": "Jane",
  "last_name": "Smith",
  "dni": "87654321",
  "phone_number": "+1234567890",
  "location_id": "location_uuid",
  "category_id": "category_uuid",
  "address": "456 Work St"  // Optional
}
```
Response:
```json
{
  "success": true,
  "data": {
    "id": "user_uuid",
    "email": "worker@example.com",
    "first_name": "Jane",
    "last_name": "Smith",
    "dni": "87654321",
    "phone_number": "+1234567890",
    "role": "worker",
    "location_id": "location_uuid",
    "category_id": "category_uuid",
    "address": "456 Work St",
    "is_verified": false,
    "created_at": "2024-03-21T12:00:00Z"
  }
}
```

### Login
```http
POST /api/v1/auth/login
```
Request:
```json
{
  "email": "user@example.com",
  "password": "your_password"
}
```
Response:
```json
{
  "success": true,
  "data": {
    "access_token": "jwt_token",
    "token_type": "bearer",
    "user": {
      "id": "user_uuid",
      "email": "user@example.com",
      "first_name": "John",
      "last_name": "Doe",
      "phone": "+1234567890",
      "role": "client/worker",
      "location_id": "location_uuid",
      "category_id": "category_uuid", // only for workers
      "is_verified": true/false/null,
      "created_at": "2024-03-21T12:00:00Z"
    }
  }
}
```

## User Endpoints

### Get Current User
```http
GET /api/v1/users/me
```
Response:
```json
{
  "success": true,
  "data": {
    "id": "user_uuid",
    "email": "user@example.com",
    "first_name": "John",
    "last_name": "Doe",
    "phone": "+1234567890",
    "role": "client/worker",
    "location_id": "location_uuid",
    "category_id": "category_uuid", // only for workers
    "is_verified": true/false/null,
    "created_at": "2024-03-21T12:00:00Z"
  }
}
```

### Update Current User
```http
PUT /api/v1/users/me
```
Request:
```json
{
  "first_name": "John",
  "last_name": "Doe",
  "phone": "+1234567890"
}
```
Response:
```json
{
  "success": true,
  "data": {
    "id": "user_uuid",
    "email": "user@example.com",
    "first_name": "John",
    "last_name": "Doe",
    "phone": "+1234567890",
    "role": "client/worker",
    "location_id": "location_uuid",
    "category_id": "category_uuid", // only for workers
    "is_verified": true/false/null,
    "created_at": "2024-03-21T12:00:00Z"
  }
}
```

### List Workers
```http
GET /api/v1/users/workers?category_id=uuid&location_id=uuid
```
Response:
```json
{
  "success": true,
  "data": [
    {
      "id": "user_uuid",
      "email": "worker@example.com",
      "first_name": "Jane",
      "last_name": "Smith",
      "phone": "+1234567890",
      "role": "worker",
      "location_id": "location_uuid",
      "category_id": "category_uuid",
      "is_verified": true,
      "average_rating": 4.5,
      "ratings_count": 10,
      "created_at": "2024-03-21T12:00:00Z"
    }
  ]
}
```

## Service Endpoints

### Create Service Request
```http
POST /api/v1/services/request
```
Request:
```json
{
  "worker_id": "worker_uuid",
  "description": "Service description"
}
```
Response:
```json
{
  "success": true,
  "data": {
    "id": "request_uuid",
    "client_id": "client_uuid",
    "worker_id": "worker_uuid",
    "description": "Service description",
    "status": "pending",
    "created_at": "2024-03-21T12:00:00Z"
  }
}
```

### List Service Requests (Worker)
```http
GET /api/v1/services/requests
```
Response:
```json
{
  "success": true,
  "data": [
    {
      "id": "request_uuid",
      "client_id": "client_uuid",
      "worker_id": "worker_uuid",
      "description": "Service description",
      "status": "pending/accepted/rejected/cancelled/completed",
      "created_at": "2024-03-21T12:00:00Z"
    }
  ]
}
```

### Action Service Request
```http
POST /api/v1/services/request/{request_id}/action
```
Request:
```json
{
  "action": "accept/reject/cancel/complete"
}
```
Response:
```json
{
  "success": true,
  "data": {
    "id": "request_uuid",
    "client_id": "client_uuid",
    "worker_id": "worker_uuid",
    "description": "Service description",
    "status": "accepted/rejected/cancelled/completed",
    "created_at": "2024-03-21T12:00:00Z"
  }
}
```

### Rate Worker
```http
POST /api/v1/services/request/{service_request_id}/rate
```
Request:
```json
{
  "rating": 5
}
```
Response:
```json
{
  "success": true,
  "data": {
    "average_rating": 4.5,
    "ratings_count": 10
  }
}
```

## Reference Endpoints

### Get Locations
```http
GET /api/v1/references/locations
```
Response:
```json
{
  "success": true,
  "data": [
    {
      "id": "location_uuid",
      "name": "Location Name",
      "created_at": "2024-03-21T12:00:00Z"
    }
  ]
}
```

### Get Categories
```http
GET /api/v1/references/categories
```
Response:
```json
{
  "success": true,
  "data": [
    {
      "id": "category_uuid",
      "name": "Category Name",
      "created_at": "2024-03-21T12:00:00Z"
    }
  ]
}
```

### Search Workers
```http
GET /api/v1/references/workers/search?category_id=uuid&location_id=uuid
```
Response:
```json
{
  "success": true,
  "data": [
    {
      "id": "worker_uuid",
      "email": "worker@example.com",
      "first_name": "Jane",
      "last_name": "Smith",
      "phone": "+1234567890",
      "role": "worker",
      "location_id": "location_uuid",
      "category_id": "category_uuid",
      "is_verified": true,
      "average_rating": 4.5,
      "ratings_count": 10,
      "created_at": "2024-03-21T12:00:00Z"
    }
  ]
}
```

## Health Check
```http
GET /health
```
Response:
```json
{
  "success": true,
  "data": {
    "status": "healthy",
    "uptime_seconds": 3600,
    "uptime_formatted": "1:00:00",
    "version": "1.0.0",
    "environment": "production"
  }
}
```

## Error Codes
- `USER_EXISTS`: User with this email already exists
- `INVALID_CREDENTIALS`: Invalid email or password
- `WORKER_NOT_VERIFIED`: Worker account is pending verification
- `UNAUTHORIZED`: User is not authorized to perform this action
- `NOT_FOUND`: Resource not found
- `INVALID_LOCATION`: Location not found
- `INVALID_CATEGORY`: Category not found
- `INVALID_ACTION`: Invalid action for service request
- `ALREADY_RATED`: Service already rated
- `VALIDATION_ERROR`: Request validation failed
- `FETCH_ERROR`: Error fetching data
- `UPDATE_ERROR`: Error updating data
- `CREATE_ERROR`: Error creating data
- `ACTION_ERROR`: Error performing action
- `RATING_ERROR`: Error processing rating