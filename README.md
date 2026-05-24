# 🚀 Tamila SAAS

> Plataforma de gestión empresarial con sistema de permisos granulares, autenticación segura y arquitectura escalable. Base sólida para integración de IA.

[![Python](https://img.shields.io/badge/Python-3.12-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115-009688?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![React](https://img.shields.io/badge/React-19-61DAFB?logo=react&logoColor=black)](https://github.com/peligro/python-demo-ia-react)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-15-4169E1?logo=postgresql&logoColor=white)](https://www.postgresql.org/)
[![Redis](https://img.shields.io/badge/Redis-7-DC382D?logo=redis&logoColor=white)](https://redis.io/)
[![Docker](https://img.shields.io/badge/Docker-24-2496ED?logo=docker&logoColor=white)](https://www.docker.com/)
---

## 📋 Tabla de Contenidos

- [✨ Características](#-características)
- [🏗️ Arquitectura](#️-arquitectura)
- [🛠️ Tecnologías](#️-tecnologías)
- [📁 Estructura del Proyecto](#-estructura-del-proyecto)
- [🚀 Instalación](#-instalación)
- [⚙️ Variables de Entorno](#️-variables-de-entorno)
- [🔐 Sistema de Permisos](#-sistema-de-permisos)
- [📚 Documentación API](#-documentación-api)
- [🧪 Testing](#-testing)
- [🤖 Módulos para Inteligencia Artificial](#-módulos-para-inteligencia-artificial)
- [🤝 Contribuir](#-contribuir)
- [📄 Licencia](#-licencia)

---

## ✨ Características

### 🔐 Seguridad & Autenticación
- ✅ Autenticación con cookies HTTP-only + sesiones en Redis
- ✅ Validación de estado de usuario (activo/inactivo) en cada request
- ✅ Hash de contraseñas con bcrypt
- ✅ Middleware de autorización con respuestas genéricas (fail securely)
- ✅ Protección contra escalada de privilegios con `view_all_register`
- ✅ Rate limiting con slowapi + Redis (120 requests/minuto)
- ✅ Headers de seguridad OWASP (CSP, X-Frame-Options, etc.)

### 🎯 Sistema de Permisos Granulares
- ✅ Módulos configurables con slugs únicos (`/settings/users`, etc.)
- ✅ Items/acciones con códigos identificadores (`crear_usuario`, `editar_perfil`, etc.)
- ✅ Asignación flexible: Perfil → Módulos → Items
- ✅ Llave maestra: `view_all_register` otorga acceso total
- ✅ Menús dinámicos (AppMenu/HomeMenu) filtrados por perfil

### 🏗️ Arquitectura Escalable
- ✅ Patrón **Router + Service + Schema**: separación clara de responsabilidades
- ✅ SQLModel para modelos + validaciones Pydantic
- ✅ Alembic para migraciones de base de datos
- ✅ Middlewares reutilizables: auth, RBAC, security headers, rate limit

### 📦 Módulos Incluidos
| Módulo | Descripción | Endpoints Principales |
|--------|------------|---------------------|
| 👤 **Users** | Gestión de usuarios con metadata | `GET/POST/PUT/DELETE /users` |
| 🔐 **Auth** | Login, logout, me | `POST /auth/login`, `GET /auth/me` |
| 🧩 **Profiles** | Roles/perfiles con permisos asignados | `GET/POST/PUT/DELETE /profiles` |
| 🧱 **Modules** | Definición de módulos del sistema | `GET/POST/PUT/DELETE /modules` |
| ⚡ **Items** | Acciones/permisos granulares | `GET/POST/PUT/DELETE /items` |
| 📊 **States** | Estados genéricos (activo, inactivo, etc.) | `GET/POST/PUT/DELETE /states` |
| 📑 **App Menu** | Menús dinámicos para sidebar | `GET /app-menu/all`, CRUD protegido |
| 🏠 **Home Menu** | Tarjetas para dashboard home | `GET /home-menu/all`, CRUD protegido |

### 🛡️ Calidad & DevOps
- ✅ Swagger automático con FastAPI
- ✅ Validaciones con Pydantic + mensajes personalizados
- ✅ Docker compose para desarrollo (Python, Postgres, Redis, LocalStack)
- ✅ Límites de recursos configurados (CPU, RAM, procesos)
- ✅ `pip-audit` para escaneo de vulnerabilidades en dependencias

---

## 🏗️ Arquitectura

```text
┌─────────────────────────────────────────┐
│ Frontend (React)                        │
│ • TypeScript + Bootstrap 5              │
│ • Consumo de API REST                   │
│ • Renderizado dinámico de menús         │
└─────────────────┬───────────────────────┘
                  │ HTTPS/JSON + Cookies
                  ▼
┌─────────────────────────────────────────┐
│ Backend (Python + FastAPI)              │
├─────────────────────────────────────────┤
│ 🌐 main.py                              │
│ ├─ Middlewares: CORS, Security, Auth    │
│ └─ Registro de routers por módulo       │
│                                         │
│ 🔐 middleware/                          │
│ ├─ auth.py → Validación de sesión       │
│ ├─ rbac.py → Autorización granular      │
│ ├─ security_headers.py → Headers OWASP  │
│ └─ rate_limiter.py → slowapi + Redis    │
│                                         │
│ 📦 router/{module}/                     │
│ ├─ {module}_router.py → Endpoints HTTP  │
│                                         │
│ ⚙️ services/{module}/                   │
│ ├─ {module}_service.py → Lógica + DB    │
│                                         │
│ 📄 schemas/{module}.py                  │
│ ├─ Pydantic: Request/Response + valid.  │
│                                         │
│ 🗄️ models/                              │
│ ├─ SQLModel: User, Profile, Module, etc.│
└─────────────────┬───────────────────────┘
                  │ SQLModel/SQLAlchemy
                  ▼
┌─────────────────────────────────────────┐
│ Capa de Datos                           │
├─────────────────────────────────────────┤
│ 🐘 PostgreSQL 15 + pgvector             │
│ • Tablas: user, profile, module, item   │
│ • Relaciones: Profile↔Module↔Item       │
│                                         │
│ 🔴 Redis                                │
│ • Sesiones de usuario (TTL configurable)│
│ • Rate limiting + blacklist de tokens   │
└─────────────────────────────────────────┘
```
## 🛠️ Tecnologías

### Backend
| Tecnología | Versión | Propósito |
|-----------|---------|-----------|
| **Python** | 3.12 | Lenguaje principal |
| **FastAPI** | 0.115+ | Framework HTTP asíncrono |
| **SQLModel** | 0.0.24 | ORM + Pydantic integrado |
| **Pydantic** | 2.9+ | Validaciones de datos |
| **bcrypt** | 4.3+ | Hash de contraseñas |
| **redis-py** | 5.0+ | Cliente Redis |
| **slowapi** | 0.1.9+ | Rate limiting |
| **alembic** | 1.13+ | Migraciones de DB |

### Frontend
| Tecnología | Versión | Propósito |
|-----------|---------|-----------|
| **React** | 19 | UI library |
| **TypeScript** | 5 | Tipado estático |
| **Bootstrap 5** | 5.3 | Componentes UI |
| **Vite** | 5 | Build tool + dev server |
| **React Router** | 7 | Navegación SPA |
| **Axios** | 1.16+ | Cliente HTTP |

### Infraestructura
| Tecnología | Propósito |
|-----------|-----------|
| **Docker + Docker Compose** | Contenedores para desarrollo |
| **PostgreSQL 15 + pgvector** | Base de datos relacional + embeddings |
| **Redis 7** | Cache, sesiones y rate limiting |
| **LocalStack** | Emulación de AWS para desarrollo |

## 📁 Estructura del Proyecto

### Backend (`python/`)
```text
tamila-saas-backend/          # Repo: https://github.com/peligro/python-demo-ia
├── 📁 fastapi/
│   ├── main.py               # Entry point + middlewares globales
│   ├── 📁 common/            # Utilidades compartidas
│   │   ├── constants.py      # Constantes: slugs, códigos de items
│   │   └── redis_client.py   # Cliente Redis singleton
│   ├── 📁 database/          # Configuración de DB
│   │   └── database.py       # Conexión SQLModel + engine
│   ├── 📁 middleware/        # Middlewares reutilizables
│   │   ├── auth.py           # Validación de sesión (cookie + Redis)
│   │   ├── rbac.py           # Autorización granular (require_permission)
│   │   ├── security_headers.py # Headers OWASP
│   │   ├── rate_limiter.py   # slowapi + Redis
│   │   └── disable_options.py # Mitiga API B1
│   ├── 📁 models/            # Modelos SQLModel
│   │   ├── user.py, profile.py, module.py, app_menu.py, home_menu.py
│   ├── 📁 schemas/           # Pydantic schemas
│   │   ├── user.py, auth.py, app_menu.py
│   ├── 📁 services/          # Lógica de negocio
│   │   ├── auth/, user/, app_menu/, ...
│   ├── 📁 router/            # Endpoints por módulo
│   │   ├── auth/, user/, app_menu/, ...
│   ├── 📁 alembic/           # Migraciones de DB
│   ├── requirements.txt
│   └── Dockerfile
├── docker-compose.yml        # Orquesta backend + DB + Redis
├── .env.example
├── .gitignore
└── README.md
```
 

### Frontend (react/)

```text
python-demo-ia-react/         # Repo: https://github.com/peligro/python-demo-ia-react
├── src/
│   ├── common/
│   │   ├── api/api.ts        # Instancia axios centralizada
│   │   ├── interfaces/       # Tipos TypeScript
│   │   └── services/         # Servicios API
│   ├── components/
│   │   ├── Sidebar.tsx       # Menús dinámicos con íconos Font Awesome
│   │   ├── Header.tsx
│   │   └── ...
│   ├── context/
│   │   └── AuthContext.tsx   # Estado de autenticación global
│   ├── modules/
│   │   ├── seguridad/        # Login, auth services
│   │   └── admin/            # Paneles administrativos
│   ├── main.tsx
│   └── router.tsx
├── package.json
├── vite.config.ts
├── .env.example
└── README.md
```


## 🚀 Instalación

### Requisitos Previos
- Docker + Docker Compose v2+
- Python 3.12+ (para desarrollo local sin Docker)
- Node.js 18+ y npm (para frontend)


### 1. Clonar ambos repositorios
```bash
# Backend
git clone https://github.com/peligro/python-demo-ia.git
cd python-demo-ia

# Frontend (en paralelo)
git clone https://github.com/peligro/python-demo-ia-react.git
```

### 2. Configurar variables de entorno

### backend
```bash
cd python-demo-ia
cp .env.example .env
# Editar con tus configuraciones: DATABASE_URL, REDIS_HOST, API keys de IA, etc.
```

### frontend
```bash
cd python-demo-ia-react
cp .env.example .env
# Editar VITE_API_URL para apuntar al backend
```

### 3. Levantar servicios con Docker

```bash
# Desde la raíz del repo
cd /home/cesar/Documentos/trabajo/repo
docker-compose up -d --build

# Ver logs
docker-compose logs -f python_service
```

### 4. Acceder a los servicios

| Servicio | URL | Credenciales (dev) |
|----------|-----|-------------------|
| 🌐 API Backend | `http://localhost:8050` | - |
| 📚 Swagger UI | `http://localhost:8050/docs` | - |
| 🐘 PostgreSQL | `localhost:5432` | `laravel` / `secret` |
| 🔴 Redis | `localhost:6379` | - |
| 🗂️ pgAdmin | `http://localhost:5050` | `admin@example.com` / `admin` |


### 5. (Opcional) Desarrollo local sin Docker

```bash
# Backend
cd python/fastapi
pip install -r requirements.txt
uvicorn main:app --host 0.0.0.0 --port 8050 --reload

# Frontend (en otra terminal)
cd python/react
npm install
npm run dev
```

### ⚙️ Variables de Entorno

## ⚙️ Variables de Entorno

### Backend (python/.env)
```env
# Entorno
ENVIRONMENT=local          # local, production
PORT=8050

# Base de datos PostgreSQL
DATABASE_URL=postgresql://laravel:secret@postgres:5432/fastapi

# Redis para sesiones y rate limiting
REDIS_HOST=redis
REDIS_PORT=6379
REDIS_DB=0
SESSION_TTL=86400          # 24 horas en segundos

# Cookies
COOKIE_DOMAIN=
COOKIE_SECURE=false        # true en producción con HTTPS

# Rate limiting
RATE_LIMIT_DEFAULT=120/minute
RATE_LIMIT_STRATEGY=fixed-window

# Frontend para CORS
ALLOWED_ORIGINS=http://localhost:5173,http://127.0.0.1:5173
```

### Frontend (python/react/.env)

```env
VITE_API_URL=http://localhost:8050
VITE_APP_NAME=Tamila SAAS
```
### 🔐 Sistema de Permisos

 


### Conceptos Clave

- **Module**: Recurso del sistema (ej: `/settings/users`)
- **Item**: Acción específica dentro de un módulo (ej: `crear_usuario`)
- **Profile**: Rol que agrupa módulos + items asignados
- **view_all_register**: Item especial que otorga acceso total (llave maestra)

```text
Usuario → UserMetadata → Profile → [ProfileModule] → Module
                                      ↓
                              [ProfileModuleItem] → Item
```

### Flujo de Autorización

```mermaid
graph LR
    A[Request] --> B{AuthMiddleware?}
    B -->|❌ No autenticado | C[401 "No autenticado"]
    B -->|✅ Autenticado | D{require_permission?}
    D -->|❌ Sin permisos | E[401 "No autenticado"]
    D -->|✅ Con permisos | F[Handler]
    F --> G[Response]
```

### Ejemplo: Asignar permisos a un perfil

```bash
# 1. Login para obtener cookie
curl -X POST http://localhost:8050/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@demo.com","password":"SecurePass123!"}' \
  -c cookies.txt

# 2. Asignar módulo "Users" al perfil (ID=1)
curl -X POST http://localhost:8050/profiles/1/modules \
  -b cookies.txt \
  -H "Content-Type: application/json" \
  -d '{"module_id": 1}'
```

>🔍 Nota: Los endpoints protegidos retornan 401 {"estado":"error","mensaje":"No autenticado"} tanto para usuarios no autenticados como para usuarios sin permisos (fail securely).

### 📚 Documentación API


## 📚 Documentación API

### Swagger UI
Accede a la documentación interactiva en:
```text
http://localhost:8050/docs
```

>🔒 En producción (ENVIRONMENT=production), /docs y /redoc no se registran.

## 🛡️ Casos de Seguridad Abordados

### 🔐 Control de Acceso & Autorización
- ✅ Segmentación granular de permisos por perfil (módulos + items)
- ✅ Validación de autorización en cada endpoint (fail securely)
- ✅ Principio de mínimo privilegio aplicado por defecto
- ✅ Llave maestra `view_all_register` para administración total

### 🔑 Gestión de Sesiones & Autenticación
- ✅ Sesiones en Redis con TTL configurable (24h dev / 1h prod)
- ✅ Cookies HttpOnly + Secure + SameSite para protección XSS/CSRF
- ✅ Blacklist de tokens en logout para prevenir reuso
- ✅ Hash de contraseñas con bcrypt (costo adaptable)

### 🌐 Protección de Endpoints & Tráfico
- ✅ Rate limiting por usuario/IP para prevenir abuso de recursos
- ✅ Control de origen con CORS + validación de cookies
- ✅ Restricción de métodos HTTP no necesarios (OPTIONS mitigado)
- ✅ Respuestas genéricas 401 para no divulgar información interna

### 🧱 Headers de Seguridad & Hardening
- ✅ Content-Security-Policy para mitigar inyección de recursos
- ✅ X-Frame-Options: DENY para prevenir clickjacking
- ✅ X-Content-Type-Options: nosniff para evitar MIME sniffing
- ✅ Eliminación de headers `Server` y `X-Powered-By` (info disclosure)
- ✅ Directivas anti-cache: `Cache-Control: no-store`, `Pragma: no-cache`

### 📚 Exposición Controlada de Documentación
- ✅ Swagger/ReDoc solo disponible en entorno de desarrollo
- ✅ Documentación técnica no expuesta en producción

> 💡 **Enfoque**: Todas las medidas siguen prácticas de seguridad por defecto (secure by default) y defensa en profundidad.

## 🚦 Estado del Proyecto

| Módulo | Estado | Notas |
|--------|--------|-------|
| 🔐 Auth + RBAC | ✅ Completado | Cookies HttpOnly + Redis + filtrado por perfil |
| 👥 Users CRUD | ✅ Completado | Paginación, filtros, metadata |
| 📑 App Menu | ✅ Completado | Sidebar dinámico con íconos Font Awesome |
| 🏠 Home Menu | ✅ Completado | Tarjetas para dashboard |
| 🤖 Módulos de IA | 🟨 En planificación | Ver sección dedicada abajo |