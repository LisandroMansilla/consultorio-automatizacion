"""Tests of this metric calculator; fixtures are not operational clinic results."""
from pathlib import Path
import importlib.util
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('metricas', ROOT / 'tools/metricas.py')
metricas = importlib.util.module_from_spec(spec)
spec.loader.exec_module(metricas)


def example(**changes):
    # Synthetic counters used only to exercise formulas and rejection behavior.
    return {'inicio': '2026-01-01', 'fin': '2026-02-01', 'corte': '2026-02-02',
            'fuente': 'FIXTURE_SINTETICO', 'intentados_unicos': 4, 'entregados_unicos': 3,
            'asistencias': 3, 'ausencias': 1, 'turnos_vencidos': 5, **changes}


class MetricTests(unittest.TestCase):
    def test_resource_ranges_from_synthetic_rows(self):
        header = 'fecha,componente,muestra,cpu_pct,memoria_mib,evidencia\n'
        body = ('2000-01-01,n8n,1,1,10,FIXTURE_SINTETICO\n'
                '2000-01-01,n8n,2,3,20,FIXTURE_SINTETICO\n')
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / 'synthetic.csv'; p.write_text(header + body)
            result = metricas.recursos(p)
        row = result['componentes'][0]
        self.assertEqual(row['muestras'], 2)
        self.assertEqual((row['memoria_mib_min'], row['memoria_mib_max']), (10, 20))
        self.assertEqual((row['cpu_pct_min'], row['cpu_pct_max']), (1, 3))

    def test_resource_ranges_declare_units_samples_date_and_source(self):
        header = 'fecha,componente,muestra,cpu_pct,memoria_mib,evidencia\n'
        body = ('2000-01-01,n8n,1,1,10,FIXTURE_SINTETICO\n'
                '2000-01-01,n8n,2,3,20,FIXTURE_SINTETICO\n')
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / 'synthetic.csv'; p.write_text(header + body)
            row = metricas.recursos(p)['componentes'][0]

        trace = row['trazabilidad_metricas']
        self.assertEqual(trace['cpu'], {
            'unidad': 'porcentaje_reportado',
            'minimo': 1,
            'maximo': 3,
            'muestras': 2,
            'fecha': '2000-01-01',
            'fuente': 'FIXTURE_SINTETICO',
        })
        self.assertEqual(trace['memoria'], {
            'unidad': 'MiB',
            'minimo': 10,
            'maximo': 20,
            'muestras': 2,
            'fecha': '2000-01-01',
            'fuente': 'FIXTURE_SINTETICO',
        })

    def test_no_operational_data_is_explicit(self):
        self.assertEqual(metricas.operacion({'periodos': []}), {'estado': 'sin_datos', 'periodos': []})

    def test_rates_keep_their_denominators(self):
        row = metricas.operacion({'periodos': [example()]})['periodos'][0]
        self.assertEqual(row['tasa_entrega'], .75)
        self.assertEqual(row['tasa_ausencias_sobre_clasificados'], .25)
        self.assertEqual(row['cobertura_clasificacion'], .8)

        trace = row['trazabilidad_tasas']
        self.assertEqual(trace['tasa_entrega'], {
            'valor': .75,
            'unidad': 'proporcion_0_a_1',
            'numerador': {'campo': 'entregados_unicos', 'valor': 3},
            'denominador': {'campo': 'intentados_unicos', 'valor': 4},
        })
        self.assertEqual(
            trace['tasa_ausencias_sobre_clasificados']['denominador'],
            {'campo': 'asistencias + ausencias', 'valor': 4})
        self.assertEqual(
            trace['cobertura_clasificacion']['numerador'],
            {'campo': 'asistencias + ausencias', 'valor': 4})

    def test_missing_and_zero_are_not_invented_rates(self):
        for changes in [{'entregados_unicos': None}, {'intentados_unicos': 0, 'entregados_unicos': 0}]:
            row = metricas.operacion({'periodos': [example(**changes)]})['periodos'][0]
            self.assertIsNone(row['tasa_entrega'])
        row = metricas.operacion({'periodos': [example(asistencias=0, ausencias=0)]})['periodos'][0]
        self.assertIsNone(row['tasa_ausencias_sobre_clasificados'])
        self.assertEqual(row['cobertura_clasificacion'], 0)

    def test_rate_trace_preserves_missing_and_zero_denominators(self):
        missing = metricas.operacion({'periodos': [example(entregados_unicos=None)]})['periodos'][0]
        delivery = missing['trazabilidad_tasas']['tasa_entrega']
        self.assertIsNone(delivery['valor'])
        self.assertEqual(delivery['numerador']['valor'], None)
        self.assertEqual(delivery['denominador']['valor'], 4)

        zero = metricas.operacion({
            'periodos': [example(intentados_unicos=0, entregados_unicos=0)]
        })['periodos'][0]['trazabilidad_tasas']['tasa_entrega']
        self.assertIsNone(zero['valor'])
        self.assertEqual(zero['denominador'], {'campo': 'intentados_unicos', 'valor': 0})

    def test_inconsistent_counts_are_rejected(self):
        for changes in [{'entregados_unicos': 5}, {'asistencias': 6, 'ausencias': None},
                        {'turnos_vencidos': 3}, {'intentados_unicos': -1}, {'ausencias': True}]:
            with self.subTest(changes=changes), self.assertRaises(ValueError):
                metricas.operacion({'periodos': [example(**changes)]})

    def test_dates_duplicates_and_unrelated_fields_are_rejected(self):
        for payload in [{'periodos': [example(corte='2026-01-20')]},
                        {'periodos': [example(fin='2026-01-01')]},
                        {'periodos': [example(), example()]},
                        {'periodos': [example(paciente='NO_ADMITIDO')]}]:
            with self.subTest(payload=payload), self.assertRaises(ValueError):
                metricas.operacion(payload)

    def test_operational_period_requires_metadata_and_one_counter(self):
        without_cutoff = example()
        without_cutoff.pop('corte')
        no_counters = example(**{key: None for key in metricas.COUNTERS})
        for row in [without_cutoff, example(fuente=' FIXTURE_SINTETICO'),
                    example(fuente='FIXTURE_SINTETICO '), no_counters]:
            with self.subTest(row=row), self.assertRaises(ValueError):
                metricas.operacion({'periodos': [row]})

    def test_non_finite_or_repeated_resource_sample_is_rejected(self):
        header = 'fecha,componente,muestra,cpu_pct,memoria_mib,evidencia\n'
        for body in ['2000-01-01,n8n,1,nan,10,FIXTURE_SINTETICO\n',
                     '2000-01-01,n8n,1,1,10,FIXTURE_SINTETICO\n2000-01-01,n8n,1,2,20,FIXTURE_SINTETICO\n']:
            with tempfile.TemporaryDirectory() as d:
                p = Path(d) / 'test.csv'; p.write_text(header + body)
                with self.assertRaises(ValueError):
                    metricas.recursos(p)

    def test_resource_rows_require_unambiguous_identifiers_and_shape(self):
        header = 'fecha,componente,muestra,cpu_pct,memoria_mib,evidencia\n'
        invalid_rows = [
            '2000-01-01,n8n,,1,10,FIXTURE_SINTETICO\n',
            '2000-01-01, n8n,1,1,10,FIXTURE_SINTETICO\n',
            '2000-01-01,n8n,1,1,10,   \n',
            '2000-01-01,n8n,1,1,10,FIXTURE_SINTETICO,COLUMNA_EXTRA\n',
        ]
        for body in invalid_rows:
            with self.subTest(body=body), tempfile.TemporaryDirectory() as d:
                p = Path(d) / 'test.csv'; p.write_text(header + body)
                with self.assertRaises(ValueError):
                    metricas.recursos(p)

    def test_duplicate_csv_header_is_rejected(self):
        text = ('fecha,componente,muestra,cpu_pct,memoria_mib,evidencia,cpu_pct\n'
                '2000-01-01,n8n,1,1,10,FIXTURE_SINTETICO,99\n')
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / 'duplicate-header.csv'; p.write_text(text)
            with self.assertRaisesRegex(ValueError, 'duplicadas'):
                metricas.recursos(p)

    def test_duplicate_json_key_is_rejected(self):
        text = ('{"periodos":[{"inicio":"2026-01-01","fin":"2026-02-01",'
                '"corte":"2026-02-02","fuente":"FIXTURE_SINTETICO",'
                '"intentados_unicos":4,"intentados_unicos":400}]}')
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / 'duplicate-key.json'; p.write_text(text)
            with self.assertRaisesRegex(ValueError, 'intentados_unicos'):
                metricas.cargar_json(p)

    def test_dates_require_canonical_calendar_format(self):
        for field, value in [('inicio', '20260101'), ('inicio', '2026-W01-1'),
                             ('fin', '2026-02-01T00:00:00'), ('corte', 20260202)]:
            with self.subTest(field=field, value=value), self.assertRaisesRegex(ValueError, 'AAAA-MM-DD'):
                metricas.operacion({'periodos': [example(**{field: value})]})
        header = 'fecha,componente,muestra,cpu_pct,memoria_mib,evidencia\n'
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / 'non-canonical.csv'
            p.write_text(header + '20000101,n8n,1,1,10,FIXTURE_SINTETICO\n')
            with self.assertRaisesRegex(ValueError, 'AAAA-MM-DD'):
                metricas.recursos(p)

    def test_identifiers_reject_control_characters(self):
        for source in ['FIXTURE\\nOTRA', 'FIXTURE\\tOTRA', 'FIXTURE\\x00OTRA']:
            decoded = source.encode().decode('unicode_escape')
            with self.subTest(source=source), self.assertRaisesRegex(ValueError, 'imprimible'):
                metricas.operacion({'periodos': [example(fuente=decoded)]})
        header = 'fecha,componente,muestra,cpu_pct,memoria_mib,evidencia\n'
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / 'control.csv'
            p.write_text(header + '2000-01-01,n8n,"muestra\npartida",1,10,FIXTURE_SINTETICO\n')
            with self.assertRaisesRegex(ValueError, 'imprimible'):
                metricas.recursos(p)

    def test_resource_numbers_reject_external_spaces_and_controls(self):
        header = 'fecha,componente,muestra,cpu_pct,memoria_mib,evidencia\n'
        invalid_rows = [
            '2000-01-01,n8n,1," 1",10,FIXTURE_SINTETICO\n',
            '2000-01-01,n8n,1,1,"10 ",FIXTURE_SINTETICO\n',
            '2000-01-01,n8n,1,"1\n",10,FIXTURE_SINTETICO\n',
        ]
        for body in invalid_rows:
            with self.subTest(body=body), tempfile.TemporaryDirectory() as d:
                p = Path(d) / 'ambiguous-number.csv'; p.write_text(header + body)
                with self.assertRaisesRegex(ValueError, 'sin espacios externos'):
                    metricas.recursos(p)

    def test_malformed_resource_csv_is_rejected(self):
        text = ('fecha,componente,muestra,cpu_pct,memoria_mib,evidencia\n'
                '2000-01-01,n8n,1,"1,10,FIXTURE_SINTETICO\n')
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / 'malformed.csv'; p.write_text(text)
            with self.assertRaisesRegex(ValueError, 'malformado'):
                metricas.recursos(p)


if __name__ == '__main__':
    unittest.main()

