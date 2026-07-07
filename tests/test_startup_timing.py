import unittest
from helpers import PerfettoTestCase

class StartupTimingMetricTest(PerfettoTestCase):
    def test_successful_fixed_trace_warm_start(self):
        query = """
        INCLUDE PERFETTO MODULE androidx.benchmark.startup;
        SELECT time_to_initial_display_ms, time_to_full_display_ms 
        FROM androidx_startup_timing 
        WHERE package_name = 'androidx.benchmark.integration.macrobenchmark.target';
        """
        rows = self.run_query('api32_startup_warm.perfetto-trace', query)
        self.assertTrue(len(rows) > 0, "No startup rows returned")
        self.assertAlmostEqualThreshold(float(rows[0]['time_to_initial_display_ms']), 154.636678, msg="Warm Initial Display")
        self.assertAlmostEqualThreshold(float(rows[0]['time_to_full_display_ms']), 659.648153, msg="Warm Full Display")

    def test_successful_fixed_trace_immediate_fully_drawn(self):
        query = """
        INCLUDE PERFETTO MODULE androidx.benchmark.startup;
        SELECT time_to_initial_display_ms, time_to_full_display_ms 
        FROM androidx_startup_timing 
        WHERE package_name = 'androidx.benchmark.macro.test';
        """
        rows = self.run_query('api24_startup_sameproc_immediatefullydrawn.perfetto-trace', query)
        self.assertTrue(len(rows) > 0, "No startup rows returned")
        self.assertAlmostEqualThreshold(float(rows[0]['time_to_initial_display_ms']), 178.58525, msg="Immediate Initial Display")
        self.assertAlmostEqualThreshold(float(rows[0]['time_to_full_display_ms']), 178.58525, msg="Immediate Full Display")

if __name__ == '__main__':
    unittest.main()
