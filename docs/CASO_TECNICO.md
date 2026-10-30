# Caso técnico: automatización y operación del Consultorio

## Necesidad

Apoyar la gestión de turnos con recordatorios y confirmaciones por WhatsApp mediante servicios integrados en un VPS. El caso muestra trabajo de integración y operación técnica; no afirma resultados clínicos ni una reducción medida de ausencias.

## Trabajo documentado

- Uso de Docker y Compose para organizar n8n, MySQL y WAHA, con persistencia mediante volúmenes.
- Diagnóstico de consumo de recursos y consultas lentas durante una incidencia.
- Revisión de conectividad y del estado del servicio de automatización.
- Comprobación de integridad de un respaldo comprimido y de la respuesta de salud de n8n.
- Revisión de la sesión de WhatsApp después de una recuperación.

La evidencia histórica del diagnóstico registra también un servicio de túnel de acceso. El diagrama del README describe sus responsabilidades y evita divulgar direcciones de infraestructura.

## Aprendizajes que se pueden demostrar

El estado `WORKING` observado en WAHA describe la sesión. Una respuesta de salud de n8n describe ese servicio. Ninguna de las dos respuestas, por sí sola, demuestra que el destinatario haya recibido un recordatorio.

Una prueba de integridad de un archivo comprimido confirma que el archivo puede comprobarse estructuralmente. La restauración completa de la aplicación requiere otro procedimiento y no se presenta como validada a partir de esa prueba.

Los recursos se analizaron a partir de muestras de `docker stats`. Sus rangos se publican con fecha y tamaño de muestra. Los valores permiten documentar el diagnóstico histórico, pero no son un benchmark ni acreditan una optimización posterior.

## Próximas evidencias útiles

1. Exportación mensual de contadores agregados, con definición de cada estado y fecha de corte.
2. Entrega de mensajes confirmada por el proveedor y correlacionada con recordatorios únicos.
3. Resultados de turnos clasificados para calcular ausencias con cobertura conocida.
4. Registro de disponibilidad y, si se busca medir ahorro, una línea de base comparable.

Esos pasos son pendientes de medición; no modifican el sistema operativo desde este repositorio.
