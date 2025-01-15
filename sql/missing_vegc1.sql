/*
Count the MODs whose vEGC1s were missing from the two vEGC1 tables 
*/
-- Around 15k missing from UW_rpt
SELECT
    COUNT(DISTINCT displayIdentifier)
FROM
    RADDB.UW_rpt.vMODs vmod
    LEFT JOIN RADDB.UW_rpt.vEGC1 vegc1 
        ON vmod.ProposalID = vegc1.applicationID
WHERE
    vegc1.applicationID IS NULL
;

-- Only 14 missing from UW
SELECT
    COUNT(DISTINCT displayIdentifier)
FROM
    RADDB.UW_rpt.vMODs vmod
    LEFT JOIN RADDB.UW.vEGC1 vegc1 
        ON vmod.ProposalID = vegc1.applicationUTN
WHERE
    vegc1.applicationUTN IS NULL
;