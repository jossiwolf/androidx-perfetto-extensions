import unittest
from helpers import PerfettoTestCase

class TraceSectionMetricTest(PerfettoTestCase):
    def verify_section(self, trace, pkg, section, first, min_val, max_val, sum_val, count, target_only):
        target_filter = f"AND process_name = '{pkg}'" if target_only else ""
        
        # 1. Test First
        q_first = f"""
        INCLUDE PERFETTO MODULE androidx.benchmark.trace;
        SELECT dur / 1e6 AS dur_ms FROM androidx_trace_slices 
        WHERE name = '{section}' {target_filter} ORDER BY ts ASC LIMIT 1;
        """
        res = self.run_query(trace, q_first)
        self.assertTrue(len(res) > 0, f"No slice found for first {section}")
        self.assertAlmostEqualThreshold(float(res[0]['dur_ms']), first, msg=f"First {section}")

        # 2. Test Aggregations (Min, Max, Sum, Count)
        q_aggs = f"""
        INCLUDE PERFETTO MODULE androidx.benchmark.trace;
        SELECT 
          MIN(dur) / 1e6 AS min_ms,
          MAX(dur) / 1e6 AS max_ms,
          SUM(dur) / 1e6 AS sum_ms,
          COUNT(1) AS count
        FROM androidx_trace_slices 
        WHERE name = '{section}' {target_filter} AND dur != -1;
        """
        res = self.run_query(trace, q_aggs)
        self.assertTrue(len(res) > 0, f"No aggregations found for {section}")
        row = res[0]
        self.assertAlmostEqualThreshold(float(row['min_ms']), min_val, msg=f"Min {section}")
        self.assertAlmostEqualThreshold(float(row['max_ms']), max_val, msg=f"Max {section}")
        self.assertAlmostEqualThreshold(float(row['sum_ms']), sum_val, msg=f"Sum {section}")
        self.assertEqual(int(row['count']), count, f"Count {section}")

    def test_trace_section_metrics(self):
        # ActivityThreadMain
        self.verify_section('api24_startup_cold.perfetto-trace', 'androidx.benchmark.integration.macrobenchmark.target', 
                             'ActivityThreadMain', 12.639, 12.639, 12.639, 12.639, 1, target_only=True)
                             
        # activityStart
        self.verify_section('api24_startup_cold.perfetto-trace', 'androidx.benchmark.integration.macrobenchmark.target', 
                             'activityStart', 81.979, 81.979, 81.979, 81.979, 1, target_only=True)
                             
        # startActivityAndWait
        self.verify_section('api24_startup_cold.perfetto-trace', 'androidx.benchmark.integration.macrobenchmark.test', 
                             'startActivityAndWait', 1110.689, 1110.689, 1110.689, 1110.689, 1, target_only=True)
                             
        # inflate (target only)
        self.verify_section('api24_startup_cold.perfetto-trace', 'androidx.benchmark.integration.macrobenchmark.target', 
                             'inflate', 4.949, 4.588, 10.242, 19.779, 3, target_only=True)
                             
        # inflate (unfiltered)
        self.verify_section('api24_startup_cold.perfetto-trace', '', 
                             'inflate', 13.318, 0.836, 13.318, 43.128, 8, target_only=False)
                             
        # wait (non-terminating filter)
        self.verify_section('api31_startup_cold.perfetto-trace', '', 
                             'wait', 0.00724, 0.001615, 357.761234, 811.865025, 226, target_only=False)

if __name__ == '__main__':
    unittest.main()
