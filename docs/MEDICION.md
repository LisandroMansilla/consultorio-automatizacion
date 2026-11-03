# Protocolo para métricas de operación

## Unidad y período

Trabajar con exportaciones agregadas por período. Para una cohorte de recordatorios, contar identificadores únicos cuyo primer intento se produjo dentro de `[inicio, fin)`. Aplicar la misma cohorte al contar entregas y registrar la fecha de corte: una entrega puede confirmarse después del primer intento.

Un reintento no crea otro recordatorio único. Una ejecución exitosa de n8n o una respuesta HTTP de aceptación de WAHA no se cuenta como entrega al destinatario. El total entregado requiere el estado de entrega confirmado y su correlación con la cohorte.

## Contrato de entrada

El comando `operacion` acepta un objeto con `periodos`, una lista. Cada entrada contiene:

| Campo | Definición |
|---|---|
| `inicio`, `fin` | Fechas de calendario en formato canónico `AAAA-MM-DD`; inicio incluido y fin excluido. |
| `corte` | Fecha de captura en formato canónico `AAAA-MM-DD`, igual o posterior al fin. |
| `fuente` | Referencia de la exportación agregada, sin credenciales ni contactos. |
| `intentados_unicos` | Recordatorios únicos de la cohorte. Entero o `null`. |
| `entregados_unicos` | Entregas confirmadas de esa misma cohorte. Entero o `null`. |
| `asistencias` | Turnos vencidos con asistencia confirmada. Entero o `null`. |
| `ausencias` | Turnos vencidos con ausencia confirmada. Entero o `null`. |
| `turnos_vencidos` | Total de turnos de esa cohorte cuyo horario ya pasó. Entero o `null`. |

Los contadores de turnos deben usar la misma cohorte entre sí; no necesitan confundirse con la cohorte de mensajes. No incluir información de pacientes en los archivos de este repositorio. El ejemplo distribuido es una lista vacía, sin datos operativos inventados.

Los cuatro metadatos (`inicio`, `fin`, `corte` y `fuente`) son obligatorios. `fuente` debe ser un identificador imprimible, no vacío y sin espacios externos; no admite saltos de línea, tabulaciones ni otros caracteres de control. Cada período debe aportar al menos uno de los cinco contadores; una fila compuesta solo por metadatos no se presenta como datos agregados.

## Fórmulas y datos incompletos

- Tasa de entrega: `entregados_unicos / intentados_unicos`, con denominador positivo y ambos valores confirmados.
- Tasa de ausencias entre resultados clasificados: `ausencias / (asistencias + ausencias)`, con ambos resultados confirmados y denominador positivo.
- Cobertura de clasificación: `(asistencias + ausencias) / turnos_vencidos`, cuando los tres valores están disponibles y el total es positivo.

Los campos faltantes y los denominadores cero producen `null`, no una tasa de 0 %. El verificador rechaza contadores negativos, booleanos, entregas superiores a intentos y resultados clasificados superiores al total de turnos vencidos.

## Comparaciones de impacto

Para afirmar una reducción de ausencias se necesitan al menos una línea de base y un período posterior comparables, con la misma definición, cobertura y población. Registrar también cambios de agenda o proceso que puedan afectar la comparación. Una diferencia observada por sí sola no demuestra causalidad.

El tiempo ahorrado requiere una medición del proceso manual y del proceso automatizado sobre una cantidad conocida de casos. No se deriva de contar workflows ni mensajes.
