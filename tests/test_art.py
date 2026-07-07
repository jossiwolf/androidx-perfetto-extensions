import unittest
from helpers import PerfettoTestCase

class ArtMetricTest(PerfettoTestCase):
    def test_successful_fixed_trace_art_metrics(self):
        query = """
        INCLUDE PERFETTO MODULE androidx.benchmark.art;
        SELECT jit_sum_ms, jit_count, verify_class_sum_ms, verify_class_count, class_load_sum_ms, class_load_count 
        FROM androidx_art_metrics 
        WHERE process_name = 'androidx.compose.integration.hero.macrobenchmark.target';
        """
        rows = self.run_query('api35_startup_cold_classinit.perfetto-trace', query)
        self.assertTrue(len(rows) > 0, "No ART rows returned")
        row = rows[0]
        
        self.assertAlmostEqualThreshold(float(row['jit_sum_ms']), 433.488508, threshold=0.001, msg="JIT Sum")
        self.assertAlmostEqualThreshold(float(row['jit_count']), 177, threshold=0.001, msg="JIT Count")
        self.assertAlmostEqualThreshold(float(row['verify_class_sum_ms']), 0.0, threshold=0.001, msg="Verify Class Sum")
        self.assertAlmostEqualThreshold(float(row['verify_class_count']), 0, threshold=0.001, msg="Verify Class Count")
        self.assertAlmostEqualThreshold(float(row['class_load_sum_ms']), 147.052337, threshold=0.001, msg="Class Load Sum")
        self.assertAlmostEqualThreshold(float(row['class_load_count']), 2013, threshold=0.001, msg="Class Load Count")

if __name__ == '__main__':
    unittest.main()
