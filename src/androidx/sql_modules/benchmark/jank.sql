INCLUDE PERFETTO MODULE android.frames.jank_type;

-- Computes jank metrics for a given process.
-- Returns total display tokens, app janky frames, sf janky frames, and total janky frames.
CREATE PERFETTO FUNCTION androidx_benchmark_jank(target_process_name STRING)
RETURNS TABLE(
  total_display_tokens INT,
  app_janky_frames INT,
  sf_janky_frames INT,
  total_janky_frames INT
) AS
WITH
  app_slices AS (
    SELECT
      display_frame_token,
      jank_type
    FROM actual_frame_timeline_slice
    WHERE upid = (
      SELECT upid FROM process WHERE name LIKE $target_process_name
    )
  ),
  sf_slices AS (
    SELECT
      display_frame_token,
      jank_type
    FROM actual_frame_timeline_slice
    WHERE upid = (
      SELECT upid FROM process WHERE name = '/system/bin/surfaceflinger'
    )
  ),
  all_tokens AS (
    SELECT display_frame_token AS token FROM app_slices
    UNION
    SELECT display_frame_token AS token FROM sf_slices
  )
SELECT
  -- The denominator: unique display slots encountered
  (
    SELECT COUNT(DISTINCT token) FROM all_tokens
  ) AS total_display_tokens,

  -- App-caused jank tokens
  (
    SELECT COUNT(DISTINCT display_frame_token)
    FROM app_slices
    WHERE android_is_app_jank_type(jank_type)
  ) AS app_janky_frames,

  -- SF-caused jank tokens
  (
    SELECT COUNT(DISTINCT display_frame_token)
    FROM sf_slices
    WHERE android_is_sf_jank_type(jank_type)
  ) AS sf_janky_frames,

  -- Deduplicated total jank count (Union of all missed frames)
  (
    SELECT COUNT(DISTINCT token)
    FROM (
      SELECT display_frame_token AS token
      FROM app_slices
      WHERE android_is_missed_frame_type(jank_type)
      UNION
      SELECT display_frame_token AS token
      FROM sf_slices
      WHERE android_is_missed_frame_type(jank_type)
    )
  ) AS total_janky_frames;
