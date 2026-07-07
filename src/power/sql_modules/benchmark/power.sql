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

-- Helper view to map raw tracks to camelCase components and categories
CREATE PERFETTO VIEW _androidx_power_mapped AS
SELECT
  track_name,
  energy_uws,
  power_uw,
  CASE
    WHEN track_name = 'power.rails.tpu' THEN 'Tpu'
    WHEN track_name = 'power.rails.modem' THEN 'Modem'
    WHEN track_name = 'power.rails.radio.frontend' THEN 'RadioFrontend'
    WHEN track_name = 'power.rails.cpu.big' THEN 'CpuBig'
    WHEN track_name = 'power.rails.cpu.mid' THEN 'CpuMid'
    WHEN track_name = 'power.rails.cpu.little' THEN 'CpuLittle'
    WHEN track_name = 'power.rails.system.fabric' THEN 'SystemFabric'
    WHEN track_name = 'power.rails.memory.interface' THEN 'MemoryInterface'
    WHEN track_name = 'power.rails.wifi.bt' THEN 'WifiBt'
    WHEN track_name = 'power.rails.aoc.memory' THEN 'AocMemory'
    WHEN track_name = 'power.rails.aoc.logic' THEN 'AocLogic'
    WHEN track_name = 'power.rails.ddr.a' THEN 'DdrA'
    WHEN track_name = 'power.rails.ddr.b' THEN 'DdrB'
    WHEN track_name = 'power.rails.ddr.c' THEN 'DdrC'
    WHEN track_name = 'power.rails.gpu' THEN 'Gpu'
    WHEN track_name = 'power.rails.display' THEN 'Display'
    ELSE SUBSTR(track_name, 13) -- fallback
  END AS component_name,
  CASE
    WHEN track_name LIKE '%cpu%' THEN 'Cpu'
    WHEN track_name LIKE '%display%' THEN 'Display'
    WHEN track_name LIKE '%gpu%' THEN 'Gpu'
    WHEN track_name LIKE '%gps%' THEN 'Gps'
    WHEN track_name LIKE '%ddr%' OR track_name LIKE '%memory.interface%' THEN 'Memory'
    WHEN track_name LIKE '%tpu%' THEN 'MachineLearning'
    WHEN track_name LIKE '%aoc%' OR track_name LIKE '%radio%' OR track_name LIKE '%wifi%' OR track_name LIKE '%modem%' THEN 'Network'
    ELSE 'Uncategorized'
  END AS category_name
FROM androidx_power_metrics;

-- Exposes formatted power and energy metrics as name-value pairs
CREATE PERFETTO TABLE androidx_power_output(
  -- Formatted metric name (e.g. 'powerCategoryCpuUw', 'energyComponentCpuBigUws').
  metric_name STRING,
  -- Value of the metric.
  value DOUBLE
) AS
-- 1. Component Energy
SELECT 'energyComponent' || component_name || 'Uws' AS metric_name, energy_uws AS value
FROM _androidx_power_mapped
UNION ALL
-- 2. Component Power
SELECT 'powerComponent' || component_name || 'Uw' AS metric_name, power_uw AS value
FROM _androidx_power_mapped
UNION ALL
-- 3. Category Energy
SELECT 'energyCategory' || category_name || 'Uws' AS metric_name, SUM(energy_uws) AS value
FROM _androidx_power_mapped
GROUP BY category_name
UNION ALL
-- 4. Category Power
SELECT 'powerCategory' || category_name || 'Uw' AS metric_name, SUM(power_uw) AS value
FROM _androidx_power_mapped
GROUP BY category_name
UNION ALL
-- 5. Total Energy
SELECT 'energyTotalUws' AS metric_name, SUM(energy_uws) AS value
FROM androidx_power_metrics
UNION ALL
-- 6. Total Power
SELECT 'powerTotalUw' AS metric_name, SUM(power_uw) AS value
FROM androidx_power_metrics
UNION ALL
-- 7. Uncategorized Power (special mapping for 'powerUncategorizedUw')
SELECT 'powerUncategorizedUw' AS metric_name, SUM(power_uw) AS value
FROM _androidx_power_mapped
WHERE category_name = 'Uncategorized';
