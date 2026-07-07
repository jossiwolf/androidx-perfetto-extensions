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

-- ART metrics (JIT, class verification, class loading) for all processes.
CREATE PERFETTO TABLE androidx_art_metrics(
  -- Internal process ID.
  upid JOINID(process.id),
  -- Process name.
  process_name STRING,
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
WITH
  art_slices AS (
    SELECT
      process.upid,
      process.name AS process_name,
      slice.name AS slice_name,
      slice.dur
    FROM slice
    JOIN thread_track ON slice.track_id = thread_track.id
    JOIN thread USING(utid)
    JOIN process USING(upid)
    WHERE slice.name GLOB 'JIT Compiling*'
       OR slice.name GLOB 'VerifyClass*'
       OR slice.name GLOB 'L*;'
  ),
  jit AS (
    SELECT upid, COALESCE(SUM(dur) / 1e6, 0.0) AS sum_dur, COUNT(1) AS count
    FROM art_slices WHERE slice_name GLOB 'JIT Compiling*' GROUP BY upid
  ),
  verify AS (
    SELECT upid, COALESCE(SUM(dur) / 1e6, 0.0) AS sum_dur, COUNT(1) AS count
    FROM art_slices WHERE slice_name GLOB 'VerifyClass*' GROUP BY upid
  ),
  load AS (
    SELECT upid, COALESCE(SUM(dur) / 1e6, 0.0) AS sum_dur, COUNT(1) AS count
    FROM art_slices WHERE slice_name GLOB 'L*;' GROUP BY upid
  )
SELECT
  p.upid,
  p.name AS process_name,
  COALESCE(jit.sum_dur, 0.0) AS jit_sum_ms,
  COALESCE(jit.count, 0) AS jit_count,
  COALESCE(verify.sum_dur, 0.0) AS verify_class_sum_ms,
  COALESCE(verify.count, 0) AS verify_class_count,
  COALESCE(load.sum_dur, 0.0) AS class_load_sum_ms,
  COALESCE(load.count, 0) AS class_load_count
FROM process p
LEFT JOIN jit USING(upid)
LEFT JOIN verify USING(upid)
LEFT JOIN load USING(upid)
WHERE jit.upid IS NOT NULL OR verify.upid IS NOT NULL OR load.upid IS NOT NULL;
