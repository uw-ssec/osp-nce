/*
Should return an empty result set if mods and awards are 1-1.
*/
WITH
    grouped_data AS (
        SELECT
            displayIdentifier,
            COUNT(DISTINCT WorkdayAwardNumber) AS awrd_cnt
        FROM
            RADDB.UW.vAwardMOdificationRequest
        GROUP BY
            displayIdentifier
    )
SELECT
    *
FROM
    grouped_data
WHERE
    awrd_cnt > 1