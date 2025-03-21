/*
Fetch a MOD joined to award, workday, and egc1 data for ERM autofilling.

In general, we pull from the award data rather to ensure the most current
state of the award at hand. In the future we may break this out into separate 
queries for each ERM field, but for now, while things are in flux, we pull 
everything we suspect may be useful.

We also deduplicate `vAwardModificationRequest` and `vAward` to ensure only one 
record is returned per `displayIdentifier`. 
*/
WITH
    --  Rank the mods by RAD key
    numbered_mods AS (
        SELECT
            displayIdentifier,
            ModificationType,
            Status,
            WorkdayAwardNumber,
            modifiedSponsorAwardedTotal,
            sponsorHasDeadline,
            sponsorDeadlineDate,
            ---RADeGC1Key,
            RADAwardModificationRequestKey,
            ROW_NUMBER() OVER (
                PARTITION BY
                    displayIdentifier
                ORDER BY
                    RADAwardModificationRequestKey DESC
            ) AS row_num
        FROM
            RADDB.UW.vAwardModificationRequest
    ),
    -- Take the displayIdentifier with the largest RAD key
    deduplicated_mods AS (
        SELECT
            *
        FROM
            numbered_mods
        WHERE
            row_num = 1
    ),
    -- Rank the awards by RAD key
    numbered_awards AS (
        SELECT
            AwardNumber,
            RadAwardKey,
            AwardLifecycleStatus,
            AwardShortName,
            AwardDescription,
            AwardContractOwnerName,
            SponsorFECDMEntityName,
            SponsorFECDMEntityType,
            PrimeSponsorFECDMEntityName,
            PrimeSPonsorFECDMEntityType,
            BillToSponsorFECDMEntityName,
            BillToSponsorFECDMEntityType,
            AwardTotalAmount,
            AuthorizedAmount,
            BilledToDateAmount,
            AwardScheduleStartDate,
            AwardScheduleEndDate,
            ProposalID,
            ROW_NUMBER() OVER (
                PARTITION BY
                    AwardNumber
                ORDER BY
                    RadAwardKey DESC
            ) AS row_num
        FROM
            RADDB.UW.vAward
    ),
    -- Take the AwardNumber with the largest RAD key
    deduplicated_awards AS (
        SELECT
            *
        FROM
            numbered_awards
        WHERE
            row_num = 1
    ),
    -- Pivot the mod categories to avoid duplicate rows
    mod_category_pivot AS (
        SELECT
            displayIdentifier,
            MAX(CASE WHEN ModificationCategory = 'Schedule changes'          THEN 1 ELSE 0 END) AS has_schedule_changes,
            MAX(CASE WHEN ModificationCategory = 'Programmatic changes'      THEN 1 ELSE 0 END) AS has_programmatic_changes,
            MAX(CASE WHEN ModificationCategory = 'Other changes'             THEN 1 ELSE 0 END) AS has_other_changes,
            MAX(CASE WHEN ModificationCategory = 'Funding & budgeting changes' THEN 1 ELSE 0 END) AS has_funding_budgeting_changes,
            MAX(CASE WHEN ModificationCategory = 'End of award changes'      THEN 1 ELSE 0 END) AS has_end_of_award_changes
        FROM RADDB.UW.vAwardModificationRequestCategory
        GROUP BY 
            displayIdentifier
    ),
    -- Gather RAD data by joining deduplicated mods & awards + other tables
    rad_data AS (
        SELECT
            -- From mod (deduplicated)
            mod.displayIdentifier,
            mod.RADAwardModificationRequestKey,
            mod.Status AS mod_status,
            mod.WorkdayAwardNumber,
            mod.modifiedSponsorAwardedTotal,
            mod.sponsorHasDeadline,
            mod.sponsorDeadlineDate,
            -- From category
            cats.has_schedule_changes,
            cats.has_programmatic_changes,
            cats.has_other_changes,
            cats.has_funding_budgeting_changes,
            cats.has_end_of_award_changes,
            -- From award (deduplicated)
            awrd.RADAwardKey,
            awrd.AwardNumber,
            awrd.AwardLifecycleStatus,
            awrd.AwardShortName,
            awrd.AwardDescription,
            awrd.AwardContractOwnerName AS pi_name,
            awrd.SponsorFECDMEntityName,
            awrd.SponsorFECDMEntityType,
            awrd.PrimeSponsorFECDMEntityName,
            awrd.PrimeSponsorFECDMEntityType,
            awrd.BillToSponsorFECDMEntityName,
            awrd.BillToSponsorFECDMEntityType,
            awrd.AwardTotalAmount,
            awrd.AuthorizedAmount,
            awrd.BilledToDateAmount,
            awrd.AwardScheduleStartDate,
            awrd.AwardScheduleEndDate,
            -- EGC1 data
            -- egc1.applicationType AS egc1_application_type,
            -- egc1.applicationStatus AS egc1_application_status,
            --egc1.projectType,
            -- egc1.sponsoredProgramActivityType,
            -- Compliance data
            comp.isAnimalUse,
            comp.isClinicalTrial,
            comp.isHumanSubjects,
            comp.isEHS
        FROM
            deduplicated_mods mod
            LEFT JOIN mod_category_pivot cats ON mod.displayIdentifier = cats.displayIdentifier
            LEFT JOIN deduplicated_awards awrd ON mod.WorkdayAwardNumber = awrd.AwardNumber
            --LEFT JOIN RADDB.UW.vEGC1 egc1 ON awrd.ProposalID = egc1.applicationUTN
            LEFT JOIN RADDB.UW.vCompliance comp ON mod.WorkdayAwardNumber = comp.WorkdayAwardNumber
    )
    -- Final selection
SELECT
    *
FROM
    rad_data
WHERE
    displayIdentifier = %(mod_id)s