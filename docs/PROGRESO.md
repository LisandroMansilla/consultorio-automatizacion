# Avances y siguientes pasos

## 07/11/2026

Se hizo explícito por qué una tasa operativa queda en `null`. Cada entrada de `trazabilidad_tasas` ahora declara el estado `calculada`, `datos_incompletos` o `denominador_cero`, además de conservar sus operandos, unidad y valor. Los campos escalares anteriores se mantienen para compatibilidad.

Una regresión nueva distingue datos faltantes de un denominador cero y eleva la suite a dieciocho pruebas. El cambio usa únicamente fixtures sintéticos; las plantillas públicas siguen vacías. No publica muestras históricas, métricas operativas ni datos reales, y no accede al VPS, contenedores o workflows del Consultorio.

## 06/11/2026

Se hizo explícita la trazabilidad de los rangos de recursos: cada resultado de CPU y memoria ahora declara unidad, mínimo, máximo, cantidad de muestras, fecha y fuente en `trazabilidad_metricas`. Los campos escalares anteriores se conservan para compatibilidad.

Una regresión nueva comprueba el contrato completo y eleva la suite a diecisiete pruebas. El cambio usa únicamente un fixture sintético; las plantillas públicas siguen vacías. No publica las muestras históricas ni accede al VPS, contenedores, workflows operativos o datos del Consultorio.

## 05/11/2026

Se hizo explícita la trazabilidad de las tasas operativas: cada resultado ahora declara unidad, numerador y denominador con sus valores, además de conservar los campos escalares anteriores. Cuando falta un contador o el denominador es cero, la tasa sigue siendo `null` y la salida muestra qué operando faltó o valió cero.

Una regresión nueva comprueba los casos incompletos y con denominador cero; la suite suma dieciséis pruebas. El cambio usa exclusivamente fixtures sintéticos y plantillas vacías. No publica métricas operativas ni muestras históricas y no accede al VPS, contenedores, workflows o datos del Consultorio.

## 04/11/2026

Se endureció la lectura de recursos para rechazar CSV malformados y celdas numéricas con espacios externos o caracteres de control que `float()` normalizaba silenciosamente. Dos pruebas de regresión cubren las entradas ambiguas y elevan la suite a quince pruebas.

También se corrigió una afirmación del caso técnico: las muestras históricas de recursos y sus rangos no están publicados en este repositorio. Las plantillas siguen vacías y el cambio no incorpora cifras privadas, no accede al VPS y no modifica el sistema operativo del Consultorio.

## 03/11/2026

Se corrigieron dos ambigüedades del contrato de entrada. Python aceptaba fechas básicas sin guiones y semanas ISO aunque las plantillas usan fechas de calendario `AAAA-MM-DD`; además, una fuente o muestra podía contener saltos de línea, tabulaciones u otros caracteres de control. El calculador ahora exige fechas canónicas e identificadores imprimibles. Dos pruebas de regresión cubren recursos y períodos operativos.

El cambio valida estructura local con datos sintéticos. Las plantillas públicas siguen vacías, no se incorporaron métricas operativas ni muestras históricas y no se accedió al VPS o al sistema del Consultorio.

## 02/11/2026

Se corrigieron dos ambigüedades de entrada reproducibles: un CSV podía repetir un encabezado y conservar solo uno de sus valores, y el lector JSON estándar aceptaba claves repetidas tomando silenciosamente la última. El calculador ahora rechaza ambos casos antes de producir métricas; dos pruebas de regresión cubren los defectos.

La validación sigue siendo local y estructural: no acredita la veracidad de una fuente. Las plantillas públicas continúan vacías, no se publicaron cifras históricas y no se accedió al sistema del Consultorio.

## 01/11/2026

Se corrigió una ambigüedad del contrato de métricas operativas: una fila podía omitir metadatos, contener una fuente con espacios externos o no aportar ningún contador. El calculador ahora exige inicio, fin, corte y fuente inequívoca, y rechaza cohortes sin al menos un contador agregado. Una prueba de regresión cubre esos casos.

El cambio afecta solo la validación local y datos sintéticos de prueba. Las plantillas públicas continúan vacías; no se incorporaron cifras operativas ni se accedió al sistema del Consultorio.

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

