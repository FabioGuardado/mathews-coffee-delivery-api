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

  | Parámetro | Tipo    | Requerido | Descripción           |
  | --------- | ------- | --------- | --------------------- |
  | `active`  | boolean | Sí        | Nuevo estado del conductor |
