# Avances y siguientes pasos

## 30/10/2026

Se documentó el caso técnico y se definieron indicadores de operación. Se incorporó un calculador local de recursos y contadores agregados, con rechazo de datos inconsistentes y salida explícita para ausencia de datos. Sus pruebas emplean fixtures sintéticos.

Se endureció el contrato CSV de recursos para rechazar muestras sin identificador, espacios externos que fragmenten una serie y filas con columnas adicionales. Una prueba de regresión cubre esas entradas ambiguas; no incorpora datos operativos.

El flujo de GitHub Actions ahora comprueba `SHA256SUMS.txt` antes de ejecutar el calculador, para detectar archivos modificados sin actualizar su registro de integridad.

El trabajo se limita a documentación y cálculo local. No se accedió al VPS, no se cambiaron contenedores o workflows y no se enviaron mensajes.

### Pendientes

1. Revisar y autorizar el dataset agregado que pueda publicarse.
2. Registrar período, fuente y fecha de corte para cada indicador real.
3. Obtener una exportación agregada verificable de entregas y resultados de turnos.
4. Medir una línea de base antes de afirmar ahorro o reducción de ausencias.
