--
-- Copyright 2026 The Android Open Source Project
--
-- Licensed under the Apache License, Version 2.0 (the "License");
-- you may not use this file except in compliance with the License.
-- You may obtain a copy of the License at
--
--     https://www.apache.org/licenses/LICENSE-2.0
--
-- Unless required by applicable law or agreed to in writing, software
-- distributed under the License is distributed on an "AS IS" BASIS,
-- WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
-- See the License for the specific language governing permissions and
-- limitations under the License.
--

-- Get maximum memory usage (RSS, Heap, GPU) in KB for a given process.
CREATE PERFETTO FUNCTION androidx_memory_usage_max(
  -- Glob pattern matching the target process name.
  process_glob STRING
)
RETURNS TABLE(
  -- Name of the memory counter track.
  counter_name STRING,
  -- Maximum value observed, converted to KB.
  max_value_kb DOUBLE
) AS
SELECT
  track.name AS counter_name,
  MAX(value) / IIF(track.name = 'Heap size (KB)', 1.0, 1024.0) AS max_value_kb
FROM counter
LEFT JOIN process_counter_track AS track ON counter.track_id = track.id
LEFT JOIN process USING (upid)
WHERE process.name GLOB $process_glob
  AND (
    track.name LIKE 'mem.rss%' OR
    track.name = 'Heap size (KB)' OR
    track.name = 'GPU Memory'
  )
GROUP BY counter_name;

-- Get last observed memory usage (RSS, Heap, GPU) in KB for a given process.
CREATE PERFETTO FUNCTION androidx_memory_usage_last(
  -- Glob pattern matching the target process name.
  process_glob STRING
)
RETURNS TABLE(
  -- Name of the memory counter track.
  counter_name STRING,
  -- Last value observed, converted to KB.
  last_value_kb DOUBLE
) AS
WITH ranked_counters AS (
  SELECT
    track.name AS counter_name,
    value,
    ROW_NUMBER() OVER (PARTITION BY track.id ORDER BY ts DESC) as rn,
    track.name = 'Heap size (KB)' as already_in_kb
  FROM counter
  LEFT JOIN process_counter_track AS track ON counter.track_id = track.id
  LEFT JOIN process USING (upid)
  WHERE process.name GLOB $process_glob
    AND (
      track.name LIKE 'mem.rss%' OR
      track.name = 'Heap size (KB)' OR
      track.name = 'GPU Memory'
    )
)
SELECT
  counter_name,
  value / IIF(already_in_kb, 1.0, 1024.0) AS last_value_kb
FROM ranked_counters
WHERE rn = 1;

-- Get total counts for memory events (page faults, compaction, reclaim) for a given process.
CREATE PERFETTO FUNCTION androidx_memory_counters(
  -- Glob pattern matching the target process name.
  process_glob STRING
)
RETURNS TABLE(
  -- Name of the memory event counter track.
  counter_name STRING,
  -- Sum of the counter values over the trace.
  total_count DOUBLE
) AS
SELECT
  track.name AS counter_name,
  SUM(value) AS total_count
FROM counter
LEFT JOIN process_counter_track AS track ON counter.track_id = track.id
LEFT JOIN process USING (upid)
WHERE process.name GLOB $process_glob
  AND track.name LIKE 'mem.%.count'
GROUP BY counter_name;
