# Agent Guidelines for AndroidX Perfetto Extensions

This workspace implements AndroidX Macrobenchmark metrics as PerfettoSQL tables and views.

## Commit Validation Rule
Before proposing any code change, committing, or declaring a task complete, you **MUST** run the integration test suite to ensure no regressions are introduced and the SQL modules produce correct metrics:

1.  **Rebuild Manifest and Packages**:
    Run `build.py` to compile the SQL files into JSON modules and regenerate the server manifest:
    ```bash
    python3 build.py
    ```

2.  **Run the Test Suite**:
    Run `run_tests.py` in the root of the repository. This script downloads the `trace_processor_shell` if not present, merges the separate SQL modules into a mock package, and executes queries against integration test traces from the AndroidX codebase:
    ```bash
    python3 run_tests.py
    ```

3.  **Required State**: All tests must print `PASS` and the runner must exit with code `0`. If any tests fail, you must fix the SQL implementation to align with the expected values.

## Testing Traces
The tests rely on trace assets located in the AndroidX build output directory. 
If the script complains about missing trace files, make sure the `ANDROIDX_TEST_TRACES_DIR` environment variable is set to the directory containing the trace assets (e.g., `androidx-main/out/.../mergeReleaseAssets`).
