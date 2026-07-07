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

-- Get slices matching a specific name pattern for a given process.
-- Useful for calculating custom trace section durations.
CREATE PERFETTO FUNCTION androidx_trace_slices(
  -- Glob pattern matching the slice name (e.g. 'MyCustomSlice%' or 'Choreographer#doFrame%').
  section_glob STRING,
  -- Glob pattern matching the target process name.
  process_glob STRING
)
RETURNS TABLE(
  -- Slice start timestamp.
  ts TIMESTAMP,
  -- Slice duration.
  dur DURATION,
  -- Slice name.
  name STRING
) AS
SELECT slice.ts, slice.dur, slice.name
FROM slice
JOIN thread_track ON slice.track_id = thread_track.id
JOIN thread USING(utid)
JOIN process USING(upid)
WHERE slice.name GLOB $section_glob
  AND process.name GLOB $process_glob;
