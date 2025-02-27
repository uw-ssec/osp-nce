import pytest
import pandas as pd
from unittest.mock import MagicMock

from osp_nce.backend.libs.erm_autofiller import ERMAutofiller
from osp_nce.shared.erm_form import Form

@pytest.fixture
def mock_rad_connector():
    """Fixture to mock SQLConnector."""
    mock = MagicMock()
    mock.query_from_file.return_value = pd.DataFrame(
        {
            "AwardNumber": ["12345"],
            "AuthorizedAmount": [10000.00],
            "BilledToDateAmount": [8000.00],
            "pi_name": ["John Doe"],
            "isHumanSubjects": ["Yes"],
            "isAnimalUse": ["No"],
            "PrimeSponsorFECDMEntityType": ["Federal Government"],
            "projectType": ["Contract"],
        }
    )
    return mock


@pytest.fixture
def mock_sharepoint_connector():
    """Fixture to mock SharepointConnector."""
    mock = MagicMock()
    mock.read_extension_forms_from_short_link.return_value = pd.DataFrame(
        {
            "ID": [1],
            "UWAwardNumber": ["12345"],
            "ContinuingHumanSubjectsResearch": ["Yes"],
            "AnimalResearchDone": ["No"],
            "IsRemainingBalanceMoreThan25Percent": ["Yes"],
            "ExplanationForRemainingBalance": ["Some explanation"],
            "isTemporaryExtensionRequest": ["No"],
            "isNewCostShare": ["No"],
            "allDeliverablesSubmitted": ["Yes"],
        }
    )
    return mock


def test_erm_autofiller_init(mock_rad_connector, mock_sharepoint_connector):
    """Test initialization of ERMAutofiller with mocked connectors."""
    mock_form = Form()
    autofiller = ERMAutofiller("12345", mock_form, mock_rad_connector, mock_sharepoint_connector)

    assert autofiller.mod_id == "12345"
    assert autofiller.award_number.iloc[0] == "12345"
    assert autofiller.data_rad["pi_name"]["value"] == "John Doe"
    assert autofiller.data_sharepoint["ContinuingHumanSubjectsResearch"]["value"] == "Yes"


# def test_process_extension_forms(mock_rad_connector, mock_sharepoint_connector):
#     """Test process_extension_forms filters Sharepoint data correctly."""
#     autofiller = ERMAutofiller("12345", mock_rad_connector, mock_sharepoint_connector)

#     df_result = autofiller.process_extension_forms(
#         mock_sharepoint_connector.read_extension_forms_from_short_link.return_value,
#         "12345",
#     )

#     assert not df_result.empty
#     assert df_result.loc[0, "UWAwardNumber"] == "12345"


# def test_autofill(mock_rad_connector, mock_sharepoint_connector):
#     """Test autofill method generates expected answers."""
#     autofiller = ERMAutofiller("12345", mock_rad_connector, mock_sharepoint_connector)

#     results = autofiller.autofill()

#     assert "pi_name" in results
#     assert results["pi_name"]["val"] == "John Doe"
#     assert "ri1" in results  # Should return NA_FLAG
#     assert results["ri1"]["val"] == autofiller.NA_FLAG


# def test_ri2_balance_calculation(mock_rad_connector, mock_sharepoint_connector):
#     """Test ri2 balance calculation method."""
#     autofiller = ERMAutofiller("12345", mock_rad_connector, mock_sharepoint_connector)

#     result = autofiller.ri2()
#     assert result["val"] == "$2000.00"
#     assert "Calculated as Total Authorized" in result["notes"]


# def test_ri3_deficit_check(mock_rad_connector, mock_sharepoint_connector):
#     """Test ri3 determines if the award is in deficit."""
#     autofiller = ERMAutofiller("12345", mock_rad_connector, mock_sharepoint_connector)

#     result = autofiller.ri3()
#     assert result["val"] == "NO"
#     assert "Billed to Date" in result["notes"]


# def test_ri8_human_subjects(mock_rad_connector, mock_sharepoint_connector):
#     """Test ri8 method for determining human subjects involvement."""
#     autofiller = ERMAutofiller("12345", mock_rad_connector, mock_sharepoint_connector)

#     result = autofiller.ri8()
#     assert result["val"] == "YES"
#     assert "reported human subjects" in result["notes"]


# def test_ri9_animal_use(mock_rad_connector, mock_sharepoint_connector):
#     """Test ri9 method for animal use determination."""
#     autofiller = ERMAutofiller("12345", mock_rad_connector, mock_sharepoint_connector)

#     result = autofiller.ri9()
#     assert result["val"] == "NO"
#     assert "reported animal use" in result["notes"]


# def test_to_json(mock_rad_connector, mock_sharepoint_connector):
#     """Test JSON serialization of autofill results."""
#     autofiller = ERMAutofiller("12345", mock_rad_connector, mock_sharepoint_connector)

#     autofiller.autofill()
#     json_output = autofiller.to_json()

#     assert "pi_name" in json_output
#     assert "ri1" in json_output
