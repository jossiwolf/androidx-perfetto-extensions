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

-- Memory usage metrics (RSS, Heap, GPU) in KB for all processes.
-- Exposes both maximum (max) and last observed (last) values.
CREATE PERFETTO TABLE androidx_memory_usage(
  -- Internal process ID.
  upid JOINID(process.id),
  -- Process name.
  process_name STRING,
  -- Name of the memory counter track.
  counter_name STRING,
  -- Maximum value observed in KB.
  max_value_kb DOUBLE,
  -- Last observed value in KB.
  last_value_kb DOUBLE
) AS
WITH
  max_val AS (
    SELECT
      upid,
      track.name AS counter_name,
      MAX(value) / IIF(track.name = 'Heap size (KB)', 1.0, 1024.0) AS max_value_kb
    FROM counter
    LEFT JOIN process_counter_track AS track ON counter.track_id = track.id
    WHERE track.name LIKE 'mem.rss%' OR track.name = 'Heap size (KB)' OR track.name = 'GPU Memory'
    GROUP BY upid, counter_name
  ),
  last_val AS (
    SELECT
      upid,
      counter_name,
      value / IIF(already_in_kb, 1.0, 1024.0) AS last_value_kb
    FROM (
      SELECT
        upid,
        track.name AS counter_name,
        value,
        ROW_NUMBER() OVER (PARTITION BY track.id ORDER BY ts DESC) as rn,
        track.name = 'Heap size (KB)' as already_in_kb
      FROM counter
      LEFT JOIN process_counter_track AS track ON counter.track_id = track.id
      WHERE track.name LIKE 'mem.rss%' OR track.name = 'Heap size (KB)' OR track.name = 'GPU Memory'
    )
    WHERE rn = 1
  )
SELECT
  p.upid,
  p.name AS process_name,
  m.counter_name,
  m.max_value_kb,
  l.last_value_kb
FROM process p
JOIN max_val m ON p.upid = m.upid
JOIN last_val l ON p.upid = l.upid AND l.counter_name = m.counter_name;

-- Total counts for memory events (page faults, compaction, reclaim) for all processes.
CREATE PERFETTO TABLE androidx_memory_counters(
  -- Internal process ID.
  upid JOINID(process.id),
  -- Process name.
  process_name STRING,
  -- Name of the memory event counter track.
  counter_name STRING,
  -- Sum of the counter values over the trace.
  total_count DOUBLE
) AS
SELECT
  p.upid,
  p.name AS process_name,
  track.name AS counter_name,
  SUM(value) AS total_count
FROM counter
LEFT JOIN process_counter_track AS track ON counter.track_id = track.id
LEFT JOIN process p USING (upid)
WHERE track.name LIKE 'mem.%.count'
GROUP BY upid, counter_name;
