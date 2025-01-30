import os
import json
import logging

import pandas as pd
import numpy as np

from libs.sharepoint_connector import SharepointConnector
from libs.sql_connector import SQLConnector

# Setup logging
logger = logging.getLogger(__name__)


class ERMAutofiller:
    """
    Autofiller to run queries and apply business logic to fill the ERM form.

    During initialization, the autofiller queries the RAD database and pulls and 
    processes the extension forms from the Sharepoint.

    Attributes:
        df_rad (pandas.DataFrame): DataFrame combining a single row with data
            from RAD pertaining to the mod.
        answers (dict): Dictionary that stores the output of all 17
            business-logic methods, keyed by "ri1", "ri2", ..., "ri17".
    """

    # Sharepoint short link to extension forms excel file
    SHORT_LINK = os.getenv("EXTENSION_FORMS_SHORT_LINK")

    # Path to RAD query
    RAD_QUERY_FILE = "./sql/nonprod_rad.sql"

    # Shared constants and flags
    NA_FLAG = "AUTOMATED RESPONSE CURRENTLY UNAVAILABLE"
    IN_YES = "Y"
    IN_NO = "N"
    OUT_YES = "YES"
    OUT_NO = "NO"

    def __init__(
        self,
        mod_id,
        rad_connector: SQLConnector,
        sharepoint_connector: SharepointConnector,
    ):
        """
        Initialize the autofiller by querying/cleaning RAD and Sharepoint data.

        Args:
            mod_id (str): The identifier in SAGE of the modification request
                to review.
            rad_connector (SQLConnector): Initialized SQLConnector object for
                connecting to and querying RAD.
            sharepoint_connector (SharepointConnector): Intialized
                SharepointConnector object for pulling the extension forms.
        """
        # Query RAD
        df_rad = rad_connector.query_from_file(
            self.RAD_QUERY_FILE, params={"mod_id": mod_id}
        )

        # Pull extension forms from sharepoint and query for the relevant mod
        df_sharepoint = (
            sharepoint_connector.read_extension_forms_from_short_link(
                self.SHORT_LINK
            )
        )
        df_sharepoint_clean = self.process_extension_forms(
            df_sharepoint, df_rad.loc[0, "AwardNumber"]
        )

        if df_rad.empty or df_sharepoint_clean.empty:
            raise ValueError(
                f"No matches found for mod request {mod_id}. RAD result set empty: {df_rad.empty}. Extensions result set empty: {df_sharepoint_clean.empty}"
            )

        # Assign isntance attributes
        self.df_rad = df_rad
        self.df_sharepoint = df_sharepoint_clean
        self.mod_id = mod_id
        self.award_number = df_rad["AwardNumber"]
        self.answers = {}  # autofill() will store the review item results here

    def process_extension_forms(self, df_sharepoint, award_number):
        """
        Filter the extension forms to the relevant mod by award_number and ID.

        Args:
            df_sharepoint (pd.DataFrame): DataFrame containing extension froms
                from Sharepoint.
            award_number (str): The award number to match against.

        Returns:
            pd.DataFrame: A single-row DataFrame containing the highest ID that
                matches the award.
        """
        # Filter to rows where UWAwardNumber contains the award_number
        df_filter = df_sharepoint.loc[
            df_sharepoint["UWAwardNumber"].str.contains(award_number, na=False)
        ].copy()

        # If nothing matched, return an empty DataFrame
        if df_filter.empty:
            return df_filter

        # Get the most recent modification
        max_id = df_filter["ID"].max()
        df_filter = df_filter.loc[df_filter["ID"] == max_id]

        # Standardize the award number and return the filtered data
        df_filter["UWAwardNumber"] = award_number
        return df_filter.reset_index()

    def autofill(self):
        """
        Run all 17 business-logic methods in sequence and store the results.

        Each output is stored in the `self.answers` dictionary under the
        keys "ri1", "ri2", ..., "ri17".

        Returns:
            dict: A dictionary of all 17 results, each of which is of the form
                {"val": str, "notes": str}.
        """
        self.answers["pi_name"] = {"val": self.df_rad.loc[0, "pi_name"], "notes": ""}
        self.answers["mod_id"] = {"val": self.mod_id, "notes": ""}
        self.answers["ri1"] = self.ri1()
        self.answers["ri2"] = self.ri2()
        self.answers["ri3"] = self.ri3()
        self.answers["ri4"] = self.ri4()
        self.answers["ri5"] = self.ri5()
        self.answers["ri6"] = self.ri6()
        self.answers["ri7"] = self.ri7()
        self.answers["ri8"] = self.ri8()
        self.answers["ri9"] = self.ri9()
        self.answers["ri10"] = self.ri10()
        self.answers["ri11"] = self.ri11()
        self.answers["ri12"] = self.ri12()
        self.answers["ri13"] = self.ri13()
        self.answers["ri14"] = self.ri14()
        self.answers["ri15"] = self.ri15()
        self.answers["ri16"] = self.ri16()
        self.answers["ri17"] = self.ri17()
        self.answers["review_notes"] = {"val": "", "notes": ""}
        return self.answers

    def to_json(self) -> str:
        """
        Converts the `answers` dictionary to a JSON string.

        Returns:
            str: JSON string of all 17 results, formatted as dictionaries of the
                form {"val": str, "notes": str}.
        """
        return json.dumps(self.answers)

    # ------------------------------------------------------------------------
    # Helper Methods
    # ------------------------------------------------------------------------
    def _is_yes(self, db_yes_no: str) -> str:
        """
        Translates a database-encoded "Y"/"N" into "YES"/"NO".

        Args:
            db_yes_no (str): Database value "Y" or "N".

        Returns:
            str: "YES" if input is "Y", "NO" if input is "N".

        Raises:
            ValueError: If db_yes_no is not recognized.
        """
        if isinstance(db_yes_no, str) and db_yes_no in [
            self.IN_YES,
            self.IN_NO,
        ]:
            return self.OUT_YES if db_yes_no == self.IN_YES else self.OUT_NO
        else:
            logger.error("Unexpected input: expected 'Y' or 'N'")
            raise ValueError("Unexpected input: expected 'Y' or 'N'")

    def _tf_to_yn(self, condition: bool) -> str:
        """
        Converts a boolean condition to "YES"/"NO".

        Args:
            condition (bool): The boolean value to interpret.

        Returns:
            str: "YES" if condition is True, "NO" otherwise.

        Raises:
            TypeError: If the input is not a boolean.
        """
        if isinstance(condition, (bool, np.bool_)):
            return self.OUT_YES if condition else self.OUT_NO
        else:
            raise TypeError(
                f"Expected boolean input, got {type(condition)} instead"
            )

    # ------------------------------------------------------------------------
    # Individual Business Logic Methods (RI0 - RI17)
    # ------------------------------------------------------------------------
    def ri1(self) -> dict:
        """
        Check that Significant Financial Interest disclosures are current.

        Not possible with current data sources, so we return NA.

        Returns:
            dict:
                {
                    "val": NA_FLAG,
                    "notes": "SFI current not possible with current data."
                }
        """
        return {
            "val": self.NA_FLAG,
            "notes": "SFI current not possible with current data.",
        }

    def ri2(self) -> dict:
        """
        Compute the remaining award balance and return it as a formatted string.

        The balance calculation is provisional, as the actual balance must be
        calculated using the Total Authorized Amount and Total Expenditures, 
        which we do not yet have access to.

        Returns:
            dict:
                {
                    "val": str,  # e.g., "$10000.00"
                    "notes": "Calculated as Total Authorized minus Billed to Date."
                }
        """
        authorized_amount = self.df_rad.loc[0, "AuthorizedAmount"]
        billed_to_date_amount = self.df_rad.loc[0, "BilledToDateAmount"]
        balance = authorized_amount - billed_to_date_amount
        return {
            "val": f"${balance:.2f}",
            "notes": "Calculated as Total Authorized minus Billed to Date.",
        }

    def ri3(self) -> dict:
        """
        Determines whether the award is in deficit (has a negative balance).

        The balance calculation is provisional, as the actual balance must be
        calculated using the Total Authorized Amount and Total Expenditures, 
        which we do not yet have access to.

        Returns:
            dict:
                {
                    "val": "YES" or "NO",
                    "notes": "YES if Billed To Date  > Total Authorized Amount."
                }
        """
        authorized_amount = self.df_rad.loc[0, "AuthorizedAmount"]
        billed_to_date_amt = self.df_rad.loc[0, "BilledToDateAmount"]
        balance_negative = (authorized_amount - billed_to_date_amt) < 0
        return {
            "val": self._tf_to_yn(balance_negative),
            "notes": "YES if Billed to Date  > Total Authorized Amount.",
        }

    def ri4(self) -> dict:
        """
        Check if the Award Balance is >= 25% of the Total Authorized Amount.

        The balance calculation is provisional, as the actual balance must be
        calculated using the Total Authorized Amount and Total Expenditures, 
        which we do not yet have access to.

        Returns:
            dict:
                {
                    "val": "YES" or "NO",
                    "notes": "Award balance / Total Authorized Amount >= 0.25."
                }
        """
        authorized_amount = self.df_rad.loc[0, "AuthorizedAmount"]
        billed_to_date_amt = self.df_rad.loc[0, "BilledToDateAmount"]
        balance = authorized_amount - billed_to_date_amt
        balance_p = 100 * (balance / authorized_amount)
        return {
            "val": self._tf_to_yn((balance_p >= 25)),
            "notes": f"Extension form indicated answer is: {self.df_sharepoint.loc[0, "IsRemainingBalanceMoreThan25Percent"]}. Computed balance was {balance_p}% of total, with explanation {self.df_sharepoint.loc[0, "ExplanationForRemainingBalance"]}",
        }

    def ri5(self) -> dict:
        """
        Indicate if specific Award lines were listed, or extend all.

        Not possible with current data sources, so we return NA.

        Returns:
            dict:
                {
                    "val": NA_FLAG,
                    "notes": ""
                }
        """
        return {
            "val": self.NA_FLAG,
            "notes": "",
        }

    def ri6(self) -> dict:
        """
        Indicate if the request is a temporary internal extension request.

        Returns:
            dict:
                {
                    "val": "YES" or "NO",
                    "notes": "Answer pulled from Extension Form data"
                }
        """
        return {
            "val": self._tf_to_yn(self.df_sharepoint.loc[0, "isTemporaryExtensionRequest"] == "Yes"),
            "notes": "Answer pulled from Extension Form data",
        }

    def ri7(self) -> dict:
        """
        Indicate if there is new cost share in the mod.

        Returns:
            dict:
                {
                    "val": "YES" or "NO",
                    "notes": "Answer pulled from Extension Form data"
                }
        """
        return {
            "val": self._tf_to_yn(self.df_sharepoint.loc[0, "isNewCostShare"] == "Yes"),
            "notes": "Answer pulled from Extension Form data",
        }

    def ri8(self) -> dict:
        """
        Indicate if Human Subjects are involved.

        Returns:
            dict:
                {
                    "val": "YES" or "NO",
                    "notes": "Based on EGC1 and Extension form data"
                }
        """
        is_human_subjects_rad = self.df_rad.loc[0, "isHumanSubjects"]
        is_human_subjects_ext = self.df_sharepoint.loc[0, "ContinuingHumanSubjectsResearch"]
        return {"val": self._tf_to_yn(is_human_subjects_ext == "Yes"), "notes": "Based on EGC1 and Extension form data"}

    def ri9(self) -> dict:
        """
        Determines whether Animal Use is involved.

        Returns:
            dict:
                {
                    "val": "YES" or "NO",
                    "notes": "Based on EGC1 and Extension Form data."
                }
        """
        is_animal_use_rad = self.df_rad.loc[0, "isAnimalUse"]
        is_animal_use_ext = self.df_sharepoint.loc[0, "AnimalResearchDone"]
        return {"val": self._tf_to_yn(is_animal_use_ext == "Yes"), "notes": "Based on EGC1 and Extension form data"}

    def ri10(self) -> dict:
        """
        Indicate if prior sponsor approval is required for extension.
        
        Not possible with current data sources, so we return NA.

        Returns:
            dict:
                {
                    "val": NA_FLAG,
                    "notes": "Placeholder for prior approval logic."
                }
        """
        return {
            "val": self.NA_FLAG,
            "notes": "",
        }

    def ri11(self) -> dict:
        """
        Determines whether the project has been previously extended.

        Not yet implemented, so we return NA.

        Returns:
            dict:
                {
                    "val": NA_FLAG,
                    "notes": "Not yet implemented."
                }
        """
        nih_second_plus = self.df_sharepoint.loc[0, "isNIH2PlusExtension"]
        return {
            "val": self._tf_to_yn(nih_second_plus == "Yes"),
            "notes": "Answer pulled from Extension Form data.",
        }

    def ri12(self) -> dict:
        """
        Indicate if extension request is within the sponsor's timeframe.

        The balance calculation is provisional, as the actual balance must be
        calculated using the Total Authorized Amount and Total Expenditures, 
        which we do not yet have access to.

        Returns:
            dict:
                {
                    "val": "YES" or "NO",
                    "notes": ""
                }
        """
        return {
            "val": self.NA_FLAG,
            "notes": "",
        }

    def ri13(self) -> dict:
        """
        Indicate if this is a federal contract.

        "YES" if sponsor_entity_type == "Federal Government" AND project_type == "Contract".

        Returns:
            dict:
                {
                    "val": "YES" or "NO",
                    "notes": "Use Prime Sponsor and Project Type to indicate."
                }
        """
        sponsor_entity_type = self.df_rad.loc[0, "PrimeSponsorFECDMEntityType"]
        project_type = self.df_rad.loc[0, "projectType"]
        is_federal_contract = (
            sponsor_entity_type == "Federal Government"
        ) and (project_type == "Contract")
        return {
            "val": self._tf_to_yn(is_federal_contract),
            "notes": "YES if Prime Sponsor is Federal Government & project_type is Contract.",
        }

    def ri14(self) -> dict:
        """
        Indicate if the sponsor includes e-verify.

        Not possible with current data sources, so we return NA.

        Returns:
            dict:
                {
                    "val": NA_FLAG,
                    "notes": "Not possible with current data sources."
                }
        """
        return {
            "val": self.NA_FLAG,
            "notes": "",
        }

    def ri15(self) -> dict:
        """
        Placeholder for logic regarding fixed price terms.

        Found in the EDW, but not in RAD.

        Returns:
            dict:
                {
                    "val": NA_FLAG,
                    "notes": "Found in EDW, but not in RAD"
                }
        """
        return {
            "val": self.NA_FLAG,
            "notes": "",
        }

    def ri16(self) -> dict:
        """
        Checks if the award is fully paid (no outstanding payments).

        The open_amount calculation is provisional. In practice, reviewers
        answer this question by checking the TotalOpen amaount in the award line
        view of the workday award portal. This seems to be a function of the 
        BilledToDate and Receipt amounts in the award line view. We currently do
        not have access to the Receipt amount. 

        Returns:
            dict:
                {
                    "val": "YES" or "NO",
                    "notes": "Provisional calc: Total Authorized - Billed to Date."
                }
        """
        authorized_amount = self.df_rad.loc[0, "AuthorizedAmount"]
        billed_to_date_amt = self.df_rad.loc[0, "BilledToDateAmount"]
        balance = authorized_amount - billed_to_date_amt
        return {
            "val": self._tf_to_yn(balance == 0),
            "notes": "Provisional calc: Total Authorized - Billed to Date.",
        }

    def ri17(self) -> dict:
        """
        Indicate if all deliverables have been submitted.

        Returns:
            dict:
                {
                    "val": "YES" or "NO,
                    "notes": ""
                }
        """
        all_deliverables_met = self.df_sharepoint.loc[0, "allDeliverablesSubmitted"]
        return {
            "val": self._tf_to_yn(all_deliverables_met == "Yes"),
            "notes": "Pulled from Extensions Form",
        }
