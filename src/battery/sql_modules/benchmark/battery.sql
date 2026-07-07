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

-- Battery discharge metrics (start, end, and diff in mAh) calculated over the entire trace.
CREATE PERFETTO TABLE androidx_battery_discharge(
  -- Start battery charge in mAh.
  start_mah DOUBLE,
  -- End battery charge in mAh.
  end_mah DOUBLE,
  -- Total discharge in mAh.
  diff_mah DOUBLE
) AS
SELECT
  MAX(c.value) / 1000.0 AS start_mah,
  MIN(c.value) / 1000.0 AS end_mah,
  (MAX(c.value) - MIN(c.value)) / 1000.0 AS diff_mah
FROM counter c
JOIN counter_track t ON c.track_id = t.id
WHERE t.name = 'batt.charge_uah';
