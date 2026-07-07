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

-- View exposing all trace slices with process and thread context.
-- Useful for querying custom trace section durations.
CREATE PERFETTO VIEW androidx_trace_slices(
  -- Slice start timestamp.
  ts TIMESTAMP,
  -- Slice duration.
  dur DURATION,
  -- Slice name.
  name STRING,
  -- Process name.
  process_name STRING,
  -- Thread name.
  thread_name STRING,
  -- Internal process ID.
  upid JOINID(process.id),
  -- Internal thread ID.
  utid JOINID(thread.id)
) AS
SELECT
  slice.ts,
  slice.dur,
  slice.name,
  process.name AS process_name,
  thread.name AS thread_name,
  process.upid,
  thread.utid
FROM slice
JOIN thread_track ON slice.track_id = thread_track.id
JOIN thread USING(utid)
JOIN process USING(upid);
