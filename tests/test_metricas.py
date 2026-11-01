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

    def test_no_operational_data_is_explicit(self):
        self.assertEqual(metricas.operacion({'periodos': []}), {'estado': 'sin_datos', 'periodos': []})

    def test_rates_keep_their_denominators(self):
        row = metricas.operacion({'periodos': [example()]})['periodos'][0]
        self.assertEqual(row['tasa_entrega'], .75)
        self.assertEqual(row['tasa_ausencias_sobre_clasificados'], .25)
        self.assertEqual(row['cobertura_clasificacion'], .8)

    def test_missing_and_zero_are_not_invented_rates(self):
        for changes in [{'entregados_unicos': None}, {'intentados_unicos': 0, 'entregados_unicos': 0}]:
            row = metricas.operacion({'periodos': [example(**changes)]})['periodos'][0]
            self.assertIsNone(row['tasa_entrega'])
        row = metricas.operacion({'periodos': [example(asistencias=0, ausencias=0)]})['periodos'][0]
        self.assertIsNone(row['tasa_ausencias_sobre_clasificados'])
        self.assertEqual(row['cobertura_clasificacion'], 0)

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


if __name__ == '__main__':
    unittest.main()
