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
uvicorn app.main:app --reload
```

La API estará disponible en `http://localhost:8000`

## Documentación API

- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## Base URL
```
https://your-render-url.onrender.com
```

## Authentication
Todos los endpoints excepto `/api/v1/auth/register/*` y `/api/v1/auth/login` requieren un token Bearer en el header:
```
Authorization: Bearer <your_token>
```

## Formato de Respuesta
Todos los endpoints retornan respuestas en el siguiente formato:
```json
{
  "success": true/false,
  "data": { ... },  // cuando success es true
  "error": {        // cuando success es false
    "code": "ERROR_CODE",
    "message": "Error message"
  }
}
```

## Endpoints

### Autenticación (`/api/v1/auth`)

#### Registro de Cliente
```http
POST /register/client
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

#### Registro de Trabajador
```http
POST /register/worker
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
  "address": "456 Work St"  // Opcional
}
```

#### Login
```http
POST /login
```
Request:
```json
{
  "email": "user@example.com",
  "password": "your_password"
}
```

### Usuarios (`/api/v1/users`)

#### Obtener Usuario Actual
```http
GET /me
```

#### Actualizar Usuario Actual
```http
PUT /me
```
Request:
```json
{
  "first_name": "John",
  "last_name": "Doe",
  "phone_number": "+1234567890"
}
```

#### Listar Trabajadores
```http
GET /workers?category_id=uuid&location_id=uuid
```

### Servicios (`/api/v1/services`)

#### Crear Solicitud de Servicio
```http
POST /request
```
Request:
```json
{
  "worker_id": "worker_uuid",
  "description": "Service description"
}
```

#### Listar Solicitudes (Worker)
```http
GET /requests
```

#### Acción sobre Solicitud
```http
POST /request/{request_id}/action
```
Request:
```json
{
  "action": "accept/reject/cancel/complete"
}
```

#### Calificar Trabajador
```http
POST /request/{service_request_id}/rate
```
Request:
```json
{
  "rating": 5
}
```

### Referencias (`/api/v1/references`)

#### Ubicaciones
```http
GET /locations
```

#### Categorías
```http
GET /categories
```

#### Búsqueda de Trabajadores
```http
GET /workers/search?category_id=uuid&location_id=uuid
```

### Health Check
```http
GET /health
```

## Códigos de Error
- `USER_EXISTS`: Usuario con este email ya existe
- `INVALID_CREDENTIALS`: Email o contraseña inválidos
- `WORKER_NOT_VERIFIED`: Cuenta de trabajador pendiente de verificación
- `UNAUTHORIZED`: Usuario no autorizado para esta acción
- `NOT_FOUND`: Recurso no encontrado
- `INVALID_LOCATION`: Ubicación no encontrada
- `INVALID_CATEGORY`: Categoría no encontrada
- `INVALID_ACTION`: Acción inválida para solicitud de servicio
- `ALREADY_RATED`: Servicio ya calificado
- `VALIDATION_ERROR`: Error en validación de datos
- `FETCH_ERROR`: Error al obtener datos
- `UPDATE_ERROR`: Error al actualizar datos
- `CREATE_ERROR`: Error al crear datos
- `ACTION_ERROR`: Error al realizar acción
- `RATING_ERROR`: Error al procesar calificación

## Estructura del Proyecto
```
.
├── app/
│   ├── api/
│   │   └── v1/
│   │       ├── auth.py
│   │       ├── users.py
│   │       ├── services.py
│   │       └── references.py
│   ├── core/
│   │   ├── auth.py
│   │   ├── config.py
│   │   └── supabase.py
│   ├── middleware/
│   │   └── error_handler.py
│   ├── models/
│   │   ├── user.py
│   │   ├── category.py
│   │   └── location.py
│   └── main.py
├── requirements.txt
└── README.md
```

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