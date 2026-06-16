# Analysis: IoT Ingestion Service Roles

- **Role:** Data Provider & Publisher.
- **Upstream:** Subscribe raw sensor data from MQTT topic `smart-campus/raw/iot/environment` (simulated by Pi IoT).
- **Downstream:** Validate, normalize, and publish processed sensor events to `smart-campus/events/sensor`.
- **Consumers:** Core Business (A6) and Analytics (A5).
