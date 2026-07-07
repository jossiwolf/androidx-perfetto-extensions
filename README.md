# User Guide: AndroidX PerfettoSQL Modules

This guide describes how to load the AndroidX PerfettoSQL extension package and lists the available metrics.

## Loading the Extension Server in Perfetto UI

You can load these modules into the Perfetto UI (https://ui.perfetto.dev) directly from GitHub:

1. Open the Perfetto UI (https://ui.perfetto.dev).
2. Go to **Settings** (gear icon in the sidebar) -> **Extension Servers** (or open [settings directly](https://ui.perfetto.dev/#!/settings/dev.perfetto.ExtensionServers)).
3. Click **Add Server** and select **GitHub**.
4. Enter the repository `jossiwolf/androidx-perfetto-extensions` in the **Repository** field.
5. Enter `main` in the **Ref** field.
6. The UI will fetch the manifest. Enable the specific modules you need (e.g. `Jank`, `Frame`, `Startup`, `Trace`, `Art`, `Power`, `Battery`, `Memory`).
7. Click **Save** and reload the page.

---


## List of Available Metrics

All tables and views are under the `androidx` namespace. To use them, you must include their corresponding module first:
`INCLUDE PERFETTO MODULE androidx.benchmark.[module_name];`

### Jank Metrics (`androidx.benchmark.jank`)
Exposes frame timeline-based jank metrics (S+).

- **Table/View**: `androidx_benchmark_jank(process_name STRING)` (Function)
  *Note: This specific one is currently implemented as a function to match targets.*
- **Columns**:
  - `total_display_tokens`: Unique display vsync slots encountered.
  - `app_janky_frames`: Count of frames janked due to app-side delays.
  - `sf_janky_frames`: Count of frames janked due to SurfaceFlinger delays.
  - `total_janky_frames`: Total janky frames.
- **Example**:
  ```sql
  INCLUDE PERFETTO MODULE androidx.benchmark.jank;
  SELECT * FROM androidx_benchmark_jank('com.example.myapp');
  ```

---

### Frame Timing (`androidx.benchmark.frame`)
Exposes detailed frame-by-frame performance stats.

- **Table**: `androidx_frame_timing`
- **Columns**:
  - `frame_id`: VSYNC ID.
  - `process_name`: Target app process.
  - `cpu_duration_ms`: Duration of UI Thread + RenderThread work.
  - `ui_duration_ms`: Duration of UI Thread work (`Choreographer#doFrame`).
  - `frame_overrun_ms`: Milliseconds the frame missed its VSYNC deadline (S+).
  - `full_duration_ms`: Expected VSYNC start to actual rendering end (S+).
- **Example**:
  ```sql
  INCLUDE PERFETTO MODULE androidx.benchmark.frame;
  SELECT * FROM androidx_frame_timing 
  WHERE process_name = 'com.example.myapp' AND frame_overrun_ms > 0;
  ```

---

### Startup Timing (`androidx.benchmark.startup`)
Exposes cold/warm/hot app startup durations (TTID and TTFD).

- **Table**: `androidx_startup_timing`
- **Columns**:
  - `package_name`: Package of the started app.
  - `startup_type`: Cold, warm, or hot start.
  - `time_to_initial_display_ms`: Time to first frame display (TTID).
  - `time_to_full_display_ms`: Time to `reportFullyDrawn()` display (TTFD).
- **Example**:
  ```sql
  INCLUDE PERFETTO MODULE androidx.benchmark.startup;
  SELECT package_name, startup_type, time_to_initial_display_ms 
  FROM androidx_startup_timing;
  ```

---

### Trace Sections (`androidx.benchmark.trace`)
Exposes all slices in the trace with process and thread context.

- **View**: `androidx_trace_slices`
- **Columns**:
  - `name`: Slice name (e.g. `Choreographer#doFrame`).
  - `ts`: Timestamp.
  - `dur`: Duration.
  - `process_name`: Process name.
  - `thread_name`: Thread name.
- **Example**: Sum of a custom trace section:
  ```sql
  INCLUDE PERFETTO MODULE androidx.benchmark.trace;
  SELECT SUM(dur) / 1e6 AS total_ms, COUNT(1) AS count 
  FROM androidx_trace_slices 
  WHERE name = 'MyCustomSection' AND process_name = 'com.example.myapp';
  ```

---

### ART Runtime Metrics (`androidx.benchmark.art`)
Exposes compilation, verification, and loading metrics.

- **Table**: `androidx_art_metrics`
- **Columns**:
  - `process_name`: Process name.
  - `jit_sum_ms` / `jit_count`: JIT compiler time and invocation count.
  - `verify_class_sum_ms` / `verify_class_count`: Class verification time and count.
  - `class_load_sum_ms` / `class_load_count`: Class loading (`L%;`) time and count.
- **Example**:
  ```sql
  INCLUDE PERFETTO MODULE androidx.benchmark.art;
  SELECT process_name, class_load_sum_ms, class_load_count 
  FROM androidx_art_metrics;
  ```

---

### Power and Energy (`androidx.benchmark.power`)
Exposes total energy and average power consumption per rail.

- **Table**: `androidx_power_metrics`
- **Columns**:
  - `track_name`: Power rail counter track name (e.g., `power.rails.cpu.little`).
  - `energy_uws`: Energy in microwatt-seconds (uWs).
  - `power_uw`: Average power in microwatts (uW).
- **Example**:
  ```sql
  INCLUDE PERFETTO MODULE androidx.benchmark.power;
  SELECT * FROM androidx_power_metrics WHERE track_name LIKE '%cpu%';
  ```

---

### Battery Discharge (`androidx.benchmark.battery`)
Exposes battery discharge metrics over the trace.

- **Table**: `androidx_battery_discharge`
- **Columns**:
  - `start_mah`: Starting battery charge in mAh.
  - `end_mah`: Ending battery charge in mAh.
  - `diff_mah`: Total battery discharged in mAh.
- **Example**:
  ```sql
  INCLUDE PERFETTO MODULE androidx.benchmark.battery;
  SELECT diff_mah FROM androidx_battery_discharge;
  ```

---

### Memory Usage and Counters (`androidx.benchmark.memory`)
Exposes process-level memory usage (RSS, Heap) and kernel memory events.

- **Table**: `androidx_memory_usage`
  - Columns:
    - `process_name`: Process name.
    - `counter_name`: Counter type (e.g., `mem.rss.anon`, `Heap size (KB)`).
    - `max_value_kb`: Maximum memory observed.
    - `last_value_kb`: Last memory value observed.
- **Table**: `androidx_memory_counters`
  - Columns:
    - `process_name`: Process name.
    - `counter_name`: Kernel event name (e.g. `mem.mm.min_flt.count` for minor page faults).
    - `total_count`: Total event count.
- **Example**: Max RSS Anon for app:
  ```sql
  INCLUDE PERFETTO MODULE androidx.benchmark.memory;
  SELECT max_value_kb FROM androidx_memory_usage 
  WHERE process_name = 'com.example.myapp' AND counter_name = 'mem.rss.anon';
  ```
