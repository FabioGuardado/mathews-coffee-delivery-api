# ☕ Mathews Coffee Delivery API

API REST desarrollada con **FastAPI** y **MongoDB** para la gestión de pedidos y conductores de una plataforma de delivery de café.

Este proyecto forma parte de la asignatura **Base de Datos NoSQL**, donde se implementan conceptos de:

- Modelado en MongoDB
- Consultas eficientes
- Paginación
- Filtros dinámicos
- Arquitectura backend

## Tabla de Contenidos

- [☕ Mathews Coffee Delivery API](#-mathews-coffee-delivery-api)
  - [Tabla de Contenidos](#tabla-de-contenidos)
  - [🚀 Tecnologías utilizadas](#-tecnologías-utilizadas)
  - [Requisitos](#requisitos)
  - [📁 Estructura del proyecto](#-estructura-del-proyecto)
  - [📦 Instalación del proyecto](#-instalación-del-proyecto)
  - [⚙️ Configuración](#️-configuración)
  - [🌐 Acceso a la API](#-acceso-a-la-api)
  - [📌 Endpoints principales](#-endpoints-principales)
    - [🧾 Orders](#-orders)
    - [🚚 Drivers](#-drivers)
  - [📊 Características implementadas](#-características-implementadas)
  - [🧠 Consideraciones técnicas](#-consideraciones-técnicas)
  - [🎓 Contexto académico](#-contexto-académico)
  - [👨‍💻 Autores](#-autores)

## 🚀 Tecnologías utilizadas

- Python 3.10+
- FastAPI
- MongoDB
- Motor (driver async para MongoDB)
- Docker (opcional para base de datos)

## Requisitos

- Python 3.10 o superior
- Tener `pip` instalado

## 📁 Estructura del proyecto

```text
mathews-coffee-delivery-api
├── app/
│   ├── models/
│   │   ├── driver.py
│   │   └── order.py
│   │
│   ├── routes/
│   │   ├── drivers.py
│   │   └── orders.py
│   │
│   └── database.py
│
├── main.py
├── .env
├── .gitignore
├── LICENSE
├── requirements.txt
└── README.md
```

## 📦 Instalación del proyecto

1. **Clonar repositorio**

   ```bash
   git clone https://github.com/FabioGuardado/mathews-coffee-delivery-api.git
   cd mathews-coffee-delivery-api
   ```

2. **Crear el entorno virtual (`venv`)**

   Desde la raíz del repositorio, crear el entorno virtual con:

   ```bash
   python -m venv .venv
   ```

3. **Activar el entorno virtual**
   - **PowerShell:**

     ```powershell
     .\.venv\Scripts\Activate.ps1
     ```

   - **CMD:**

     ```cmd
     .venv\Scripts\activate.bat
     ```

   - **Bash:**

     ```bash
     source .venv/Scripts/activate
     ```

4. **Instalar las dependencias**
   - Con el entorno activado ejecutar:

     ```powershell
     python -m pip install --upgrade pip
     ```

   - Luego instalar las dependencias definidas en [requirements.txt](requirements.txt):

     ```powershell
     pip install -r requirements.txt
     ```

## ⚙️ Configuración

1. Crear archivo `.env` a partir de [.env.example](.env.example):
   - **Powershell:**

     ```powershell
     copy .env.example .env
     ```

   - **Bash:**

     ```bash
     cp .env.example .env
     ```

2. Completar los valores:

   ```env
   MONGODB_URL=mongodb://localhost:27017
   DB_NAME=mathews_coffee_delivery
   ```

3. Ejecutar la aplicación en modo desarrollo

Utilizar el siguiente comando para ejecutar la aplicación en el entorno local:

```powershell
fastapi dev main.py
```

## 🌐 Acceso a la API

Esto iniciará el servidor de desarrollo y la API quedará disponible en:

- http://127.0.0.1:8000
- Swagger UI: http://127.0.0.1:8000/docs
- ReDoc: http://127.0.0.1:8000/redoc

## 📌 Endpoints principales

### 🧾 Orders

- Obtener órdenes (con filtros y paginación)

  ```http
  GET /orders
  ```

- Parámetros:

  | Parámetro     | Tipo   | Descripción          |
  | ------------- | ------ | -------------------- |
  | `status`      | string | Filtrar por estado   |
  | `customer_id` | string | Filtrar por cliente  |
  | `min_total`   | number | Total mínimo         |
  | `max_total`   | number | Total máximo         |
  | `page`        | int    | Página (default: 1)  |
  | `limit`       | int    | Registros por página |

### 🚚 Drivers

- Obtener conductores

  ```http
  GET /drivers
  ```

- Parámetros:

  | Parámetro | Tipo    | Descripción         |
  | --------- | ------- | ------------------- |
  | `name`    | string  | Búsqueda por nombre |
  | `active`  | boolean | Estado activo       |
  | `page`    | int     | Página              |
  | `limit`   | int     | Registros           |

## 📊 Características implementadas

- [x] API REST con FastAPI
- [x] Conexión a MongoDB
- [x] Filtros dinámicos en endpoints
- [x] Paginación eficiente
- [x] Arquitectura modular
- [x] Uso de variables de entorno

## 🧠 Consideraciones técnicas

- Se utiliza Motor como driver asíncrono para MongoDB
- Los filtros se construyen dinámicamente mediante diccionarios
- La paginación se implementa con skip y limit
- Se retorna metadata de paginación en cada respuesta

## 🎓 Contexto académico

Este proyecto fue desarrollado como parte de la asignatura:

- **Base de Datos II (NoSQL)**
- Universidad Evangélica de El Salvador

## 👨‍💻 Autores

- Fabio Guardado
- Dereck Méndez
- Aldo Landaverde
- Carlos
- Juanjo
