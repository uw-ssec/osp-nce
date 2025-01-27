/*
Pull a fixed cost terms flag from the EDW for award lines under the award_id.

Ideally, this data could be added to the vAwardLine view in RAD. Querying the
EDW in our end product would not be ideal.
*/
SELECT
    AwardLineName,
    AwardLineType
FROM
    WDFinDataMart.sec.dimAwardLine
WHERE
    AwardLineName LIKE '%' + %(award_num)s + '%';
;