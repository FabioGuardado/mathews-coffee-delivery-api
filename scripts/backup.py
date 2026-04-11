import os
import logging
from datetime import datetime

# Configuración de logging
logging.basicConfig(
    filename="logs/backup.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

# Configuración de backup
CONTAINER = "mongo-clase3"
DB = "mathews_coffee_delivery"
BACKUP_DIR = "backups"

os.makedirs(BACKUP_DIR, exist_ok=True)

timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")

try:
    logging.info("Iniciando backup")

    # Comando para generar el backup dentro del contenedor
    dump_cmd = f"docker exec {CONTAINER} mongodump --db {DB} --out /tmp/{timestamp}"
    # Comando para copiar el backup del contenedor al host
    copy_cmd = f"docker cp {CONTAINER}:/tmp/{timestamp} {BACKUP_DIR}/backup_{timestamp}"

    # Ejecutar comandos
    os.system(dump_cmd)
    logging.info("Backup generado en contenedor")

    os.system(copy_cmd)
    logging.info("Backup copiado al host")

    print(f"Backup creado: {BACKUP_DIR}/backup_{timestamp}")

except Exception as e:
    logging.error(f"Error en backup: {e}")