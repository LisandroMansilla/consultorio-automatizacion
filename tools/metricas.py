"""Calculate traceable local metrics; no network, messaging or production access."""
from collections import defaultdict
from datetime import date
from pathlib import Path
import argparse
import csv
import json
import math


def canonical_date(value, field):
    if not isinstance(value, str):
        raise ValueError(f'{field} debe usar AAAA-MM-DD')
    try:
        parsed = date.fromisoformat(value)
    except ValueError as exc:
        raise ValueError(f'{field} debe usar una fecha válida AAAA-MM-DD') from exc
    if value != parsed.isoformat():
        raise ValueError(f'{field} debe usar el formato canónico AAAA-MM-DD')
    return parsed


def identifier(value, field):
    if (not isinstance(value, str) or not value.strip() or value != value.strip()
            or not value.isprintable()):
        raise ValueError(f'{field} debe ser un identificador imprimible no vacío sin espacios externos')
    return value


def resource_number(value, field):
    if (not isinstance(value, str) or not value or value != value.strip()
            or not value.isprintable()):
        raise ValueError(f'{field} debe ser un número imprimible sin espacios externos')
    try:
        number = float(value)
    except ValueError as exc:
        raise ValueError(f'{field} debe ser un número no negativo') from exc
    if not math.isfinite(number) or number < 0:
        raise ValueError(f'{field} debe ser un número finito no negativo')
    return number


def traced_range(unit, minimum, maximum, samples, day, source):
    """Describe a resource range without detaching it from its evidence."""
    return {
        'unidad': unit,
        'minimo': minimum,
        'maximo': maximum,
        'muestras': samples,
        'fecha': day,
        'fuente': source,
    }


def recursos(path):
    groups = defaultdict(list)
    seen = set()
    try:
        with Path(path).open(newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f, strict=True)
            rows = list(reader)
            fieldnames = reader.fieldnames or []
    except csv.Error as exc:
        raise ValueError('CSV de recursos malformado') from exc
    required = {'fecha', 'componente', 'muestra', 'cpu_pct', 'memoria_mib', 'evidencia'}
    if len(fieldnames) != len(required) or set(fieldnames) != required:
        raise ValueError('Columnas de recursos distintas o duplicadas respecto del contrato')
    for row in rows:
        if set(row) != required or any(value is None for value in row.values()):
            raise ValueError('Fila de recursos distinta del contrato')
        for field in ('componente', 'muestra', 'evidencia'):
            identifier(row[field], field)
        canonical_date(row['fecha'], 'fecha')
        key = (row['fecha'], row['componente'], row['muestra'])
        if key in seen:
            raise ValueError('Muestra duplicada')
        seen.add(key)
        cpu = resource_number(row['cpu_pct'], 'cpu_pct')
        memory = resource_number(row['memoria_mib'], 'memoria_mib')
        groups[(row['fecha'], row['componente'], row['evidencia'])].append((cpu, memory))
    result = []
    for (day, component, source), values in sorted(groups.items()):
        samples = len(values)
        cpu_min, cpu_max = min(x[0] for x in values), max(x[0] for x in values)
        memory_min, memory_max = min(x[1] for x in values), max(x[1] for x in values)
        result.append({
            'fecha': day,
            'componente': component,
            'evidencia': source,
            'muestras': samples,
            'cpu_pct_min': cpu_min,
            'cpu_pct_max': cpu_max,
            'memoria_mib_min': memory_min,
            'memoria_mib_max': memory_max,
            'trazabilidad_metricas': {
                'cpu': traced_range(
                    'porcentaje_reportado', cpu_min, cpu_max, samples, day, source),
                'memoria': traced_range(
                    'MiB', memory_min, memory_max, samples, day, source),
            },
        })
    return {'estado': 'muestras_proporcionadas' if result else 'sin_datos', 'componentes': result}


COUNTERS = {'intentados_unicos', 'entregados_unicos', 'asistencias', 'ausencias', 'turnos_vencidos'}


def ratio(numerator, denominator):
    if numerator is None or denominator is None or denominator == 0:
        return None
    return numerator / denominator


def traced_ratio(numerator_name, numerator, denominator_name, denominator):
    """Keep a rate tied to the exact counters used to calculate it."""
    value = ratio(numerator, denominator)
    if value is not None:
        status = 'calculada'
    elif denominator == 0:
        status = 'denominador_cero'
    else:
        status = 'datos_incompletos'
    return {
        'valor': value,
        'estado': status,
        'unidad': 'proporcion_0_a_1',
        'numerador': {'campo': numerator_name, 'valor': numerator},
        'denominador': {'campo': denominator_name, 'valor': denominator},
    }


def object_without_duplicates(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f'Clave JSON duplicada: {key}')
        result[key] = value
    return result


def cargar_json(path):
    return json.loads(Path(path).read_text(encoding='utf-8'),
                      object_pairs_hook=object_without_duplicates)


def operacion(payload):
    if not isinstance(payload, dict) or set(payload) != {'periodos'} or not isinstance(payload['periodos'], list):
        raise ValueError('Se requiere un objeto con la lista periodos')
    results, seen = [], set()
    for row in payload['periodos']:
        metadata = {'inicio', 'fin', 'corte', 'fuente'}
        allowed = COUNTERS | metadata
        if (not isinstance(row, dict) or not metadata.issubset(row)
                or not set(row).issubset(allowed)):
            raise ValueError('Metadatos obligatorios ausentes o campos ajenos al contrato agregado')
        start, end, cutoff = (canonical_date(row[k], k) for k in ('inicio', 'fin', 'corte'))
        if start >= end or cutoff < end:
            raise ValueError('Período o fecha de corte inválidos')
        cohort = (start, end)
        if cohort in seen:
            raise ValueError('Período duplicado; revisar la exportación')
        seen.add(cohort)
        identifier(row['fuente'], 'fuente')
        values = {key: row.get(key) for key in COUNTERS}
        if all(value is None for value in values.values()):
            raise ValueError('Se requiere al menos un contador agregado')
        if any(v is not None and (type(v) is not int or v < 0) for v in values.values()):
            raise ValueError('Los contadores deben ser enteros no negativos o null')
        attempted, delivered = values['intentados_unicos'], values['entregados_unicos']
        present, absent, expired = values['asistencias'], values['ausencias'], values['turnos_vencidos']
        if attempted is not None and delivered is not None and delivered > attempted:
            raise ValueError('Entregados supera intentados de la misma cohorte')
        known_results = sum(v for v in (present, absent) if v is not None)
        if expired is not None and known_results > expired:
            raise ValueError('Resultados clasificados superan turnos vencidos')
        classified = present + absent if present is not None and absent is not None else None
        traced_rates = {
            'tasa_entrega': traced_ratio(
                'entregados_unicos', delivered, 'intentados_unicos', attempted),
            'tasa_ausencias_sobre_clasificados': traced_ratio(
                'ausencias', absent, 'asistencias + ausencias', classified),
            'cobertura_clasificacion': traced_ratio(
                'asistencias + ausencias', classified, 'turnos_vencidos', expired),
        }
        results.append({'inicio': row['inicio'], 'fin': row['fin'], 'corte': row['corte'],
                        'fuente': row['fuente'], 'contadores': values,
                        'tasa_entrega': ratio(delivered, attempted),
                        'tasa_ausencias_sobre_clasificados': ratio(absent, classified),
                        'cobertura_clasificacion': ratio(classified, expired),
                        'trazabilidad_tasas': traced_rates})
    return {'estado': 'datos_agregados_proporcionados' if results else 'sin_datos', 'periodos': results}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('tipo', choices=['recursos', 'operacion'])
    parser.add_argument('archivo', type=Path)
    args = parser.parse_args()
    try:
        result = recursos(args.archivo) if args.tipo == 'recursos' else operacion(cargar_json(args.archivo))
    except (ValueError, KeyError, TypeError, OSError) as exc:
        parser.error(str(exc))
    print(json.dumps(result, ensure_ascii=False, indent=2, allow_nan=False))


if __name__ == '__main__':
    main()

