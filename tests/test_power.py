import unittest
from helpers import PerfettoTestCase

class PowerMetricTest(PerfettoTestCase):
    def test_successful_fixed_trace_energy_breakdown(self):
        query = """
        INCLUDE PERFETTO MODULE androidx.benchmark.power;
        SELECT metric_name, value FROM androidx_power_output;
        """
        rows = self.run_query('api32_odpm_rails.perfetto-trace', query)
        self.assertTrue(len(rows) > 0, "No power rows returned")
        
        metrics = {row['metric_name']: float(row['value']) for row in rows}
        
        # Check energy component breakdown (threshold = 0.1)
        self.assertAlmostEqualThreshold(metrics.get('energyComponentCpuBigUws', 0.0), 31935.0, threshold=0.1, msg="energyComponentCpuBigUws")
        self.assertAlmostEqualThreshold(metrics.get('energyComponentCpuLittleUws', 0.0), 303264.0, threshold=0.1, msg="energyComponentCpuLittleUws")
        self.assertAlmostEqualThreshold(metrics.get('energyComponentCpuMidUws', 0.0), 55179.0, threshold=0.1, msg="energyComponentCpuMidUws")
        self.assertAlmostEqualThreshold(metrics.get('energyComponentDisplayUws', 0.0), 1006934.0, threshold=0.1, msg="energyComponentDisplayUws")
        self.assertAlmostEqualThreshold(metrics.get('energyComponentGpuUws', 0.0), 66555.0, threshold=0.1, msg="energyComponentGpuUws")
        self.assertAlmostEqualThreshold(metrics.get('energyTotalUws', 0.0), 2589658.0, threshold=0.1, msg="energyTotalUws")

    def test_successful_fixed_trace_power_total(self):
        query = """
        INCLUDE PERFETTO MODULE androidx.benchmark.power;
        SELECT metric_name, value FROM androidx_power_output;
        """
        rows = self.run_query('api32_odpm_rails.perfetto-trace', query)
        self.assertTrue(len(rows) > 0, "No power rows returned")
        
        metrics = {row['metric_name']: float(row['value']) for row in rows}
        
        # Check power category totals (threshold = 0.00001)
        self.assertAlmostEqualThreshold(metrics.get('powerCategoryCpuUw', 0.0), 80.94090814845532, threshold=0.00001, msg="powerCategoryCpuUw")
        self.assertAlmostEqualThreshold(metrics.get('powerCategoryDisplayUw', 0.0), 208.77752436243003, threshold=0.00001, msg="powerCategoryDisplayUw")
        self.assertAlmostEqualThreshold(metrics.get('powerCategoryGpuUw', 0.0), 13.799502384408045, threshold=0.00001, msg="powerCategoryGpuUw")
        self.assertAlmostEqualThreshold(metrics.get('powerCategoryMemoryUw', 0.0), 73.69686916856728, threshold=0.00001, msg="powerCategoryMemoryUw")
        self.assertAlmostEqualThreshold(metrics.get('powerCategoryMachineLearningUw', 0.0), 10.527679867302508, threshold=0.00001, msg="powerCategoryMachineLearningUw")
        self.assertAlmostEqualThreshold(metrics.get('powerCategoryNetworkUw', 0.0), 123.74248393116318, threshold=0.00001, msg="powerCategoryNetworkUw")
        self.assertAlmostEqualThreshold(metrics.get('powerUncategorizedUw', 0.0), 25.454281567489115, threshold=0.00001, msg="powerUncategorizedUw")
        self.assertAlmostEqualThreshold(metrics.get('powerTotalUw', 0.0), 536.9392494298155, threshold=0.00001, msg="powerTotalUw")

    def test_successful_fixed_trace_battery_discharge(self):
        query = """
        INCLUDE PERFETTO MODULE androidx.benchmark.battery;
        SELECT start_mah, end_mah, diff_mah FROM androidx_battery_discharge;
        """
        rows = self.run_query('api31_battery_discharge.perfetto-trace', query)
        self.assertTrue(len(rows) > 0, "No battery rows returned")
        row = rows[0]
        
        self.assertAlmostEqualThreshold(float(row['start_mah']), 1020.0, threshold=0.1, msg="batteryStartMah")
        self.assertAlmostEqualThreshold(float(row['end_mah']), 1007.0, threshold=0.1, msg="batteryEndMah")
        self.assertAlmostEqualThreshold(float(row['diff_mah']), 13.0, threshold=0.1, msg="batteryDiffMah")

if __name__ == '__main__':
    unittest.main()
