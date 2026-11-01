"""Calculate traceable local metrics; no network, messaging or production access."""
from collections import defaultdict
from datetime import date
from pathlib import Path
import argparse
import csv
import json
import math


def recursos(path):
    groups = defaultdict(list)
    seen = set()
    with Path(path).open(newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        required = {'fecha', 'componente', 'muestra', 'cpu_pct', 'memoria_mib', 'evidencia'}
        if set(reader.fieldnames or []) != required:
            raise ValueError('Columnas de recursos distintas del contrato')
        for row in reader:
            if set(row) != required or any(value is None for value in row.values()):
                raise ValueError('Fila de recursos distinta del contrato')
            identifiers = (row['componente'], row['muestra'], row['evidencia'])
            if any(not value.strip() or value != value.strip() for value in identifiers):
                raise ValueError('Componente, muestra y evidencia deben ser identificadores no vacíos sin espacios externos')
            date.fromisoformat(row['fecha'])
            key = (row['fecha'], row['componente'], row['muestra'])
            if key in seen:
                raise ValueError('Muestra duplicada')
            seen.add(key)
            cpu, memory = float(row['cpu_pct']), float(row['memoria_mib'])
            if not all(math.isfinite(x) and x >= 0 for x in (cpu, memory)):
                raise ValueError('Recurso negativo o no finito')
            groups[(row['fecha'], row['componente'], row['evidencia'])].append((cpu, memory))
    result = []
    for (day, component, source), values in sorted(groups.items()):
        result.append({'fecha': day, 'componente': component, 'evidencia': source,
                       'muestras': len(values),
                       'cpu_pct_min': min(x[0] for x in values),
                       'cpu_pct_max': max(x[0] for x in values),
                       'memoria_mib_min': min(x[1] for x in values),
                       'memoria_mib_max': max(x[1] for x in values)})
    return {'estado': 'muestras_proporcionadas' if result else 'sin_datos', 'componentes': result}


COUNTERS = {'intentados_unicos', 'entregados_unicos', 'asistencias', 'ausencias', 'turnos_vencidos'}


def ratio(numerator, denominator):
    if numerator is None or denominator is None or denominator == 0:
        return None
    return numerator / denominator


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
        start, end, cutoff = (date.fromisoformat(row[k]) for k in ('inicio', 'fin', 'corte'))
        if start >= end or cutoff < end:
            raise ValueError('Período o fecha de corte inválidos')
        cohort = (start, end)
        if cohort in seen:
            raise ValueError('Período duplicado; revisar la exportación')
        seen.add(cohort)
        if (not isinstance(row['fuente'], str) or not row['fuente'].strip()
                or row['fuente'] != row['fuente'].strip()):
            raise ValueError('Fuente agregada requerida sin espacios externos')
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
        results.append({'inicio': row['inicio'], 'fin': row['fin'], 'corte': row['corte'],
                        'fuente': row['fuente'], 'contadores': values,
                        'tasa_entrega': ratio(delivered, attempted),
                        'tasa_ausencias_sobre_clasificados': ratio(absent, classified),
                        'cobertura_clasificacion': ratio(classified, expired)})
    return {'estado': 'datos_agregados_proporcionados' if results else 'sin_datos', 'periodos': results}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('tipo', choices=['recursos', 'operacion'])
    parser.add_argument('archivo', type=Path)
    args = parser.parse_args()
    try:
        result = recursos(args.archivo) if args.tipo == 'recursos' else operacion(json.loads(args.archivo.read_text(encoding='utf-8')))
    except (ValueError, KeyError, TypeError, OSError) as exc:
        parser.error(str(exc))
    print(json.dumps(result, ensure_ascii=False, indent=2, allow_nan=False))


if __name__ == '__main__':
    main()
