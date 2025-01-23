/*
There are duplicate records in UW_rpt.vMODs, one for each cost center.
*/
WITH
    grouped_data AS (
        SELECT
            displayIdentifier,
            COUNT(DISTINCT CostCenterCode) AS cost_center_cnt
        FROM
            RADDB.UW_rpt.vMODs
        GROUP BY
            displayIdentifier
    )
SELECT
    *
FROM
    grouped_data
WHERE
    cost_center_cnt > 1