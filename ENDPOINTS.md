# 📌 Endpoints

## 🌐 General

- Health check

  ```http
  GET /
  ```

  **Respuesta:**

  ```json
  { "status": "ok", "service": "Mathews Coffee Delivery API" }
  ```

---

## 🧾 Orders

- Obtener órdenes (con filtros y paginación)

  ```http
  GET /orders
  ```

  **Parámetros:**

  | Parámetro     | Tipo   | Requerido | Descripción                        |
  | ------------- | ------ | --------- | ---------------------------------- |
  | `status`      | string | No        | Filtrar por último estado          |
  | `customer_id` | int    | No        | Filtrar por ID de cliente          |
  | `min_total`   | number | No        | Total mínimo                       |
  | `max_total`   | number | No        | Total máximo                       |
  | `page`        | int    | No        | Página (default: 1, mín: 1)        |
  | `limit`       | int    | No        | Registros por página (default: 10) |

- Obtener órdenes por nombre de conductor

  ```http
  GET /orders/by-driver
  ```

  **Parámetros:**

  | Parámetro     | Tipo   | Requerido | Descripción                        |
  | ------------- | ------ | --------- | ---------------------------------- |
  | `driver_name` | string | Sí        | Búsqueda por nombre o apellido     |
  | `page`        | int    | No        | Página (default: 1, mín: 1)        |
  | `limit`       | int    | No        | Registros por página (default: 10) |

- Obtener una orden por ID

  ```http
  GET /orders/{id}
  ```

  **Parámetros de ruta:**

  | Parámetro | Tipo   | Descripción      |
  | --------- | ------ | ---------------- |
  | `id`      | string | ObjectId de la orden |

- Crear una orden

  ```http
  POST /orders
  ```

  **Cuerpo (JSON):**

  | Campo             | Tipo             | Requerido | Descripción                      |
  | ----------------- | ---------------- | --------- | -------------------------------- |
  | `order_id`        | int              | Sí        | ID numérico de la orden          |
  | `customer_id`     | int              | Sí        | ID numérico del cliente          |
  | `items_summary`   | array            | Sí        | Lista de ítems del pedido        |
  | `timeline`        | array            | No        | Historial de estados             |
  | `driver_id`       | string           | No        | ObjectId del conductor asignado  |
  | `created_at`      | datetime (ISO 8601) | No     | Fecha de creación (auto)         |
  | `delivered_at`    | datetime (ISO 8601) | No     | Fecha de entrega                 |

  **Estructura de `items_summary`:**

  | Campo        | Tipo   | Descripción        |
  | ------------ | ------ | ------------------ |
  | `qty`        | int    | Cantidad           |
  | `name`       | string | Nombre del ítem    |
  | `unit_price` | number | Precio unitario    |

  **Estructura de `timeline`:**

  | Campo    | Tipo             | Descripción                    |
  | -------- | ---------------- | ------------------------------ |
  | `status` | string           | Estado (e.g. `delivered`)      |
  | `ts`     | datetime (ISO 8601) | Timestamp del evento        |
  | `actor`  | string           | Responsable del cambio         |

- Reemplazar una orden

  ```http
  PUT /orders/{id}
  ```

  **Parámetros de ruta:**

  | Parámetro | Tipo   | Descripción          |
  | --------- | ------ | -------------------- |
  | `id`      | string | ObjectId de la orden |

  **Cuerpo:** igual al de `POST /orders`.

- Agregar evento al timeline de una orden

  ```http
  POST /orders/{id}/timeline
  ```

  **Parámetros de ruta:**

  | Parámetro | Tipo   | Descripción          |
  | --------- | ------ | -------------------- |
  | `id`      | string | ObjectId de la orden |

  **Cuerpo (JSON):**

  | Campo    | Tipo             | Requerido | Descripción                    |
  | -------- | ---------------- | --------- | ------------------------------ |
  | `status` | string           | Sí        | Nuevo estado                   |
  | `ts`     | datetime (ISO 8601) | Sí     | Timestamp del evento           |
  | `actor`  | string           | Sí        | Responsable del cambio         |

  > Cuando `status` es `delivered`, elimina el estado live de la orden en Redis y devuelve al driver al pool de disponibles.

- Asignar un conductor a una orden

  ```http
  POST /orders/{id}/assign
  ```

  **Parámetros de ruta:**

  | Parámetro | Tipo   | Descripción          |
  | --------- | ------ | -------------------- |
  | `id`      | string | ObjectId de la orden |

  **Cuerpo (JSON):**

  | Campo       | Tipo   | Requerido | Descripción                     |
  | ----------- | ------ | --------- | ------------------------------- |
  | `driver_id` | string | Sí        | ObjectId del conductor a asignar |

  > Falla con `409 Conflict` si el conductor no está en el pool de disponibles. Al asignar: remueve al driver del pool, lo marca como `busy` en Redis e inicializa el estado live de la orden.

---

## 🚚 Drivers

- Obtener conductores (con filtros y paginación)

  ```http
  GET /drivers
  ```

  **Parámetros:**

  | Parámetro      | Tipo    | Requerido | Descripción                                |
  | -------------- | ------- | --------- | ------------------------------------------ |
  | `name`         | string  | No        | Búsqueda por nombre o apellido             |
  | `active`       | boolean | No        | Filtrar por estado activo                  |
  | `vehicle_type` | string  | No        | Filtrar por tipo de vehículo               |
  | `page`         | int     | No        | Página (default: 1, mín: 1)               |
  | `limit`        | int     | No        | Registros por página (default: 10, máx: 100) |

- Obtener un conductor por ID

  ```http
  GET /drivers/{id}
  ```

  **Parámetros de ruta:**

  | Parámetro | Tipo   | Descripción           |
  | --------- | ------ | --------------------- |
  | `id`      | string | ObjectId del conductor |

- Crear un conductor

  ```http
  POST /drivers
  ```

  **Cuerpo (JSON):**

  | Campo        | Tipo             | Requerido | Descripción              |
  | ------------ | ---------------- | --------- | ------------------------ |
  | `name`       | string           | Sí        | Nombre                   |
  | `lastname`   | string           | Sí        | Apellido                 |
  | `phone`      | string           | Sí        | Teléfono                 |
  | `vehicle`    | object           | Sí        | Datos del vehículo       |
  | `active`     | boolean          | No        | Activo (default: `true`) |
  | `created_at` | datetime (ISO 8601) | No     | Fecha de creación (auto) |

  **Estructura de `vehicle`:**

  | Campo   | Tipo   | Descripción         |
  | ------- | ------ | ------------------- |
  | `type`  | string | Tipo de vehículo    |
  | `plate` | string | Placa del vehículo  |

- Reemplazar un conductor

  ```http
  PUT /drivers/{id}
  ```

  **Parámetros de ruta:**

  | Parámetro | Tipo   | Descripción            |
  | --------- | ------ | ---------------------- |
  | `id`      | string | ObjectId del conductor |

  **Cuerpo:** igual al de `POST /drivers`.

- Activar o desactivar un conductor

  ```http
  PATCH /drivers/{id}/active
  ```

  **Parámetros de ruta:**

  | Parámetro | Tipo   | Descripción            |
  | --------- | ------ | ---------------------- |
  | `id`      | string | ObjectId del conductor |

  **Parámetros de consulta:**

  | Parámetro | Tipo    | Requerido | Descripción                |
  | --------- | ------- | --------- | -------------------------- |
  | `active`  | boolean | Sí        | Nuevo estado del conductor |

---

## 📍 Tracking

- Historial GPS de un conductor por día

  ```http
  GET /drivers/{driver_id}/gps-history
  ```

  **Parámetros de ruta:**

  | Parámetro   | Tipo   | Descripción            |
  | ----------- | ------ | ---------------------- |
  | `driver_id` | string | ObjectId del conductor |

  **Parámetros de consulta:**

  | Parámetro | Tipo   | Requerido | Descripción               |
  | --------- | ------ | --------- | ------------------------- |
  | `date`    | string | Sí        | Fecha en formato `YYYY-MM-DD` |

  **Respuesta:**

  ```json
  {
    "driver_id": "...",
    "date": "2025-05-01",
    "points": [
      { "ts": "2025-05-01T14:00:00", "lat": -0.18, "lng": -78.48, "heading": 90, "speed": 32.5, "order_id": 4502 }
    ]
  }
  ```

  > Consulta la tabla `gps_by_driver` de Cassandra, particionada por `(driver_id, day)`. Devuelve los puntos ordenados por timestamp descendente.

- Trail GPS completo de una orden

  ```http
  GET /orders/{order_id}/gps-trail
  ```

  **Parámetros de ruta:**

  | Parámetro  | Tipo | Descripción              |
  | ---------- | ---- | ------------------------ |
  | `order_id` | int  | ID numérico de la orden  |

  **Respuesta:**

  ```json
  {
    "order_id": 4502,
    "points": [
      { "ts": "2025-05-01T14:00:00", "lat": -0.18, "lng": -78.48, "heading": 90, "speed": 32.5, "driver_id": "..." }
    ]
  }
  ```

  > Consulta la tabla `gps_by_order` de Cassandra, particionada por `order_id`. Devuelve todos los puntos del recorrido ordenados por timestamp descendente.

---

## 🔌 WebSocket

- Conexión persistente del conductor (envío de ubicación)

  ```
  WS /ws/driver/{driver_id}
  ```

  **Parámetros de ruta:**

  | Parámetro   | Tipo   | Descripción            |
  | ----------- | ------ | ---------------------- |
  | `driver_id` | string | ObjectId del conductor |

  **Ciclo de vida:**

  | Evento        | Efecto en el servidor                                                |
  | ------------- | -------------------------------------------------------------------- |
  | `onconnect`   | Valida el driver en MongoDB, escribe `driver:{id}:state` en Redis y lo agrega al Set `available_drivers` |
  | `onmessage`   | Procesa el ping GPS: HSET position, PUBLISH Pub/Sub, XADD Stream    |
  | `ondisconnect`| Remueve del Set `available_drivers` y elimina las keys de estado y posición |

  **Mensaje del driver → servidor (JSON):**

  ```json
  { "order_id": 4502, "lat": -0.18, "lng": -78.48, "heading": 90, "speed": 32.5 }
  ```

  | Campo      | Tipo   | Requerido | Descripción                   |
  | ---------- | ------ | --------- | ----------------------------- |
  | `order_id` | int    | Sí        | ID numérico de la orden activa |
  | `lat`      | number | Sí        | Latitud                        |
  | `lng`      | number | Sí        | Longitud                       |
  | `heading`  | int    | Sí        | Dirección en grados (0–360)    |
  | `speed`    | number | Sí        | Velocidad en km/h              |

  **Respuesta por ping exitoso:**

  ```json
  { "status": "ok", "ts": 1714601234 }
  ```

  **Códigos de cierre:**

  | Código | Motivo                        |
  | ------ | ----------------------------- |
  | `4400` | `driver_id` con formato inválido |
  | `4404` | Driver no encontrado en la BD  |

  > La conexión en sí reemplaza los endpoints `available` y `offline`: conectarse equivale a estar disponible, desconectarse (normal o por caída de red) equivale a quedar offline. Cada ping ejecuta las mismas tres operaciones Redis que antes hacía `POST /location`; el flush a Cassandra sigue ocurriendo cada 30 segundos en background.

- Seguimiento en tiempo real de una orden

  ```
  WS /ws/delivery/{order_id}
  ```

  **Parámetros de ruta:**

  | Parámetro  | Tipo   | Descripción             |
  | ---------- | ------ | ----------------------- |
  | `order_id` | string | ID numérico de la orden |

  **Flujo al conectar:**

  1. El servidor lee `order:{order_id}:state` para obtener el `driver_id` asignado.
  2. Lee `driver:{driver_id}:position` y envía un mensaje `seed` con la posición actual.
  3. A partir de ahí, cada ping GPS del conductor (`POST /location`) hace un `PUBLISH` en Redis que el servidor re-transmite a todos los clientes conectados al mismo `order_id`.

  **Mensajes del servidor → cliente:**

  ```json
  { "type": "seed", "lat": 13.6963066, "lng": -89.1926105, "heading": 90, "speed": 32.5, "ts": 1714601234 }
  ```

  ```json
  { "lat": 13.6963066, "lng": -89.1926105, "heading": 92, "speed": 30.0, "ts": 1714601237 }
  ```

  ```json
  { "type": "ping" }
  ```

  > Si el cliente no envía ningún mensaje en 30 segundos el servidor emite un `ping` de keepalive. Múltiples clientes pueden conectarse al mismo `order_id` simultáneamente (fan-out via Pub/Sub).
