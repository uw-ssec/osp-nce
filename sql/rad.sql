/*
Fetch a modification joined to award and egc1 data for ERM autofilling.

Deduplicate vMODs to ensure only one record per displayIdentifier, as there is
one record per CostCenterCode involved in the MOD. Also, there is missingness in 
the UW_rpt.vEGC1 table, so we include an alternate query that uses UW.vEGC1 
instead.
*/
-- Original query using UW_rpt.vEGC1
-- WITH
-- 	deduplicated_vMODs AS (
-- 		SELECT
-- 			displayIdentifier,
-- 			status,
-- 			ProposalID,
-- 			PrimeSponsorFECDMEntityName,
-- 			modifiedSponsorAwardedTotal,
-- 			WorkdayAwardNumber,
-- 			CostCenterCode,
-- 			ROW_NUMBER() OVER (
-- 				PARTITION BY
-- 					displayIdentifier
-- 				ORDER BY
-- 					ProposalID
-- 			) AS row_num
-- 		FROM
-- 			RADDB.UW_rpt.vMODs
-- 	),
-- 	base_data AS (
-- 		SELECT
-- 			mod.displayIdentifier,
-- 			awrd.AwardNumber,
-- 			mod.status AS mod_status,
-- 			mod.ProposalID,
-- 			ripmod.ModificationCategory,
-- 			egc1.PI_FirstName,
-- 			egc1.PI_LastName,
-- 			awrd.AwardShortName,
-- 			awrd.AwardDescription,
-- 			awrd.AwardTotalAmount,
-- 			awrd.AuthorizedAmount,
-- 			awrd.BilledToDateAmount,
-- 			mod.PrimeSponsorFECDMEntityName,
-- 			egc1.FECDMSponsorEntityType,
-- 			mod.modifiedSponsorAwardedTotal,
-- 			egc1.shortTitle AS egc1_short_title,
-- 			egc1.longTitle AS egc1_long_title,
-- 			egc1.projectType,
-- 			egc1.applicationType AS egc1_application_type,
-- 			egc1.applicationStatus AS egc1_application_status,
-- 			egc1.sponsorDeadlineDate,
-- 			egc1.isAnimalUse,
-- 			egc1.isClinicalTrial,
-- 			egc1.isHumanSubjects,
-- 			egc1.isEHS
-- 		FROM
-- 			deduplicated_vMODs mod
-- 			LEFT JOIN RADDB.UW_rpt.vEGC1 egc1 
-- 				ON mod.ProposalID = egc1.applicationID
-- 			LEFT JOIN RIPRPTDB_prod.UW.vModification ripmod 
-- 				ON mod.displayIdentifier = ripmod.displayIdentifier
-- 			LEFT JOIN RADDB.UW.vAward awrd 
-- 				ON mod.WorkdayAwardNumber = awrd.AwardNumber
-- 		WHERE
-- 			mod.row_num = 1 -- Only use the first row for each displayIdentifier
-- 	)
-- SELECT
-- 	*
-- FROM
-- 	base_data
-- WHERE
-- 	displayIdentifier = :mod_id
-- ;

-- Alternative query using UW.vEGC1
WITH
	deduplicated_vMODs AS (
		SELECT
			displayIdentifier,
			status,
			ProposalID,
			PrimeSponsorFECDMEntityName,
			modifiedSponsorAwardedTotal,
			WorkdayAwardNumber,
			CostCenterCode,
			ROW_NUMBER() OVER (
				PARTITION BY
					displayIdentifier
				ORDER BY
					ProposalID
			) AS row_num
		FROM
			RADDB.UW_rpt.vMODs
	),
	base_data AS (
		SELECT
			mod.displayIdentifier,
			awrd.AwardNumber,
			mod.status AS mod_status,
			mod.ProposalID,
			ripmod.ModificationCategory,
			-- Need to get from Extension Form now
			-- egc1.PI_FirstName,
			-- egc1.PI_LastName,
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
			egc1.hasMandatoryCS,
			egc1.hasCommittedCS,
			egc1.hasAggregateCS,
			egc1.indirectCostRate,
			-- Need to get these from vCompliance now
			comp.isAnimalUse,
			comp.isClinicalTrial,
			comp.isHumanSubjects,
			comp.isEHS
		FROM
			deduplicated_vMODs mod
			LEFT JOIN RADDB.UW.vEGC1 egc1 
				ON mod.ProposalID = egc1.applicationUTN
			LEFT JOIN RIPRPTDB_prod.UW.vModification ripmod 
				ON mod.displayIdentifier = ripmod.displayIdentifier
			LEFT JOIN RADDB.UW.vAward awrd 
				ON mod.WorkdayAwardNumber = awrd.AwardNumber
			LEFT JOIN RADDB.UW.vCompliance comp
				ON egc1.RADEGC1Key = comp.RADEGC1Key
		WHERE
			mod.row_num = 1 -- Only use the first row for each displayIdentifier
	)
SELECT
	*
FROM
	base_data
WHERE
	displayIdentifier = :mod_id
;