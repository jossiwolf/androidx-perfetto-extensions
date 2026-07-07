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

INCLUDE PERFETTO MODULE android.frames.timeline;
INCLUDE PERFETTO MODULE android.frames.per_frame_metrics;

-- Get individual frame timing metrics for a given process.
-- Matches UI thread Choreographer callbacks with RenderThread DrawFrame slices
-- and (on API 31+) frame timeline slices.
CREATE PERFETTO FUNCTION androidx_frame_timing(
  -- Glob pattern matching the target process name.
  process_glob STRING
)
RETURNS TABLE(
  -- Frame ID (vsync ID or manually generated for legacy).
  frame_id LONG,
  -- CPU duration of the frame (UI thread + RenderThread) in milliseconds.
  cpu_duration_ms DOUBLE,
  -- UI thread duration (Choreographer#doFrame) in milliseconds.
  ui_duration_ms DOUBLE,
  -- Frame overrun in milliseconds (API 31+). Positive if frame janked.
  frame_overrun_ms DOUBLE,
  -- Full duration from expected VSYNC start to actual rendering end (API 31+).
  full_duration_ms DOUBLE
) AS
SELECT
  f.frame_id,
  (COALESCE(
    (SELECT s.ts + s.dur FROM slice s WHERE s.id = f.draw_frame_id),
    (SELECT s.ts + s.dur FROM slice s WHERE s.id = f.do_frame_id)
  ) - f.ts) / 1e6 AS cpu_duration_ms,
  (SELECT s.dur FROM slice s WHERE s.id = f.do_frame_id) / 1e6 AS ui_duration_ms,
  overrun.overrun / 1e6 AS frame_overrun_ms,
  (CASE
    WHEN f.actual_frame_timeline_id IS NOT NULL AND f.expected_frame_timeline_id IS NOT NULL
    THEN (
      SELECT
        CASE
          WHEN act.ts + act.dur > COALESCE(rt.ts + rt.dur, 0) THEN act.ts + act.dur
          ELSE COALESCE(rt.ts + rt.dur, act.ts + act.dur)
        END - exp.ts
      FROM slice act
      JOIN slice exp ON exp.id = f.expected_frame_timeline_id
      LEFT JOIN slice rt ON rt.id = f.draw_frame_id
      WHERE act.id = f.actual_frame_timeline_id
    )
    ELSE NULL
  END) / 1e6 AS full_duration_ms
FROM android_frames f
LEFT JOIN android_frames_overrun overrun USING (frame_id)
WHERE f.process_name GLOB $process_glob;
