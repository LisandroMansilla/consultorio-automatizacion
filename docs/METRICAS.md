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

Cada período operativo requiere inicio, fin, fecha de corte y una fuente inequívoca, además de al menos un contador agregado. El calculador rechaza una fila sin métricas en vez de clasificarla como datos proporcionados. Los contadores desconocidos dentro de una fila válida pueden conservarse como `null`.

Para recursos, cada fila debe respetar exactamente las seis columnas de la plantilla y usar una fecha de calendario canónica `AAAA-MM-DD`. `componente`, `muestra` y `evidencia` son identificadores imprimibles obligatorios: no admiten espacios externos, saltos de línea, tabulaciones ni otros caracteres de control. Así se evita separar accidentalmente una misma serie o aceptar una muestra sin identidad. El calculador rechaza filas con columnas adicionales o encabezados duplicados, muestras duplicadas, valores negativos o números no finitos.

Los objetos JSON con claves repetidas también se rechazan antes de calcular: no se acepta la elección silenciosa del último valor como evidencia inequívoca. Esta validación comprueba la estructura del archivo, no la veracidad de su fuente.

Las fechas de operación (`inicio`, `fin` y `corte`) usan el mismo formato canónico `AAAA-MM-DD`. Se rechazan formatos alternativos que Python podría interpretar, como fechas básicas sin guiones o semanas ISO, para que la entrada publicada y su período no dependan de una interpretación implícita.

El estado de la sesión de mensajería, la salud de un servicio y la entrega al destinatario son comprobaciones distintas. La validación estructural de un respaldo tampoco acredita por sí sola una restauración completa.
