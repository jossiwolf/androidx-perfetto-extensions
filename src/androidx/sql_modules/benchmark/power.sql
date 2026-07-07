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

-- Power rail metrics (energy and average power) calculated over the entire trace.
CREATE PERFETTO TABLE androidx_power_metrics(
  -- Name of the power rail counter track.
  track_name STRING,
  -- Energy consumed in microwatt-seconds (uWs) over the trace.
  energy_uws DOUBLE,
  -- Average power in microwatts (uW) over the trace.
  power_uw DOUBLE
) AS
SELECT
  t.name AS track_name,
  MAX(c.value) - MIN(c.value) AS energy_uws,
  IIF(
    MAX(c.ts) = MIN(c.ts),
    0.0,
    (MAX(c.value) - MIN(c.value)) / ((MAX(c.ts) - MIN(c.ts)) / 1000000.0)
  ) AS power_uw
FROM counter c
JOIN counter_track t ON c.track_id = t.id
WHERE t.name GLOB 'power.*'
GROUP BY t.name;
