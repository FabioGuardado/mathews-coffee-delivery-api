# Mathews Coffee Delivery API

## Requisitos

- Python 3.10 o superior
- Tener `pip` instalado

## 1. Crear el entorno virtual (`venv`)

Desde la raíz del repositorio, crear el entorno virtual con:

```powershell
python -m venv .venv
```

## 2. Activar el entorno virtual

### PowerShell

```powershell
.\.venv\Scripts\Activate.ps1
```

### CMD

```cmd
.venv\Scripts\activate.bat
```

### Bash:

```bash
source .venv/Scripts/activate
```

## 3. Instalar las dependencias

Con el entorno activado ejecutar:

```powershell
python -m pip install --upgrade pip
```

Luego instalar las dependencias definidas en [requirements.txt](requirements.txt):

```powershell
pip install -r requirements.txt
```

## 4. Configurar variables de entorno

Crear archivo `.env` a partir de [.env.example](.env.example):

### Powershell:

```powershell
copy .env.example .env
```

### Bash:

```bash
cp .env.example .env
```

### Completar los valores:

```env
MONGODB_URL=mongodb://localhost:27017
DB_NAME=mathews_coffee_delivery
```

## 5. Ejecutar la aplicación en modo desarrollo

Utilizar el siguiente comando para ejecutar la aplicación en el entorno local:

```powershell
fastapi dev main.py
```

Esto iniciará el servidor de desarrollo y la API quedará disponible en:

- http://127.0.0.1:8000
- http://127.0.0.1:8000/docs
- http://127.0.0.1:8000/redoc


## Desactivar el entorno virtual

```powershell
deactivate
```
