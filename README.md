# Mathews Coffee Delivery API

## Requisitos previos

- Python 3.10 o superior
- Tener `pip` disponible en el sistema

## 1. Crear el entorno virtual (`venv`)

Desde la raíz del repositorio, crea el entorno virtual con:

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

Si usas Git Bash:

```bash
source .venv/Scripts/activate
```

## 3. Instalar las dependencias

Con el entorno activado, instala las dependencias definidas en [requirements.txt](requirements.txt):

```powershell
pip install -r requirements.txt
```

## 4. Ejecutar la aplicación en modo desarrollo

Según la documentación oficial de FastAPI, para desarrollo puedes usar el comando `fastapi dev`. En este proyecto el archivo principal es [main.py](main.py) y la aplicación se expone como `app`, por lo que debes ejecutar:

```powershell
fastapi dev main.py
```

Esto iniciará el servidor de desarrollo y, normalmente, la API quedará disponible en:

- http://127.0.0.1:8000
- http://127.0.0.1:8000/docs
- http://127.0.0.1:8000/redoc

## Flujo completo

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
fastapi dev main.py
```

## Desactivar el entorno virtual

Cuando termines de trabajar:

```powershell
deactivate
```
