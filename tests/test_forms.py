import json
import pytest
from importlib.resources import files
from io import BytesIO
from pathlib import Path

from PyPDF2 import PdfWriter
from unittest.mock import patch


from osp_nce.shared.forms import FillableForm, ExtensionReviewMatrix


@pytest.fixture
def test_pdf_template(tmp_path) -> Path:
    """
    Create a temporary PDF file for testing FillableForm.

    This file won't have real form fields, but we can still use it to test basic
    reading/writing behavior.
    """
    pdf_path = tmp_path / "sample.pdf"
    pdf_writer = PdfWriter()
    pdf_writer.add_blank_page(width=72, height=72)  # 1"x1" blank page
    with open(pdf_path, "wb") as f:
        pdf_writer.write(f)
    return pdf_path


@pytest.fixture
def valid_form_dict():
    """
    Provide a minimal valid form_dict for testing FillableForm.
    """
    return {
        "test_key": {
            "display_name": "Test Field 1",
            "internal_name": "test_field_internal_name",
            "helper_text": "Help text for Test Field 1",
            "value": "foo",
            "notes": "bar",
        },
    }


@pytest.fixture
def test_erm():
    """
    Create an empty ExtensionReviewMatrix for testing the subclass.
    """
    return ExtensionReviewMatrix()


def test_fillable_form_init_success(test_pdf_template, valid_form_dict):
    """
    Test successful initialization of a FillableForm with valid inputs.
    """
    form = FillableForm(str(test_pdf_template), valid_form_dict)
    assert form.pdf_template is not None
    assert form.curr_pdf is not None
    assert form.form_dict == valid_form_dict


def test_fillable_form_init_non_dict_form_dict(test_pdf_template):
    """
    Test that initializing FillableForm with a non-dict form_dict raises ValueError.
    """
    with pytest.raises(ValueError) as excinfo:
        FillableForm(str(test_pdf_template), "not_a_dict")
    assert "must be a dictionary" in str(excinfo.value)


def test_fillable_form_init_missing_keys(test_pdf_template):
    """
    Test that missing required keys in form_dict fields raises ValueError.
    """
    invalid_dict = {
        "field_key_1": {
            # "display_name": "Field 1",  # Missing on purpose
            "internal_name": "InternalField1",
            "helper_text": "Help text",
            "value": "Value",
        }
    }
    with pytest.raises(ValueError) as excinfo:
        FillableForm(str(test_pdf_template), invalid_dict)
    assert "must contain a 'display_name'" in str(excinfo.value)


def test_erm_update_fields_valid(test_erm):
    """
    Test that update_fields properly updates both the internal dictionary and

    the PDF (to the extent we can verify without real form fields).
    """
    new_values = {"pi_name": {"value": "John Johnson"}, "mod_id": {"value": "MOD12345"}}
    test_erm.update_fields(new_values)

    # Check internal dictionary updated
    assert test_erm.form_dict["pi_name"]["value"] == "John Johnson"
    assert test_erm.form_dict["mod_id"]["value"] == "MOD12345"


def test_erm_update_fields_invalid_key(test_erm):
    """
    Test that providing a non-existent key in update_fields raises a ValueError.
    """
    new_values = {"bad_key": {"value": "Should Fail"}}
    with pytest.raises(ValueError) as excinfo:
        test_erm.update_fields(new_values)
    assert "One or more keys in `new_vals` are not present" in str(excinfo.value)


def test_erm_update_fields_non_dict(test_erm):
    """
    Test that providing a non-dict argument to update_fields raises a TypeError.
    """
    with pytest.raises(TypeError) as excinfo:
        test_erm.update_fields("not_a_dict")
    assert "must be a dictionary" in str(excinfo.value)


# TODO: Add more tests here, checking updates/writes involving curr_pdf
