# Métricas y evidencia

## Estado de publicación

No se distribuye un dataset operativo en este repositorio. Las plantillas de recursos y contadores están vacías; su ejecución devuelve `sin_datos`. Las pruebas del calculador usan fixtures sintéticos claramente identificados.

Para publicar una medición real se debe registrar período, fuente, fecha de captura, unidades, número de muestras y autorización de divulgación. Una captura puntual no se presenta como promedio diario, p95, disponibilidad sostenida o mejora de rendimiento.

## Reproducir el calculador

```sh
python3 tools/metricas.py recursos metrics/recursos.template.csv
python3 tools/metricas.py operacion metrics/operacion.template.json
python3 -m unittest discover -s tests -v
```

Los contadores de recordatorios, entregas, asistencias y ausencias permanecen sin publicar hasta disponer de una exportación agregada verificable. [MEDICION.md](MEDICION.md) establece cohortes, fórmulas y límites.

El estado de la sesión de mensajería, la salud de un servicio y la entrega al destinatario son comprobaciones distintas. La validación estructural de un respaldo tampoco acredita por sí sola una restauración completa.
