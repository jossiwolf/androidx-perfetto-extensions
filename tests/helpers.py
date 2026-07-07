import unittest
import tempfile
import os
import shutil
import subprocess
import urllib.request

class PerfettoTestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.traces_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), 'test_data'))
        cls.pkg_base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '../src'))
        cls.modules = ['jank', 'frame', 'startup', 'trace', 'art', 'power', 'battery', 'memory']
        
        cls.tp_path = cls.get_trace_processor()
        
        # Create temp dir to merge SQL modules
        cls.temp_dir = tempfile.mkdtemp()
        cls.temp_pkg_dir = os.path.join(cls.temp_dir, 'sql_modules')
        os.makedirs(os.path.join(cls.temp_pkg_dir, 'benchmark'))
        
        for m in cls.modules:
            src_mod_dir = os.path.join(cls.pkg_base_dir, m, 'sql_modules', 'benchmark')
            if os.path.exists(src_mod_dir):
                for fn in os.listdir(src_mod_dir):
                    if fn.endswith('.sql'):
                        shutil.copy(
                            os.path.join(src_mod_dir, fn),
                            os.path.join(cls.temp_pkg_dir, 'benchmark', fn)
                        )

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.temp_dir)

    @classmethod
    def get_trace_processor(cls):
        tp = shutil.which('trace_processor')
        if tp:
            return tp
        
        local_tp = os.path.abspath(os.path.join(os.path.dirname(__file__), '../trace_processor'))
        if os.path.exists(local_tp) and os.access(local_tp, os.X_OK):
            return local_tp
        
        print("trace_processor not found. Downloading from get.perfetto.dev...")
        url = "https://get.perfetto.dev/trace_processor"
        try:
            urllib.request.urlretrieve(url, local_tp)
            os.chmod(local_tp, 0o755)
            return local_tp
        except Exception as e:
            print(f"Failed to download trace_processor: {e}")
            raise e

    def run_query(self, trace_file, query):
        trace_path = os.path.join(self.traces_dir, trace_file)
        if not os.path.exists(trace_path):
            raise FileNotFoundError(f"Trace file not found: {trace_path}")
            
        cmd = [
            self.tp_path, 'query',
            '--add-sql-package', f'{self.temp_pkg_dir}@androidx',
            trace_path,
            query
        ]
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            raise RuntimeError(f"Query failed: {result.stderr.strip()}")
        
        lines = result.stdout.strip().split('\n')
        data_lines = [l for l in lines if l and not l.startswith('Loading trace') and not l.startswith('column ') and not l.startswith('[')]
        if not data_lines:
            return []
        
        headers = [h.strip('"') for h in data_lines[0].split(',')]
        rows = []
        for l in data_lines[1:]:
            values = [v.strip('"') for v in l.split(',')]
            rows.append(dict(zip(headers, values)))
        return rows

    def assertAlmostEqualThreshold(self, actual, expected, threshold=0.001, msg=None):
        diff = abs(actual - expected)
        if diff > threshold:
            label = f" ({msg})" if msg else ""
            self.fail(f"Expected {expected}, got {actual} (diff {diff} > threshold {threshold}){label}")
