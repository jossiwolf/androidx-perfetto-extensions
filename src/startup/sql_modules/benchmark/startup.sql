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

INCLUDE PERFETTO MODULE android.startup.time_to_display;

-- App startup timing metrics (TTID and TTFD) for all startups.
CREATE PERFETTO TABLE androidx_startup_timing(
  -- Startup ID.
  startup_id LONG,
  -- Package name of the app.
  package_name STRING,
  -- Startup type (cold, warm, hot).
  startup_type STRING,
  -- Time to initial display (TTID) in milliseconds.
  time_to_initial_display_ms DOUBLE,
  -- Time to full display (TTFD) in milliseconds (if reportFullyDrawn called).
  time_to_full_display_ms DOUBLE
) AS
SELECT
  startup_id,
  package AS package_name,
  startup_type,
  time_to_initial_display / 1e6 AS time_to_initial_display_ms,
  time_to_full_display / 1e6 AS time_to_full_display_ms
FROM android_startups
JOIN android_startup_time_to_display USING (startup_id);
