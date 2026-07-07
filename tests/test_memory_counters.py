import unittest
from helpers import PerfettoTestCase

class MemoryCountersMetricTest(PerfettoTestCase):
    def test_successful_fixed_trace_memory_counters(self):
        query = """
        INCLUDE PERFETTO MODULE androidx.benchmark.memory;
        SELECT counter_name, total_count 
        FROM androidx_memory_counters 
        WHERE process_name = 'androidx.benchmark.integration.macrobenchmark.target';
        """
        rows = self.run_query('api31_startup_cold.perfetto-trace', query)
        self.assertTrue(len(rows) > 0, "No memory counters rows returned")
        
        metrics = {row['counter_name']: float(row['total_count']) for row in rows}
        self.assertAlmostEqualThreshold(metrics.get('mem.mm.min_flt.count', 0.0), 3431.0, msg="Minor Page Faults")
        self.assertAlmostEqualThreshold(metrics.get('mem.mm.maj_flt.count', 0.0), 6.0, msg="Major Page Faults")
        self.assertAlmostEqualThreshold(metrics.get('mem.mm.swp_flt.count', 0.0), 0.0, msg="Page Faults Backed by Swap Cache")
        self.assertAlmostEqualThreshold(metrics.get('mem.mm.read_io.count', 0.0), 8.0, msg="Page Faults Backed by Read IO")

if __name__ == '__main__':
    unittest.main()
