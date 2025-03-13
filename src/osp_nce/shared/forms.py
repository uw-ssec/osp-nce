import json
from importlib.resources import files
from io import BytesIO

from PyPDF2 import PdfReader, PdfWriter


class FillableForm:
    """
    A class to represent a fillable PDF form to enable structured autofilling.

    This class holds a dictionary that defines each fillable field's display name, internal PDF
    name, helper text, and current value, along with the PDF template and current state of the PDF.
    To generate a form_dict, you will have to inspect the Form you wish to use as a template
    (we used PyPDF2).
    """

    FORM_DICT_FIELD_ATTRIBUTES = (
        "display_name",
        "internal_name",
        "helper_text",
        "value",
        "notes",
    )

    def __init__(self, pdf_template_path: str | None, form_dict: dict) -> None:
        """
        Initialize a `FillableForm` object.

        Args:
            pdf_template_path (str): The file path to the PDF template.
            form_dict (dict): A dictionary representing the form fields. For each key,
                a nested dictionary is expected with the following structure:

                form_dict[key] = {
                    "display_name": str,    # The field name to be displayed on the form
                    "internal_name": str,   # The internal name used by the PDF for the field
                    "helper_text": str,     # Additional helper text for the field
                    "value": any,           # The current value of the field
                    "notes": str            # Notes for autofiller use
                }

        Raises:
            ValueError: If form_dict is not a dictionary of the specified structure.
        """
        if pdf_template_path:
            with open(pdf_template_path, "rb") as pdf_file:
                pdf_template = PdfReader(pdf_file)
                curr_pdf = PdfWriter()
                for page in pdf_template.pages:
                    curr_pdf.add_page(page)
        else:
            pdf_template = None
            curr_pdf = None

        # Store the template, writer, and form dictionary
        self.pdf_template = pdf_template
        self.curr_pdf = curr_pdf
        self.form_dict = form_dict

        # Validate form_dict structure
        if not isinstance(self.form_dict, dict):
            raise ValueError("form_dict must be a dictionary")
        for key, pdf_field in self.form_dict.items():
            if not isinstance(pdf_field, dict):
                raise ValueError(f"Value for key '{key}' must be a dictionary.")
            if "display_name" not in pdf_field or not isinstance(pdf_field["display_name"], str):
                raise ValueError(f"Key '{key}' must contain a 'display_name' of type str.")
            if "internal_name" not in pdf_field or not isinstance(pdf_field["internal_name"], str):
                raise ValueError(f"Key '{key}' must contain an 'internal_name' of type str.")
            if "helper_text" not in pdf_field or not isinstance(pdf_field["helper_text"], str):
                raise ValueError(f"Key '{key}' must contain a 'helper_text' of type str.")
            if "value" not in pdf_field:
                raise ValueError(f"Key '{key}' must contain an initial 'value'.")
            if "notes" not in pdf_field or not isinstance(pdf_field["notes"], str):
                raise ValueError(f"Key '{key}' must contain 'notes' of type str.")

    def update_fields(self, updates: dict[dict]) -> None:
        """
        Update the values of the fields in both the form dictionary and the PDF.

        Args:
            updates (dict[dict]): A dictionary mapping existing keys in `self.form_dict` to new
                values of the corresponding field attributes. These values must belong to
                self.FORM_DICT_FIELD_ATTRIBUTES

        Raises:
            TypeError: If updates is not a dictionary of dictionaries.
            ValueError: If any provided key does not exist in the form_dict.
            ValueError: If any update is to a non-existent attribute
        """
        if not isinstance(updates, dict) or any(
            not isinstance(item, dict) for item in updates.values()
        ):
            print(updates)
            raise TypeError("`updates` must be a dictionary of dictionaries")
        if any(key not in self.form_dict for key in updates):
            raise ValueError(
                "One or more keys in `new_vals` are not present in the `FillableForm`."
            )
        for key, updated_field in updates.items():
            if any([att not in self.FORM_DICT_FIELD_ATTRIBUTES for att in updated_field]):
                raise ValueError(f"One or more updates for key {key} were for invalid attributes.")

        # Update the internal form_dict
        for key, updated_field in updates.items():
            for attribute_to_update in updated_field:
                self.form_dict[key][attribute_to_update] = updated_field[attribute_to_update]

        # Update the PDF with the new values
        for page in self.curr_pdf.pages:
            for key, field in self.form_dict.items():
                internal_name = field["internal_name"]
                if key in updates:
                    new_val = updates[key].get("value", "")
                    if new_val:
                        self.curr_pdf.update_page_form_field_values(page, {internal_name: new_val})

    def to_bytes(self) -> bytes:
        """
        Generate and return the current state of the PDF form as raw bytes.
        """
        if self.curr_pdf is None:
            raise ValueError("Cannot generate bytes. The `FillableForm` has no `curr_pdf`.")

        pdf_bytes = BytesIO()
        self.curr_pdf.write(pdf_bytes)
        pdf_bytes.seek(0)
        return pdf_bytes.getvalue()

    def to_dict(self) -> dict:
        """
        Return the internal form dictionary.

        Returns:
            dict: The internal dictionary representing the form. Takes the form:

                form_dict[key] = {
                    "display_name": str,    # The field name to be displayed on the form
                    "internal_name": str,   # The internal name used by the PDF for the field
                    "helper_text": str,     # Additional helper text for the field
                    "value": any            # The current value of the field
                    "notes":
                }
        """
        return self.form_dict

    def to_json_string(self) -> str:
        """
        Return the internal form dictionary as a JSON string.

        Returns:
            str: JSON string of all 17 results, formatted as dictionaries of the
                form {"val": str, "notes": str}.
        """
        return json.dumps(self.form_dict)

    def get_concatenated_notes(self, fields_to_exclude: list[str]) -> str:
        """
        Concatenate the field notes and return them as a single formatted string.

        Args:
            fields_to_exclude (list[str]): A list of keys for fields to exclude from notes
                concatenation.

        Returns:
            str: Concatenated notes from all fields.
        """
        notes = []
        for key, field in self.form_dict.items():
            if key in fields_to_exclude:
                continue
            notes.append(f"{field['display_name']}: {field['notes']}")

        return "\n\n".join(notes)


class ExtensionReviewMatrix(FillableForm):
    """
    A specialized form extending `FillableForm` to represent an OSP Extension Review Matrix.

    This class automatically loads its own PDF template and JSON form dictionary from package data,
    making it ready to be filled and used.
    """

    def __init__(self) -> None:
        """
        Initialize the `ExtensionReviewMatrix` as a `FillableFrom` from the following:
            - The PDF template (extension_review_matrix.pdf).
            - The JSON form dictionary (extension_review_matrix_fillable_form.json).
        """
        erm_template_path = files("osp_nce.shared.templates").joinpath(
            "extension_review_matrix.pdf"
        )
        erm_form_dict_template = files("osp_nce.shared.templates").joinpath(
            "extension_review_matrix_fillable_form.json"
        )

        with open(erm_form_dict_template, "r") as json_template:
            erm_form_dict = json.load(json_template)

        super().__init__(erm_template_path, erm_form_dict)
