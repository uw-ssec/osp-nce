/*
Fetch a modification data joined to award and egc1 data for EDA.ABORT

Judging from my current problems with missingness, I need to touch bases with
Aron about many things
*/
WITH base_data AS (
	SELECT
		mod.displayIdentifier,
        awrd.AwardNumber,
		mod.status AS mod_status,
		mod.ProposalID,
		ripmod.ModificationCategory,
		egc1.PI_FirstName,
		egc1.PI_LastName,
        awrd.AwardShortName,
        awrd.AwardDescription,
        awrd.AwardTotalAmount,
        awrd.AuthorizedAmount,
        awrd.BilledToDateAmount,
        mod.PrimeSponsorFECDMEntityName,
        egc1.FECDMSponsorEntityType,
		mod.modifiedSponsorAwardedTotal,
		egc1.shortTitle AS egc1_short_title,
		egc1.longTitle AS egc1_long_title,
		egc1.projectType,
		egc1.applicationType AS egc1_application_type,
		egc1.applicationStatus AS egc1_application_status,
		egc1.sponsorDeadlineDate,
        egc1.isAnimalUse,
        egc1.isClinicalTrial,
        egc1.isHumanSubjects,
        egc1.isEHS
	FROM
		RADDB.UW_rpt.vMODs mod
	INNER JOIN RADDB.UW_rpt.vEGC1 egc1
		ON mod.ProposalID = egc1.applicationID
	LEFT JOIN RIPRPTDB_prod.UW.vModification ripmod
		ON mod.displayIdentifier = ripmod.displayIdentifier
	LEFT JOIN RADDB.UW.vAward awrd
		ON mod.WorkdayAwardNumber = awrd.AwardNumber
	)
SELECT
	*
FROM
	base_data
;