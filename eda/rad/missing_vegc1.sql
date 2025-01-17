/*
Count the MODs whose vEGC1s are missing and vice versa.
*/
-- Around 28k MODs with no eGC1 in the reporting schema
SELECT
    *
FROM
    RADDB.UW_rpt.vMODs mod
    LEFT JOIN RADDB.UW_rpt.vEGC1 egc1 
        ON mod.ProposalID = egc1.applicationID
WHERE
    egc1.applicationID IS NULL
;

-- Around 9.5k eGC1s with no MODs in the reporting schema
SELECT
    *
FROM
	RADDB.UW_rpt.vEGC1 egc1 
    LEFT JOIN RADDB.UW_rpt.vMODs mod
        ON mod.ProposalID = egc1.applicationID
WHERE
    mod.ProposalID IS NULL
;

-- Only 14 missing eGC1s from the non-reporting schema
SELECT
    COUNT(DISTINCT displayIdentifier)
FROM
    RADDB.UW_rpt.vMODs mod
    LEFT JOIN RADDB.UW.vEGC1 egc1 
        ON mod.ProposalID = egc1.applicationUTN
WHERE
    egc1.applicationUTN IS NULL
;