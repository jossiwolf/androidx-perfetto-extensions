import unittest
from helpers import PerfettoTestCase

class FrameTimingMetricTest(PerfettoTestCase):
    def test_successful_fixed_trace_frame_timing(self):
        query = """
        INCLUDE PERFETTO MODULE androidx.benchmark.frame;
        SELECT frame_id, cpu_duration_ms, frame_overrun_ms 
        FROM androidx_frame_timing 
        WHERE process_name = 'androidx.benchmark.integration.macrobenchmark.target' 
        ORDER BY frame_id;
        """
        rows = self.run_query('api31_scroll.perfetto-trace', query)
        
        # Assert total frames
        self.assertEqual(len(rows), 98, "Frame count mismatch")
            
        # Assert first 10 CPU durations and overruns
        expected_cpu = [6.881407, 5.648542, 3.830261, 4.343438, 4.820522, 11.301147, 4.205469, 4.076615, 4.973699, 4.408334]
        expected_overrun = [-5.207137, -11.699862, -14.025295, -12.300155, -11.944858, -8.354770, -9.73489, -10.849726, -11.046253, -10.997936]
        
        for i in range(10):
            row = rows[i]
            self.assertAlmostEqualThreshold(float(row['cpu_duration_ms']), expected_cpu[i], msg=f"Frame {i} CPU")
            self.assertAlmostEqualThreshold(float(row['frame_overrun_ms']), expected_overrun[i], msg=f"Frame {i} Overrun")

if __name__ == '__main__':
    unittest.main()
