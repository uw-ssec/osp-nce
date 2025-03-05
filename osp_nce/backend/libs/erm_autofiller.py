import os
import json
import logging

import pandas as pd
import numpy as np

from osp_nce.backend.libs.sharepoint_connector import SharepointConnector
from osp_nce.backend.libs.sql_connector import SQLConnector
from osp_nce.shared.erm_form import Form

# Setup logging
logger = logging.getLogger(__name__)


class ERMAutofiller:
    """
    Autofiller to run queries and apply business logic to fill the ERM form.

    At initialization, the autofiller queries the RAD database and pulls and
    processes the extension forms from the Sharepoint.

    Attributes:
        df_rad (pandas.DataFrame): DataFrame combining a single row with data
            from RAD pertaining to the mod.
        answers (dict): Dictionary that stores the output of all 17
            business-logic methods, keyed by "ri1", "ri2", ..., "ri17".
            The mapping of of business logic method names and the questions they
            answer is in the `assest/abbreviations.md` file.
    """

    # Sharepoint short link to extension forms excel file
    SHORT_LINK = os.getenv("EXTENSION_FORMS_SHORT_LINK")

    # Path to RAD query
    RAD_QUERY_FILE = "./osp_nce/sql/nonprod_rad.sql"

    # Shared constants and flags
    NA_FLAG = "AUTOMATED RESPONSE CURRENTLY UNAVAILABLE"
    OUT_YES = "YES"
    OUT_NO = "NO"

    def __init__(
        self,
        mod_id: str,
        form: Form,
        rad_connector: SQLConnector,
        sharepoint_connector: SharepointConnector,
    ):
        """
        Initializes the autofiller by querying/cleaning RAD and Sharepoint data.

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
        df_sharepoint = sharepoint_connector.read_extension_forms_from_short_link(
            self.SHORT_LINK
        )

        df_sharepoint_clean = self.process_extension_forms(
            df_sharepoint, df_rad.loc[0, "AwardNumber"]
        )

        if df_rad.empty or df_sharepoint_clean.empty:
            raise ValueError(
                f"No matches found for mod request {mod_id}.\n"
                f"RAD result set empty: {df_rad.empty}.\n"
                f"Extensions result set empty: {df_sharepoint_clean.empty}"
            )

        # Assign instance attributes

        # We use dicts to track the data value AND source for each column
        # this way, we can flexible reference data sources (which may evolve) in the notes
        # and highlight any discrepancies between sources
        self.data_rad = {}

        for col in df_rad.columns:
            self.data_rad[col] = {
                "value": df_rad[col].values[0], "source": "RAD"}

        self.data_sharepoint = {}

        for col in df_sharepoint_clean.columns:
            self.data_sharepoint[col] = {
                "value": df_sharepoint_clean[col].values[0],
                "source": "Sharepoint PI request form",
            }

        self.mod_id = mod_id
        self.award_number = df_rad["AwardNumber"]
        
        self.form = form

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

        self.form.fill_item("pi_name", {
            "val": self.data_rad["pi_name"]["value"],
            "notes": "",
        })

        self.form.fill_item("mod_id", {
            "val": self.mod_id,
            "notes": "",
        })

        self.form.fill_item("ri1", self.ri1())
        self.form.fill_item("ri2", self.ri2())
        self.form.fill_item("ri3", self.ri3())
        self.form.fill_item("ri4", self.ri4())
        self.form.fill_item("ri5", self.ri5())
        self.form.fill_item("ri6", self.ri6())
        self.form.fill_item("ri7", self.ri7())
        self.form.fill_item("ri8", self.ri8())
        self.form.fill_item("ri9", self.ri9())
        self.form.fill_item("ri10", self.ri10())
        self.form.fill_item("ri11", self.ri11())
        self.form.fill_item("ri12", self.ri12())
        self.form.fill_item("ri13", self.ri13())
        self.form.fill_item("ri14", self.ri14())
        self.form.fill_item("ri15", self.ri15())
        self.form.fill_item("ri16", self.ri16())
        self.form.fill_item("ri17", self.ri17())
        self.form.fill_item("review_notes", self.get_concatenated_notes())

    def get_concatenated_notes(self) -> str:
        """
        Concatenates the notes from all the answers returned by the different methods.

        Returns:
            str: Concatenated notes from all answers, to be displayed at the bottom of the
                autofilled ERM Form.
        """
        notes_list = [
            answer["notes"]
            for answer in self.form.answers.values()
            if ("notes" in answer) and (answer["notes"] != "")
        ]
        
        return {"val": "\n".join(notes_list),
                "notes": "Concatenated notes from all answers."}

    def to_json(self) -> str:
        """
        Converts the `answers` dictionary to a JSON string.

        Returns:
            str: JSON string of all 17 results, formatted as dictionaries of the
                form {"val": str, "notes": str}.
        """
        return json.dumps(self.form.answers)

    # ------------------------------------------------------------------------
    # Helper Methods
    # ------------------------------------------------------------------------
    def _is_yes(self, val: str) -> str:
        """
        Formats indicators to strings

        Args:
            val: Value to probe.

        Returns:
            str: self.OUT_YES or self.OUT_NO

        Raises:
            ValueError: If val is not recognized.
        """
        val_string = str(val.lower())
        if (
            val_string == "yes"
            or val_string == "y"
            or val_string == "1"
            or val_string == "true"
        ):
            return self.OUT_YES
        elif (
            val_string == "no"
            or val_string == "n"
            or val_string == "0"
            or val_string == "false"
        ):
            return self.OUT_NO
        else:
            logger.error("Unexpected input: expected 'Y' or 'N'")
            raise ValueError("Unexpected input: expected 'Y' or 'N'")

    def _tf_to_yn(self, condition: bool) -> str:
        """
        Converts a boolean condition to "YES"/"NO". This is to enforce
        consistency in the output of the autofill methods.

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
                f"Expected boolean input, got {type(condition)} instead")

    # ------------------------------------------------------------------------
    # Individual Business Logic Methods (RI0 - RI17)
    # ------------------------------------------------------------------------
    def ri1(self) -> dict:
        """
        Checks that Significant Financial Interest disclosures are current.

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
            "notes": "",
        }

    def ri2(self) -> dict:
        """
        Computes the remaining award balance and return it as a formatted string.

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
        try:
            authorized_amount = float(
                self.data_rad["AuthorizedAmount"]["value"])
            billed_to_date_amt = float(
                self.data_rad["BilledToDateAmount"]["value"])
        except (KeyError, IndexError, ValueError) as e:
            logger.error(f"Error accessing or converting data: {e}")
            return {
                "val": self.NA_FLAG,
                "notes": "",
            }

        balance = authorized_amount - billed_to_date_amt
        return {
            "val": f"${balance:.2f}",
            "notes": f"Calculated as Total Authorized (${authorized_amount:.2f}) minus Billed to Date (${billed_to_date_amt:.2f}).",
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
                    "notes": explanation of billed to date and total authorized amount calculation
                }
        """
        try:
            authorized_amount = float(
                self.data_rad["AuthorizedAmount"]["value"])
            billed_to_date_amt = float(
                self.data_rad["BilledToDateAmount"]["value"])
        except (KeyError, IndexError, ValueError) as e:
            logger.error(f"Error accessing or converting data: {e}")
            return {
                "val": self.NA_FLAG,
                "notes": "",
            }

        balance_negative = (authorized_amount - billed_to_date_amt) < 0
        if balance_negative:
            notes = f"Billed to Date (${billed_to_date_amt:.2f}) is greater than Total Authorized Amount (${authorized_amount:.2f})."
        else:
            notes = f"Billed to Date (${billed_to_date_amt:.2f}) is not greater than Total Authorized Amount (${authorized_amount:.2f})."

        return {"val": self._tf_to_yn(balance_negative), "notes": notes}

    def ri4(self) -> dict:
        """
        Checks if the Award Balance is >= 25% of the Total Authorized Amount.

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
        authorized_amount = self.data_rad["AuthorizedAmount"]["value"]
        billed_to_date_amt = self.data_rad["BilledToDateAmount"]["value"]
        balance = authorized_amount - billed_to_date_amt
        balance_p = 100 * (float(balance) / authorized_amount)

        balance_percentage = balance_p >= 25
        extension_form_value = self.data_sharepoint[
            "IsRemainingBalanceMoreThan25Percent"
        ]["value"]
        explanation = self.data_sharepoint["ExplanationForRemainingBalance"]["value"]
        source = self.data_sharepoint["IsRemainingBalanceMoreThan25Percent"]["source"]

        return {
            "val": self._tf_to_yn(balance_percentage),
            "notes": f"{source} answer to whether award balance exceeds 25% of authorized amt. is: {extension_form_value}. Computed balance was {balance_p}% of total, with explanation: {explanation}",
        }

    def ri5(self) -> dict:
        """
        Indicates if specific Award lines were listed, or extend all.

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
        Indicates if the request is a temporary internal extension request.

        Returns:
            dict:
                {
                    "val": "YES" or "NO",
                    "notes": "Answer pulled from Extension Form data"
                }
        """
        try:
            is_temp_extension = self.data_sharepoint["isTemporaryExtensionRequest"][
                "value"
            ]
            source = self.data_sharepoint["isTemporaryExtensionRequest"]["source"]
        except KeyError as e:
            logger.error(f"KeyError accessing data: {e}")
            return {"val": self.NA_FLAG, "notes": ""}

        return {
            "val": self._tf_to_yn(is_temp_extension[0] == "Yes"),
            "notes": f"Source for temporary request is: {source}",
        }

    def ri7(self) -> dict:
        """
        Indicates if there is new cost share in the mod.

        Returns:
            dict:
                {
                    "val": "YES" or "NO",
                    "notes": "Answer pulled from Extension Form data"
                }

        Development note:
        This information is theoretically also accessible from RAD; we have not validated business
        logic sufficiently to implement this yet, but a future version of this method could
        cross-reference the RAD data to confirm the answer.
        """
        try:
            is_new_cost_share = self.data_sharepoint["isNewCostShare"]["value"]
            source = self.data_sharepoint["isNewCostShare"]["source"]
        except KeyError as e:
            logger.error(f"KeyError accessing data: {e}")
            return {"val": self.NA_FLAG, "notes": ""}

        return {
            "val": self._tf_to_yn(is_new_cost_share == "Yes"),
            "notes": f"New cost share source is {source}",
        }

    def ri8(self) -> dict:
        """
        Indicates if Human Subjects are involved.

        Returns:
            dict:
                {
                    "val": "YES" or "NO",
                    "notes": Reasoning based on RAD and Extension form data
                }
        """
        try:
            is_human_subjects_rad = self._is_yes(
                self.data_rad["isHumanSubjects"]["value"]
            )
            is_human_subjects_ext = self._is_yes(
                self.data_sharepoint["ContinuingHumanSubjectsResearch"]["value"]
            )
        except KeyError as e:
            logger.error(f"KeyError accessing data: {e}")
            return {"val": self.NA_FLAG, "notes": ""}

        reported_human_subjects = None

        rad_source = self.data_rad["isHumanSubjects"]["source"]
        rad_value = self.data_rad["isHumanSubjects"]["value"]
        sharepoint_source = self.data_sharepoint["ContinuingHumanSubjectsResearch"][
            "source"
        ]
        sharepoint_value = self.data_sharepoint["ContinuingHumanSubjectsResearch"][
            "value"
        ]

        if is_human_subjects_rad[0] == is_human_subjects_ext[0]:
            reported_human_subjects = self._is_yes(is_human_subjects_rad)
            notes = f"{rad_source} and {sharepoint_source} form data match; reported human subjects: {reported_human_subjects}"
        else:
            reported_human_subjects = is_human_subjects_ext
            notes = (
                f"Discrepancy between {rad_source} and {sharepoint_source} data; "
                f"{rad_source} reported: {rad_value}, "
                f"{sharepoint_source} reported: {sharepoint_value}. "
                f"\nReported answer uses {sharepoint_source} data."
            )

        return {
            "val": self._tf_to_yn(reported_human_subjects[0] == "Yes"),
            "notes": notes,
        }

    def ri9(self) -> dict:
        """
        Indicates whether Animal Use is involved.

        Returns:
            dict:
                {
                    "val": "YES" or "NO",
                    "notes": Reasoning based on RAD and Extension form data
                }
        """
        try:
            is_animal_use_rad = self._is_yes(
                self.data_rad["isAnimalUse"]["value"])
            is_animal_use_ext = self._is_yes(
                self.data_sharepoint["AnimalResearchDone"]["value"]
            )
        except KeyError as e:
            logger.error(f"KeyError accessing data: {e}")
            return {"val": self.NA_FLAG, "notes": ""}

        reported_animal_use = None

        rad_source = self.data_rad["isAnimalUse"]["source"]
        rad_value = self.data_rad["isAnimalUse"]["value"]
        sharepoint_source = self.data_sharepoint["AnimalResearchDone"]["source"]
        sharepoint_value = self.data_sharepoint["AnimalResearchDone"]["value"]
        
        print(is_animal_use_rad, is_animal_use_ext)

        if is_animal_use_rad[0] == is_animal_use_ext[0]:
            reported_animal_use = self._is_yes(is_animal_use_rad)
            notes = f"{rad_source} and {sharepoint_source} data match; reported animal use: {reported_animal_use}"
        else:
            reported_animal_use = is_animal_use_ext
            notes = (
                f"Discrepancy between {rad_source} and {sharepoint_source} data; "
                f"{rad_source} reported: {rad_value}, "
                f"{sharepoint_source} reported: {sharepoint_value}. "
                f"\nReported answer uses {sharepoint_source} data."
            )

        return {
            "val": self._tf_to_yn(reported_animal_use[0] == "Y"),
            "notes": notes,
        }

    def ri10(self) -> dict:
        """
        Indicates if prior sponsor approval is required for extension.

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
                    "notes": empty, because not yet implemented
                }
        """
        nih_second_plus = self.data_sharepoint["isNIH2PlusExtension"]["value"]
        return {
            "val": self.NA_FLAG,
            "notes": "",
        }

    def ri12(self) -> dict:
        """
        Indicates if extension request is within the sponsor's timeframe.

        The balance calculation is provisional, as the actual balance must be
        calculated using the Total Authorized Amount and Total Expenditures,
        which we do not yet have access to.

        Returns:
            dict:
                {
                    "val": "YES" or "NO",
                    "notes": empty, because not yet implemented
                }
        """
        return {
            "val": self.NA_FLAG,
            "notes": "",
        }

    def ri13(self) -> dict:
        """
        Indicates if this is a federal contract.

        "YES" if sponsor_entity_type == "Federal Government" AND project_type == "Contract".

        Returns:
            dict:
                {
                    "val": "YES" or "NO",
                    "notes": Prime Sponsor and Project Type leading to determination
                }
        """
        try:
            sponsor_entity_type = self.data_rad["PrimeSponsorFECDMEntityType"]["value"]
            project_type = self.data_rad["projectType"]["value"]
        except KeyError as e:
            logger.error(f"KeyError accessing data: {e}")
            return {"val": self.NA_FLAG, "notes": ""}

        is_federal_contract = (sponsor_entity_type == "Federal Government") and (
            project_type == "Contract"
        )

        return {
            "val": self._tf_to_yn(is_federal_contract),
            "notes": (
                f"Prime Sponsor Entity Type: {sponsor_entity_type} (source: {self.data_rad['PrimeSponsorFECDMEntityType']['source']}), "
                f"Project Type: {project_type} (source: {self.data_rad['projectType']['source']})."
            ),
        }

    def ri14(self) -> dict:
        """
        Indicates if the sponsor includes e-verify.

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
                    "notes": N/A
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
        answer this question by checking the TotalOpen amount in the award line
        view of the workday award portal. This seems to be a function of the
        BilledToDate and Receipt amounts in the award line view. We currently do
        not have access to the Receipt amount.

        Returns:
            dict:
                {
                    "val": "YES" or "NO",
                    "notes": string explaining calculation methodology
                }
        """
        try:
            authorized_amount = float(
                self.data_rad["AuthorizedAmount"]["value"])
            billed_to_date_amt = float(
                self.data_rad["BilledToDateAmount"]["value"])
        except (KeyError, IndexError, ValueError) as e:
            logger.error(f"Error accessing or converting data: {e}")
            return {
                "val": self.NA_FLAG,
                "notes": "",
            }

        balance = authorized_amount - billed_to_date_amt
        return {
            "val": self._tf_to_yn(balance == 0),
            "notes": (
                f"Provisional outstanding payments calc: Total Authorized (${authorized_amount:.2f}) "
                f"- Billed to Date (${billed_to_date_amt:.2f}) = Balance (${balance:.2f})."
            ),
        }

    def ri17(self) -> dict:
        """
        Indicate if all deliverables have been submitted.

        Returns:
            dict:
                {
                    "val": "YES" or "NO",
                    "notes": empty because not yet implemented
                }
        """
        try:
            all_deliverables_met = self.data_sharepoint["allDeliverablesSubmitted"][
                "value"
            ]
        except KeyError as e:
            logger.error(f"KeyError accessing data: {e}")
            return {"val": self.NA_FLAG, "notes": ""}

        return {
            "val": self._tf_to_yn(all_deliverables_met == "Yes"),
            "notes": f"Source for all deliverables submitted is: {self.data_sharepoint['allDeliverablesSubmitted']['source']}",
        }
