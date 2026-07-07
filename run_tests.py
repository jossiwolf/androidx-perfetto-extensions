import subprocess
import os
import json
import sys
import shutil
import tempfile
import urllib.request

# Configuration
DEFAULT_TRACES_DIR = '/usr/local/google/home/jossiwolf/androidx-main/out/androidx/activity/integration-tests/macrobenchmark/build/intermediates/assets/release/mergeReleaseAssets'
TRACES_DIR = os.environ.get('ANDROIDX_TEST_TRACES_DIR', DEFAULT_TRACES_DIR)
pkg_base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), 'src'))
modules = ['jank', 'frame', 'startup', 'trace', 'art', 'power', 'battery', 'memory']

def get_trace_processor():
    # Check if trace_processor is in PATH
    tp = shutil.which('trace_processor')
    if tp:
        return tp
    
    # Check if trace_processor is in current directory
    local_tp = os.path.abspath(os.path.join(os.path.dirname(__file__), 'trace_processor'))
    if os.path.exists(local_tp) and os.access(local_tp, os.X_OK):
        return local_tp
    
    # Download trace_processor
    print("trace_processor not found. Downloading from get.perfetto.dev...")
    url = "https://get.perfetto.dev/trace_processor"
    try:
        urllib.request.urlretrieve(url, local_tp)
        os.chmod(local_tp, 0o755)
        return local_tp
    except Exception as e:
        print(f"Failed to download trace_processor: {e}")
        sys.exit(1)

tp_path = get_trace_processor()

# Create a temporary directory to merge all modules for testing
temp_dir = tempfile.mkdtemp()
temp_pkg_dir = os.path.join(temp_dir, 'sql_modules')
os.makedirs(os.path.join(temp_pkg_dir, 'benchmark'))

# Copy all SQL files to the temp directory to mock a single unified package for trace_processor
for m in modules:
    src_mod_dir = os.path.join(pkg_base_dir, m, 'sql_modules', 'benchmark')
    if os.path.exists(src_mod_dir):
        for fn in os.listdir(src_mod_dir):
            if fn.endswith('.sql'):
                shutil.copy(
                    os.path.join(src_mod_dir, fn),
                    os.path.join(temp_pkg_dir, 'benchmark', fn)
                )

def run_query(trace_file, query):
    trace_path = os.path.join(TRACES_DIR, trace_file)
    if not os.path.exists(trace_path):
        print(f"Error: Trace file not found: {trace_path}")
        print(f"Please point ANDROIDX_TEST_TRACES_DIR to the directory containing AndroidX macrobenchmark trace assets.")
        shutil.rmtree(temp_dir)
        sys.exit(1)
        
    cmd = [
        tp_path, 'query',
        '--add-sql-package', f'{temp_pkg_dir}@androidx',
        trace_path,
        query
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        return {'error': result.stderr.strip()}
    
    lines = result.stdout.strip().split('\n')
    data_lines = [l for l in lines if l and not l.startswith('Loading trace') and not l.startswith('column ') and not l.startswith('[')]
    if not data_lines:
        return {'rows': []}
    
    headers = [h.strip('"') for h in data_lines[0].split(',')]
    rows = []
    for l in data_lines[1:]:
        values = [v.strip('"') for v in l.split(',')]
        rows.append(dict(zip(headers, values)))
    return {'rows': rows}

def assert_almost_equal(actual, expected, threshold=0.001, label=""):
    diff = abs(actual - expected)
    if diff > threshold:
        raise AssertionError(f"{label}: expected {expected}, got {actual} (diff {diff} > threshold {threshold})")

# ==================== TEST CASES ====================

def test_frame_timing_metric():
    print("Running test_frame_timing_metric...")
    query = """
    INCLUDE PERFETTO MODULE androidx.benchmark.frame;
    SELECT frame_id, cpu_duration_ms, frame_overrun_ms 
    FROM androidx_frame_timing 
    WHERE process_name = 'androidx.benchmark.integration.macrobenchmark.target' 
    ORDER BY frame_id;
    """
    res = run_query('api31_scroll.perfetto-trace', query)
    if 'error' in res:
        print(f"  FAIL: {res['error']}")
        return False
    rows = res['rows']
    
    # 1. Assert total frames
    expected_count = 98
    if len(rows) != expected_count:
        print(f"  FAIL: Expected {expected_count} frames, got {len(rows)}")
        return False
        
    # 2. Assert first 10 CPU durations
    expected_cpu = [6.881407, 5.648542, 3.830261, 4.343438, 4.820522, 11.301147, 4.205469, 4.076615, 4.973699, 4.408334]
    expected_overrun = [-5.207137, -11.699862, -14.025295, -12.300155, -11.944858, -8.354770, -9.73489, -10.849726, -11.046253, -10.997936]
    
    try:
        for i in range(10):
            row = rows[i]
            assert_almost_equal(float(row['cpu_duration_ms']), expected_cpu[i], label=f"Frame {i} CPU")
            assert_almost_equal(float(row['frame_overrun_ms']), expected_overrun[i], label=f"Frame {i} Overrun")
    except AssertionError as e:
        print(f"  FAIL: {e}")
        return False
        
    print("  PASS")
    return True

def test_startup_timing_metric():
    print("Running test_startup_timing_metric...")
    
    # Warm start API 32
    query_warm = """
    INCLUDE PERFETTO MODULE androidx.benchmark.startup;
    SELECT time_to_initial_display_ms, time_to_full_display_ms 
    FROM androidx_startup_timing 
    WHERE package_name = 'androidx.benchmark.integration.macrobenchmark.target';
    """
    res_warm = run_query('api32_startup_warm.perfetto-trace', query_warm)
    if 'error' in res_warm:
        print(f"  FAIL (warm): {res_warm['error']}")
        return False
    rows_warm = res_warm['rows']
    if not rows_warm:
        print("  FAIL (warm): No rows returned")
        return False
    try:
        assert_almost_equal(float(rows_warm[0]['time_to_initial_display_ms']), 154.636678, label="Warm Initial Display")
        assert_almost_equal(float(rows_warm[0]['time_to_full_display_ms']), 659.648153, label="Warm Full Display")
    except AssertionError as e:
        print(f"  FAIL (warm): {e}")
        return False

    # Warm start same proc immediate fully drawn API 24
    query_immediate = """
    INCLUDE PERFETTO MODULE androidx.benchmark.startup;
    SELECT time_to_initial_display_ms, time_to_full_display_ms 
    FROM androidx_startup_timing 
    WHERE package_name = 'androidx.benchmark.macro.test';
    """
    res_imm = run_query('api24_startup_sameproc_immediatefullydrawn.perfetto-trace', query_immediate)
    if 'error' in res_imm:
        print(f"  FAIL (immediate): {res_imm['error']}")
        return False
    rows_imm = res_imm['rows']
    if not rows_imm:
        print("  FAIL (immediate): No rows returned")
        return False
    try:
        assert_almost_equal(float(rows_imm[0]['time_to_initial_display_ms']), 178.58525, label="Immediate Initial Display")
        assert_almost_equal(float(rows_imm[0]['time_to_full_display_ms']), 178.58525, label="Immediate Full Display")
    except AssertionError as e:
        print(f"  FAIL (immediate): {e}")
        return False

    print("  PASS")
    return True

def test_art_metric():
    print("Running test_art_metric...")
    query = """
    INCLUDE PERFETTO MODULE androidx.benchmark.art;
    SELECT jit_sum_ms, jit_count, verify_class_sum_ms, verify_class_count, class_load_sum_ms, class_load_count 
    FROM androidx_art_metrics 
    WHERE process_name = 'androidx.compose.integration.hero.macrobenchmark.target';
    """
    res = run_query('api35_startup_cold_classinit.perfetto-trace', query)
    if 'error' in res:
        print(f"  FAIL: {res['error']}")
        return False
    rows = res['rows']
    if not rows:
        print("  FAIL: No rows returned")
        return False
    row = rows[0]
    try:
        assert_almost_equal(float(row['jit_sum_ms']), 433.488508, threshold=0.001, label="JIT Sum")
        assert_almost_equal(float(row['jit_count']), 177, threshold=0.001, label="JIT Count")
        assert_almost_equal(float(row['verify_class_sum_ms']), 0.0, threshold=0.001, label="Verify Class Sum")
        assert_almost_equal(float(row['verify_class_count']), 0, threshold=0.001, label="Verify Class Count")
        assert_almost_equal(float(row['class_load_sum_ms']), 147.052337, threshold=0.001, label="Class Load Sum")
        assert_almost_equal(float(row['class_load_count']), 2013, threshold=0.001, label="Class Load Count")
    except AssertionError as e:
        print(f"  FAIL: {e}")
        return False
        
    print("  PASS")
    return True

def test_memory_usage_metric():
    print("Running test_memory_usage_metric...")
    query = """
    INCLUDE PERFETTO MODULE androidx.benchmark.memory;
    SELECT counter_name, max_value_kb 
    FROM androidx_memory_usage 
    WHERE process_name = 'androidx.benchmark.integration.macrobenchmark.target';
    """
    res = run_query('api31_startup_cold.perfetto-trace', query)
    if 'error' in res:
        print(f"  FAIL: {res['error']}")
        return False
    rows = res['rows']
    if not rows:
        print("  FAIL: No rows returned")
        return False
        
    metrics = {row['counter_name']: float(row['max_value_kb']) for row in rows}
    try:
        assert_almost_equal(metrics.get('Heap size (KB)', 0.0), 3067.0, label="Heap Size Max")
        assert_almost_equal(metrics.get('mem.rss.anon', 0.0), 47260.0, label="Rss Anon Max")
        assert_almost_equal(metrics.get('mem.rss.file', 0.0), 67668.0, label="Rss File Max")
    except AssertionError as e:
        print(f"  FAIL: {e}")
        return False
        
    print("  PASS")
    return True

def test_memory_counters_metric():
    print("Running test_memory_counters_metric...")
    query = """
    INCLUDE PERFETTO MODULE androidx.benchmark.memory;
    SELECT counter_name, total_count 
    FROM androidx_memory_counters 
    WHERE process_name = 'androidx.benchmark.integration.macrobenchmark.target';
    """
    res = run_query('api31_startup_cold.perfetto-trace', query)
    if 'error' in res:
        print(f"  FAIL: {res['error']}")
        return False
    rows = res['rows']
    if not rows:
        print("  FAIL: No rows returned")
        return False
        
    metrics = {row['counter_name']: float(row['total_count']) for row in rows}
    try:
        assert_almost_equal(metrics.get('mem.mm.min_flt.count', 0.0), 3431.0, label="Minor Page Faults")
        assert_almost_equal(metrics.get('mem.mm.maj_flt.count', 0.0), 6.0, label="Major Page Faults")
        assert_almost_equal(metrics.get('mem.mm.swp_flt.count', 0.0), 0.0, label="Page Faults Backed by Swap Cache")
        assert_almost_equal(metrics.get('mem.mm.read_io.count', 0.0), 8.0, label="Page Faults Backed by Read IO")
    except AssertionError as e:
        print(f"  FAIL: {e}")
        return False
        
    print("  PASS")
    return True

def test_power_metric():
    print("Running test_power_metric...")
    
    # 1. Test Energy Breakdown
    query_energy = """
    INCLUDE PERFETTO MODULE androidx.benchmark.power;
    SELECT metric_name, value FROM androidx_power_output;
    """
    res = run_query('api32_odpm_rails.perfetto-trace', query_energy)
    if 'error' in res:
        print(f"  FAIL (energy): {res['error']}")
        return False
    rows = res['rows']
    if not rows:
        print("  FAIL (energy): No rows returned")
        return False
        
    metrics = {row['metric_name']: float(row['value']) for row in rows}
    try:
        # Check energy component breakdown
        assert_almost_equal(metrics.get('energyComponentCpuBigUws', 0.0), 31935.0, threshold=0.1, label="energyComponentCpuBigUws")
        assert_almost_equal(metrics.get('energyComponentCpuLittleUws', 0.0), 303264.0, threshold=0.1, label="energyComponentCpuLittleUws")
        assert_almost_equal(metrics.get('energyComponentCpuMidUws', 0.0), 55179.0, threshold=0.1, label="energyComponentCpuMidUws")
        assert_almost_equal(metrics.get('energyComponentDisplayUws', 0.0), 1006934.0, threshold=0.1, label="energyComponentDisplayUws")
        assert_almost_equal(metrics.get('energyComponentGpuUws', 0.0), 66555.0, threshold=0.1, label="energyComponentGpuUws")
        assert_almost_equal(metrics.get('energyTotalUws', 0.0), 2589658.0, threshold=0.1, label="energyTotalUws")
        
        # Check power category totals (from same view, but power names)
        assert_almost_equal(metrics.get('powerCategoryCpuUw', 0.0), 80.94090814845532, threshold=0.00001, label="powerCategoryCpuUw")
        assert_almost_equal(metrics.get('powerCategoryDisplayUw', 0.0), 208.77752436243003, threshold=0.00001, label="powerCategoryDisplayUw")
        assert_almost_equal(metrics.get('powerCategoryGpuUw', 0.0), 13.799502384408045, threshold=0.00001, label="powerCategoryGpuUw")
        assert_almost_equal(metrics.get('powerCategoryMemoryUw', 0.0), 73.69686916856728, threshold=0.00001, label="powerCategoryMemoryUw")
        assert_almost_equal(metrics.get('powerCategoryMachineLearningUw', 0.0), 10.527679867302508, threshold=0.00001, label="powerCategoryMachineLearningUw")
        assert_almost_equal(metrics.get('powerCategoryNetworkUw', 0.0), 123.74248393116318, threshold=0.00001, label="powerCategoryNetworkUw")
        assert_almost_equal(metrics.get('powerUncategorizedUw', 0.0), 25.454281567489115, threshold=0.00001, label="powerUncategorizedUw")
        assert_almost_equal(metrics.get('powerTotalUw', 0.0), 536.9392494298155, threshold=0.00001, label="powerTotalUw")
    except AssertionError as e:
        print(f"  FAIL (energy/power): {e}")
        return False
        
    # 2. Test Battery Discharge
    query_battery = """
    INCLUDE PERFETTO MODULE androidx.benchmark.battery;
    SELECT start_mah, end_mah, diff_mah FROM androidx_battery_discharge;
    """
    res_bat = run_query('api31_battery_discharge.perfetto-trace', query_battery)
    if 'error' in res_bat:
        print(f"  FAIL (battery): {res_bat['error']}")
        return False
    rows_bat = res_bat['rows']
    if not rows_bat:
        print("  FAIL (battery): No rows returned")
        return False
    row_bat = rows_bat[0]
    try:
        assert_almost_equal(float(row_bat['start_mah']), 1020.0, threshold=0.1, label="batteryStartMah")
        assert_almost_equal(float(row_bat['end_mah']), 1007.0, threshold=0.1, label="batteryEndMah")
        assert_almost_equal(float(row_bat['diff_mah']), 13.0, threshold=0.1, label="batteryDiffMah")
    except AssertionError as e:
        print(f"  FAIL (battery): {e}")
        return False

    print("  PASS")
    return True

def test_trace_section_metric():
    print("Running test_trace_section_metric...")
    
    # Helper to test different modes for a given section
    def verify_section(trace, pkg, section, first, min_val, max_val, sum_val, count, target_only):
        target_filter = f"AND process_name = '{pkg}'" if target_only else ""
        # 1. Test First
        q_first = f"""
        INCLUDE PERFETTO MODULE androidx.benchmark.trace;
        SELECT dur / 1e6 AS dur_ms FROM androidx_trace_slices 
        WHERE name = '{section}' {target_filter} ORDER BY ts ASC LIMIT 1;
        """
        res = run_query(trace, q_first)
        if 'error' in res: raise AssertionError(f"First query error: {res['error']}")
        assert_almost_equal(float(res['rows'][0]['dur_ms']), first, label=f"First {section}")

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
        res = run_query(trace, q_aggs)
        if 'error' in res: raise AssertionError(f"Aggs query error: {res['error']}")
        row = res['rows'][0]
        assert_almost_equal(float(row['min_ms']), min_val, label=f"Min {section}")
        assert_almost_equal(float(row['max_ms']), max_val, label=f"Max {section}")
        assert_almost_equal(float(row['sum_ms']), sum_val, label=f"Sum {section}")
        assert_almost_equal(int(row['count']), count, label=f"Count {section}")

    try:
        # ActivityThreadMain
        verify_section('api24_startup_cold.perfetto-trace', 'androidx.benchmark.integration.macrobenchmark.target', 
                       'ActivityThreadMain', 12.639, 12.639, 12.639, 12.639, 1, target_only=True)
                       
        # activityStart
        verify_section('api24_startup_cold.perfetto-trace', 'androidx.benchmark.integration.macrobenchmark.target', 
                       'activityStart', 81.979, 81.979, 81.979, 81.979, 1, target_only=True)
                       
        # startActivityAndWait (test process)
        verify_section('api24_startup_cold.perfetto-trace', 'androidx.benchmark.integration.macrobenchmark.test', 
                       'startActivityAndWait', 1110.689, 1110.689, 1110.689, 1110.689, 1, target_only=True)
                       
        # inflate (target only)
        verify_section('api24_startup_cold.perfetto-trace', 'androidx.benchmark.integration.macrobenchmark.target', 
                       'inflate', 4.949, 4.588, 10.242, 19.779, 3, target_only=True)
                       
        # inflate (unfiltered)
        verify_section('api24_startup_cold.perfetto-trace', '', 
                       'inflate', 13.318, 0.836, 13.318, 43.128, 8, target_only=False)
                       
        # wait (non-terminating filter)
        verify_section('api31_startup_cold.perfetto-trace', '', 
                       'wait', 0.00724, 0.001615, 357.761234, 811.865025, 226, target_only=False)
                       
    except AssertionError as e:
        print(f"  FAIL: {e}")
        return False
    except Exception as e:
        print(f"  FAIL (unexpected): {e}")
        return False

    print("  PASS")
    return True

if __name__ == '__main__':
    all_pass = True
    tests = [
        test_frame_timing_metric,
        test_startup_timing_metric,
        test_art_metric,
        test_memory_usage_metric,
        test_memory_counters_metric,
        test_power_metric,
        test_trace_section_metric
    ]
    try:
        for t in tests:
            if not t():
                all_pass = False
    finally:
        # Clean up temp directory
        shutil.rmtree(temp_dir)
    
    if not all_pass:
        print("Some tests FAILED")
        sys.exit(1)
    else:
        print("All tests PASSED")
