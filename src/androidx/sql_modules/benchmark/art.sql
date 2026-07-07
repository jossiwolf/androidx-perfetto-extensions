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

-- Helper to sum and count slices matching a pattern.
CREATE PERFETTO FUNCTION _art_slice_stats(
  -- Glob pattern matching the slice name.
  pattern STRING,
  -- Glob pattern matching the target process name.
  process_glob STRING
)
RETURNS TABLE(
  -- Sum of durations in milliseconds.
  sum_dur_ms DOUBLE,
  -- Count of slices.
  count INT
) AS
SELECT
  COALESCE(SUM(dur) / 1e6, 0.0) AS sum_dur_ms,
  COUNT(1) AS count
FROM slice
JOIN thread_track ON slice.track_id = thread_track.id
JOIN thread USING(utid)
JOIN process USING(upid)
WHERE slice.name GLOB $pattern
  AND process.name GLOB $process_glob;

-- Get ART metrics (JIT, class verification, class loading) for a given process.
CREATE PERFETTO FUNCTION androidx_art_metrics(
  -- Glob pattern matching the target process name.
  process_glob STRING
)
RETURNS TABLE(
  -- Total JIT compilation duration in milliseconds.
  jit_sum_ms DOUBLE,
  -- Total JIT compilation count.
  jit_count INT,
  -- Total class verification duration in milliseconds.
  verify_class_sum_ms DOUBLE,
  -- Total class verification count.
  verify_class_count INT,
  -- Total class loading duration in milliseconds.
  class_load_sum_ms DOUBLE,
  -- Total class loading count.
  class_load_count INT
) AS
SELECT
  (SELECT sum_dur_ms FROM _art_slice_stats('JIT Compiling*', $process_glob)) AS jit_sum_ms,
  (SELECT count FROM _art_slice_stats('JIT Compiling*', $process_glob)) AS jit_count,
  (SELECT sum_dur_ms FROM _art_slice_stats('VerifyClass*', $process_glob)) AS verify_class_sum_ms,
  (SELECT count FROM _art_slice_stats('VerifyClass*', $process_glob)) AS verify_class_count,
  (SELECT sum_dur_ms FROM _art_slice_stats('L*;', $process_glob)) AS class_load_sum_ms,
  (SELECT count FROM _art_slice_stats('L*;', $process_glob)) AS class_load_count;
