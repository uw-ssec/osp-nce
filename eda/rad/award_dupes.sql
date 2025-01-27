/*
There are duplicate records in RADDB.UW.vAward.

Following up on any of these awards, shows the records seem mostly the same. 
This seems like it could be due to updates or some other business process.
*/
-- Get rows that have award ids appearing for the 2nd+ time
WITH
    partitioned_data AS (
        SELECT
            *,
            ROW_NUMBER() OVER (
                PARTITION BY
                    AwardNumber
                ORDER BY
                    RADAwardKey
            ) AS row_num
        FROM
            RADDB.UW.vAward
    )
SELECT
    *
FROM
    partitioned_data
WHERE
    row_num != 1
;

-- Follow up on an example award
SELECT
    *
FROM
    RADDB.UW.vAward
WHERE
    AwardNumber = 'AWD-007338'
;