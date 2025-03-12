import logging
import os
from importlib.resources import files
from typing import Any

import numpy as np
import pandas as pd

from osp_nce.backend.libs.sharepoint_connector import SharepointConnector
from osp_nce.backend.libs.sql_connector import SQLConnector
from osp_nce.shared.forms import ExtensionReviewMatrix, FillableForm

logging.basicConfig(
    filename="autofiller.log",
    filemode="a",
    format="%(asctime)s - %(levelname)s - %(message)s",
    level=logging.ERROR,
)


class AutoFiller:
    """
    Base class for fillable PDF autofillers.
    """

    # Shared constants and flags for uniform output
    NA_FLAG = "AUTOMATED RESPONSE CURRENTLY UNAVAILABLE"
    OUT_YES = "YES"
    OUT_NO = "NO"

    def __init__(self, pdf_template_path: str | None, form_dict: dict) -> None:
        """
        Initalize a basic `AutoFiller`.

        Business logic for particular types of `FillableForm` should be written in child classes.

        Args:
            pdf_template_path (str or None): Path to the PDF to use as the `FillableForm` template.
            form_dict (dict): A dictionary representation of the PDF to use in  the `FillableForm`.
        """
        self.form = FillableForm(pdf_template_path, form_dict)

    def get_answers(self) -> dict:
        """
        Apply business logic to get "answers" to the FillableForm fields.

        This is a virtual method that expects implementations in child classes to return maps
        suitable for updating the internal `FillableForm.form_dict`:

            answers[key] = {
                "value": Any,   # The current value of the field
                "notes": str    # Notes for autofiller use
            }
        """
        return {}

    def autofill(self) -> None:
        """
        Update the state of the `FillableForm` to contain autofilled "answers" for each field.
        """
        answers = self.get_answers()
        try:
            self.form.update_fields(answers)
        except Exception as e:
            print(f"Error in filling internal form: {e}")

    def to_dict(self) -> dict:
        """
        Return the current internal dictionary of the object's `FillableForm`.
        """
        return self.form.to_dict()

    def to_json(self) -> str:
        """
        Return the current internal dictionary of the object's `FillableForm` as a JSON string.
        """
        return self.form.to_json_string()

    def _to_std_yn(self, val: Any) -> str:
        """
        Standardize common ways of indicating "yes" and "no" to `self.OUT_YES` and `self.OUT_NO`.

        Raises:
            ValueError: If `val is not recognized as an indicator.
        """
        val_string = str(val).lower()
        if val_string == "yes" or val_string == "y" or val_string == "1" or val_string == "true":
            return self.OUT_YES
        elif (
            val_string == "no"
            or val_string == "n"
            or val_string == "0"
            or val_string == "false"
            or val_string == "nan"
            or val_string == "none"
        ):
            return self.OUT_NO
        else:
            raise ValueError(f"Unexpected input: {val} is not recognized as 'YES' or 'NO'")

    def _to_tf(self, val: Any) -> bool:
        """
        Convert common ways of indicating "yes" and "no" to boolean.
        """
        std_val = self._to_std_yn(val)
        return std_val == self.OUT_YES


class ERMAutoFiller(AutoFiller):
    """
    An `AutoFiller` for the OSP Extension Review Matrix.
    """

    # RAD query path from package data
    RAD_QUERY_FILE = files("osp_nce.backend.queries").joinpath("nonprod_rad.sql")

    # Sharepoint short link (share link) to excel sheet containing OSP Extension Form responses
    SHORT_LINK = os.getenv("EXTENSION_FORMS_SHORT_LINK")

    # Default source descriptors for each dataset
    RAD_SOURCE = "REPORTING & ANALYTICS DATABASE (RAD)"
    SHAREPOINT_SOURCE = "OSP EXTENSION FORM"

    def __init__(
        self,
        mod_id: str,
        rad_connector: SQLConnector,
        sharepoint_connector: SharepointConnector,
    ) -> None:
        """
        Initializes the `ERMAutoFiller` by querying/cleaning RAD and Extension Form data.

        Args:
            mod_id (str): The identifier in SAGE of the modification request to review. For example,
                'MOD12345'
            rad_connector (SQLConnector): An initalized SQLConnector object for connecting to and
                querying RAD.
            sharepoint_connector (SharepointConnector): Initialized SharepointConnector object for
                retrieving the Extension Form responses relevant to the MOD.
        """
        df_rad = rad_connector.query_from_file(self.RAD_QUERY_FILE, params={"mod_id": mod_id})
        df_share = sharepoint_connector.read_extension_forms_from_short_link(self.SHORT_LINK)
        df_share = self._process_extension_forms(df_share, df_rad.loc[0, "AwardNumber"])

        if df_rad.empty:
            raise ValueError(f"No matches found for {mod_id} in RAD.")
        elif df_share.empty:
            raise ValueError(
                f"No matches found for {df_rad.loc[0, 'AwardNumber']} in Extension Form Responses."
            )

        self.df_rad = df_rad
        self.df_share = df_share
        self.mod_id = mod_id
        self.award_id = df_rad.loc[0, "AwardNumber"]
        self.form = ExtensionReviewMatrix()

    def _process_extension_forms(self, df_share: pd.DataFrame, award_number: str) -> pd.DataFrame:
        """
        Filter the extension form responses to those for the current MOD.

        The extension forms are not standardized, and do not always indicate the award_number. To
        identify the responses relevant to the current MOD requires extracting the ID that was
        supplied instead, inferring its type, and then querying RAD. For now we just take the most
        entry for the matching `award_number`.

        Args:
            df_share (pd.DataFrame): DataFrame containing the extension forms.
            award_number (str): The award number to filter the forms by.

        Returns:
            pd.DataFrame: Filtered DataFrame containing the relevant extension form responses.
        """
        # Filter the DataFrame by award number
        df_filter = df_share[df_share["UWAwardNumber"].str.contains(award_number, na=False)].copy()
        if df_filter.empty:
            return df_filter

        # Standardize the award number using the value from RAD
        df_filter["UWAwardNumber"] = award_number

        # Get the most recent modification using ID
        df_filter = df_filter[df_filter["ID"] == df_filter["ID"].max()]

        # return df_filter
        return df_filter.reset_index(drop=True)

    # ------------------------------------------------------------------------
    # Business Logic Methods
    # ------------------------------------------------------------------------

    def autofill(self) -> None:
        """
        Autofill the `ExtensionReviewMatrix` by running all business-logic methods.
        """
        autofill = {}
        try:
            autofill["mod_id"] = self._mod_id()
            autofill["pi_name"] = self._pi_name()
            autofill["ri1"] = self._ri1()
            autofill["ri2"] = self._ri2()
            autofill["ri3"] = self._ri3()
            autofill["ri4"] = self._ri4()
            autofill["ri5"] = self._ri5()
            autofill["ri6"] = self._ri6()
            autofill["ri7"] = self._ri7()
            autofill["ri8"] = self._ri8()
            autofill["ri9"] = self._ri9()
            autofill["ri10"] = self._ri10()
            autofill["ri11"] = self._ri11()
            autofill["ri12"] = self._ri12()
            autofill["ri13"] = self._ri13()
            autofill["ri14"] = self._ri14()
            autofill["ri15"] = self._ri15()
            autofill["ri16"] = self._ri16()
            autofill["ri17"] = self._ri17()
            self.form.update_fields(autofill)
            self._compile_review_notes()
        except Exception as e:
            logging.error(f"Error in autofill method (mod_id={self.mod_id}): {e}", exc_info=True)
            print(f"Error in autofill: {e}")

    def _na_fill(self) -> dict:
        """
        Return a default NA response if the AutoFiller cannot yet fill the field.

        Returns:
            dict:
                {"value": self.NA_FLAG, "notes": ""}
        """
        return {"value": self.NA_FLAG, "notes": ""}

    def _mod_id(self) -> dict:
        """
        Package the MOD ID for the internal `ExtensionReviewMatrix`.

        Returns:
            dict:
                {"value": str (e.g., MOD12345), "notes": ""}
        """
        return {"value": self.mod_id, "notes": ""}

    def _pi_name(self) -> dict:
        """
        Package the PI Name for the internal `ExtensionReviewMatrix`.

        Returns:
            dict: {"value": str (e.g., Doe, John), "notes": ""}
        """
        return {"value": self.df_rad.loc[0, "pi_name"], "notes": ""}

    def _ri1(self) -> dict:
        """
        Check that Significant Financial Interest (SFI) disclosures are current.

        Not possible with current data sources, so return the std NA fill.
        """
        return self._na_fill()

    def _ri2(self) -> dict:
        """
        Compute the remaining award balance and return it as a formatted string.

        The balance calculation is provisional, as the actual balance must be calculated using the
        Total Expenditures, which we do not yet have access to.

        Returns:
            dict:
                {"value": str (e.g., "$10000.00")", notes": str}
        """
        try:
            authorized_amt = float(self.df_rad.loc[0, "AuthorizedAmount"])
            billed_to_date_amt = float(self.df_rad.loc[0, "BilledToDateAmount"])
        except (KeyError, IndexError, ValueError):
            return self._na_fill()

        balance = authorized_amt - billed_to_date_amt
        return {
            "value": f"${balance:.2f}",
            "notes": (
                f"Calculated as Total Authorized (${authorized_amt:.2f}) "
                f"minus Billed to Date (${billed_to_date_amt:.2f}). "
                f"Values were obtained from {self.RAD_SOURCE}."
            ),
        }

    def _ri3(self) -> dict:
        """
        Determines whether the award is in deficit (has a negative balance).

        The balance calculation is provisional, as the actual balance is calculated using the
        Total Expenditures, which we do not yet have access to.

        Returns:
            dict:
                {"value": self.OUT_YES or self.OUT_NO, "notes": str}
        """
        try:
            authorized_amount = float(self.df_rad.loc[0, "AuthorizedAmount"])
            billed_to_date_amt = float(self.df_rad.loc[0, "BilledToDateAmount"])
        except (KeyError, IndexError, ValueError):
            return self._na_fill()

        negative_balance = (authorized_amount - billed_to_date_amt) < 0
        if negative_balance:
            notes = (
                f"Billed to Date (${billed_to_date_amt:.2f}) is greater than "
                f"Total Authorized Amount (${authorized_amount:.2f}). "
                f"Values were obtained from {self.RAD_SOURCE}."
            )
        else:
            notes = (
                f"Billed to Date (${billed_to_date_amt:.2f}) is not greater than "
                f"Total Authorized Amount (${authorized_amount:.2f}). "
                f"Values were obtained from {self.RAD_SOURCE}."
            )

        return {"value": self._to_std_yn(negative_balance), "notes": notes}

    def _ri4(self) -> dict:
        """
        Checks if the award balance is >= 25% of the total authorized amount.

        The balance calculation is provisional, as the actual balance must be calculated using the
        Total Expenditures, which we do not yet have access to.

        Returns:
            dict:
                {"value: self.OUT_YES or self.OUT_NO", "notes": str}
        """
        authorized_amt = float(self.df_rad.loc[0, "AuthorizedAmount"])
        billed_to_date_amt = float(self.df_rad.loc[0, "BilledToDateAmount"])
        balance = authorized_amt - billed_to_date_amt
        balance_p = 100 * (float(balance) / authorized_amt)
        gt_25p = balance_p >= 25

        extension_form_value = self.df_share.loc[0, "IsRemainingBalanceMoreThan25Percent"]
        explanation = self.df_share.loc[0, "ExplanationForRemainingBalance"]

        return {
            "value": self._to_std_yn(gt_25p),
            "notes": (
                f"The computed balance was {balance_p:.2f}% of the total. "
                f"This value was computed using the {self.RAD_SOURCE} and treated as definitive. "
                f"In addition, {self.SHAREPOINT_SOURCE} reports that the award balance "
                f"{'DOES' if self._to_tf(extension_form_value) else 'DOES NOT'} exceed 25% of "
                f"the Total Authorized Amount, with explanation: {explanation}."
            ),
        }

    def _ri5(self) -> dict:
        """
        Indicate if specific Award lines were listed, or extend all.

        Not possible with current data sources, so return the std NA fill.
        """
        return self._na_fill()

    def _ri6(self) -> dict:
        """
        Indicate if the request is a temporary internal extension request.

        Returns:
            dict: {"value: self.OUT_YES or self.OUT_NO", "notes": str}
        """
        try:
            is_temp_extension = self.df_share.loc[0, "isTemporaryExtensionRequest"]
        except (KeyError, IndexError, ValueError):
            return self._na_fill()

        return {
            "value": self._to_std_yn(is_temp_extension),
            "notes": f"Field value obtained from {self.SHAREPOINT_SOURCE}",
        }

    # TODO: This indicator is theoretically verifiable using RAD data, but we have not validated
    # business logic to implement this. a future version of this method could cross-reference RAD
    # to confirm the Extension Form response.
    def _ri7(self) -> dict:
        """
        Indicate if there is new cost share in the mod.

        Returns:
            dict: {"value: self.OUT_YES or self.OUT_NO", "notes": str}
        """
        try:
            is_new_cost_share = self.df_share.loc[0, "isNewCostShare"]
        except (KeyError, IndexError, ValueError):
            return self._na_fill()

        return {
            "value": self._to_std_yn(is_new_cost_share),
            "notes": f"Value was obtained from {self.SHAREPOINT_SOURCE}",
        }

    def _ri8(self) -> dict:
        """
        Indicate if Human Subjects are involved in the grant.

        Returns:
            dict: {"value: self.OUT_YES or self.OUT_NO", "notes": str}
        """
        try:
            is_human_subjects_rad = self._to_std_yn(self.df_rad.loc[0, "isHumanSubjects"])
            is_human_subjects_ext = self._to_std_yn(
                self.df_share.loc[0, "ContinuingHumanSubjectsResearch"]
            )
        except (KeyError, IndexError, ValueError):
            return self._na_fill()

        if is_human_subjects_rad == is_human_subjects_ext:
            to_report = is_human_subjects_rad
            notes = (
                f"The {self.RAD_SOURCE} and {self.SHAREPOINT_SOURCE} data match; "
                f"reported human subjects: {to_report}."
            )
        else:
            to_report = is_human_subjects_ext
            notes = (
                f"Discrepancy between {self.RAD_SOURCE} and {self.SHAREPOINT_SOURCE} data; "
                f"{self.RAD_SOURCE} reported: {is_human_subjects_rad}, "
                f"{self.SHAREPOINT_SOURCE} reported: {is_human_subjects_ext}.  "
                f"The AutoFiller response prioritizes {self.SHAREPOINT_SOURCE} data."
            )

        return {"value": to_report, "notes": notes}

    def _ri9(self) -> dict:
        """
        Indicate whether Animal Use is involved in the Grant.

        Returns:
            dict: {"value: self.OUT_YES or self.OUT_NO", "notes": str}
        """
        try:
            is_animal_use_rad = self._to_std_yn(self.df_rad.loc[0, "isAnimalUse"])
            is_animal_use_ext = self._to_std_yn(self.df_share.loc[0, "AnimalResearchDone"])
        except (KeyError, IndexError, ValueError):
            return self._na_fill()

        if is_animal_use_rad == is_animal_use_ext:
            to_report = is_animal_use_rad
            notes = (
                f"The {self.RAD_SOURCE} and {self.SHAREPOINT_SOURCE} data match; "
                f"reported animal use: {to_report}"
            )
        else:
            to_report = is_animal_use_ext
            notes = (
                f"Discrepancy between {self.RAD_SOURCE} and {self.SHAREPOINT_SOURCE} data; "
                f"{self.RAD_SOURCE} reported: {is_animal_use_rad}, "
                f"{self.SHAREPOINT_SOURCE} reported: {is_animal_use_ext}. "
                f"Reported answer uses {self.SHAREPOINT_SOURCE} data."
            )

        return {"value": to_report, "notes": notes}

    def _ri10(self) -> dict:
        """
        Indicate if prior sponsor approval is required for extension.

        Not possible with current data sources, so return the std NA fill.
        """
        return self._na_fill()

    def _ri11(self) -> dict:
        """
        Determines whether the project has been previously extended.

        Theoretically verifiable using RAD, but the logic has not yet implemented. For now, we
        indicate a previous extension only when the Extension Form reports the request is for an NIH
        2nd Plus Extension.
        """
        is_nih_second_plus = self._to_std_yn(self.df_share.loc[0, "isNIH2PlusExtension"])

        if not self._to_tf(is_nih_second_plus):
            return self._na_fill()
        else:
            return {
                "value": is_nih_second_plus,
                "notes": f"The {self.SHAREPOINT_SOURCE} reports this is a NIH 2nd Plus Extension.",
            }

    def _ri12(self) -> dict:
        """
        Indicate if the extension request is within the sponsor's timeframe.

        This may be possible with current data sources, but the logic needs to be verified, so for
        now return the std NA fill.
        """
        return self._na_fill()

    def _ri13(self) -> dict:
        """
        Indicate if this is a federal contract.

        The Prime Sponsor is used to make this determination.

        Returns:
            dict: {"value: self.OUT_YES or self.OUT_NO", "notes": str}
        """
        try:
            sponsor_entity_type = self.df_rad.loc[0, "PrimeSponsorFECDMEntityType"]
            project_type = self.df_rad.loc[0, "projectType"]
            is_federal_contract = (sponsor_entity_type == "Federal Government") and (
                project_type == "Contract"
            )
        except (KeyError, IndexError, ValueError):
            return self._na_fill()

        return {
            "value": self._to_std_yn(is_federal_contract),
            "notes": (
                f"Prime Sponsor Entity Type: {sponsor_entity_type};  "
                f"Project Type: {project_type} "
                f"As reported in {self.RAD_SOURCE}."
            ),
        }

    def _ri14(self) -> dict:
        """
        Indicate if the sponsor includes e-verify.

        Not possible with current data sources, so return the std NA fill.
        """
        return self._na_fill()

    def _ri15(self) -> dict:
        """
        Indicate whether or not the grant has fixed-price terms.

        An indicator was found for this in the EDW, but not in RAD, so we return the std NA fill.
        """
        return self._na_fill()

    def _ri16(self) -> dict:
        """
        Checks if the award is fully paid (no outstanding payments).

        The open_amount calculation is provisional. In practice, reviewers answer this question by
        checking the TotalOpen amount in the award line view of the workday award portal. This seems
        to be a function of the Billed To Date and Receipt amounts in the award line view, but we
        currently do not have access to the Receipt amount.

        Returns:
            dict: {"value: self.OUT_YES or self.OUT_NO", "notes": str}
        """
        try:
            authorized_amount = float(self.df_rad.loc[0, "AuthorizedAmount"])
            billed_to_date_amt = float(self.df_rad.loc[0, "BilledToDateAmount"])
            balance = authorized_amount - billed_to_date_amt
        except (KeyError, IndexError, ValueError):
            return self._na_fill()

        return {
            "value": self._to_std_yn(np.isclose(balance, 0)),
            "notes": (
                f"Balance: ${balance:.2f} (Total Authorized: ${authorized_amount:.2f} "
                f"minus  Billed to Date: ${billed_to_date_amt:.2f}). "
                f"Values obtained from {self.RAD_SOURCE}."
            ),
        }

    def _ri17(self) -> dict:
        """
        Indicate if all deliverables have been submitted.

        Returns:
            dict: {"value: self.OUT_YES or self.OUT_NO", "notes": str}
        """
        try:
            all_deliverables_met = self.df_share.loc[0, "allDeliverablesSubmitted"]
        except (KeyError, IndexError, ValueError):
            return self._na_fill()

        return {
            "value": self._to_std_yn(all_deliverables_met),
            "notes": f"Value obtained from {self.SHAREPOINT_SOURCE}.",
        }

    def _compile_review_notes(self) -> None:
        """
        Fill the 'review_notes' field by concatenating and formatting all Autofiller notes.
        """
        review_notes = self.form.get_concatenated_notes(
            fields_to_exclude=["pi_name", "mod_id", "review_notes"]
        )
        self.form.update_fields(
            {
                "review_notes": {
                    "value": review_notes,
                    "notes": "Concatenation of all AutoFiller notes.",
                }
            }
        )
