/*
There are duplicate records in RADDB.UW.vAwardModificationRequest.

Following up on any of these modifications, shows the records seem mostly the 
same.
*/
-- Get rows that have mod ids appearing for the 2nd+ time
WITH
    partitioned_data AS (
        SELECT
            *,
            ROW_NUMBER() OVER (
                PARTITION BY
                    displayIdentifier
                ORDER BY
                    RADAwardModificationRequestKey
            ) AS row_num
        FROM
            RADDB.UW.vAwardModificationRequest
    )
SELECT
    *
FROM
    partitioned_data
WHERE
    row_num != 1
;

-- Follow up on an example mod
SELECT
    *
FROM
    RADDB.UW.vAwardModificationRequest
WHERE
    displayIdentifier = 'MOD43264'