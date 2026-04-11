import os
import logging

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Rutas
BACKUP_DIR = os.path.join(BASE_DIR, "backups")
LOG_DIR = os.path.join(BASE_DIR, "logs")
LOG_FILE = os.path.join(LOG_DIR, "restore.log")

# Crear carpeta logs si no existe
os.makedirs(LOG_DIR, exist_ok=True)

# Configurar logging
logging.basicConfig(
    filename=LOG_FILE,
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

CONTAINER = "mongos"  # Router del sharded cluster

def listar_backups():
    backups = os.listdir(BACKUP_DIR)
    backups.sort(reverse=True)
    return backups

def restaurar_backup():
    try:
        logging.info("Iniciando proceso de restauración")

        backups = listar_backups()

        if not backups:
            print("No hay backups disponibles")
            logging.warning("No se encontraron backups")
            return

        print("\nBackups disponibles:\n")
        for i, backup in enumerate(backups):
            print(f"{i + 1}. {backup}")

        opcion = int(input("\nSelecciona el número del backup a restaurar: "))
        selected_backup = backups[opcion - 1]

        backup_path_host = os.path.join(BACKUP_DIR, selected_backup)
        backup_path_container = f"/tmp/{selected_backup}"

        print("\nCopiando backup al contenedor...")
        os.system(f'docker cp "{backup_path_host}" {CONTAINER}:{backup_path_container}')
        logging.info(f"Backup copiado: {selected_backup}")

        print("Restaurando base de datos...")
        os.system(f'docker exec {CONTAINER} mongorestore --host mongos:27017 {backup_path_container}')
        logging.info(f"Backup restaurado: {selected_backup}")

        print("Restauración completada")

    except Exception as e:
        logging.error(f"Error en restauración: {e}")
        print(f"Error: {e}")

if __name__ == "__main__":
    restaurar_backup()