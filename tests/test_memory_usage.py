import unittest
from helpers import PerfettoTestCase

class MemoryUsageMetricTest(PerfettoTestCase):
    def test_successful_fixed_trace_memory_usage(self):
        query = """
        INCLUDE PERFETTO MODULE androidx.benchmark.memory;
        SELECT counter_name, max_value_kb 
        FROM androidx_memory_usage 
        WHERE process_name = 'androidx.benchmark.integration.macrobenchmark.target';
        """
        rows = self.run_query('api31_startup_cold.perfetto-trace', query)
        self.assertTrue(len(rows) > 0, "No memory usage rows returned")
        
        metrics = {row['counter_name']: float(row['max_value_kb']) for row in rows}
        self.assertAlmostEqualThreshold(metrics.get('Heap size (KB)', 0.0), 3067.0, msg="Heap Size Max")
        self.assertAlmostEqualThreshold(metrics.get('mem.rss.anon', 0.0), 47260.0, msg="Rss Anon Max")
        self.assertAlmostEqualThreshold(metrics.get('mem.rss.file', 0.0), 67668.0, msg="Rss File Max")

if __name__ == '__main__':
    unittest.main()
