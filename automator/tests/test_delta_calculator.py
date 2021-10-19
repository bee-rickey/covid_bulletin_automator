"""
Test out delta calculator logic
"""
import io
import sys
sys.path.insert(0, '../')
from unittest import mock
import pytest
import requests_mock
from delta_calculator import DeltaCalculator


@pytest.fixture
def get_delta_calculator():
    mock_open = mock.mock_open(read_data='Himachal Pradesh, Sirmour, Sirmaur\n' \
                                         'Himachal Pradesh, L & Spiti   , Lahaul and Spiti\n'
                                         'West Bengal, Cooch Behar_modified, Cooch Behar')
    with requests_mock.Mocker() as mock_url:
        text = "header to be ignored,\n" \
               "707,WB,West Bengal,WB_Birbhum,Birbhum,40000,129,39000,200,0,8,-1,9,0,,\n\
            708,WB,West Bengal,WB_Cooch Behar,Cooch Behar,27974,533,27345,95,0,35,-3,38,0,,\n\
            709,WB,West Bengal,WB_Dakshin Dinajpur,Dakshin Dinajpur,16991,111,16712,168,0,15,8,7,0,,\n"

        with mock.patch('delta_calculator.open', mock_open):
            mock_url.get("https://data.covid19india.org/csv/latest/district_wise.csv", text=text)
            delta_calculator = DeltaCalculator()
            return delta_calculator


def test_build_json(get_delta_calculator):
    """
    Test url data formatting
    :return:
    """
    assert get_delta_calculator.covid_dashboard_data['West Bengal']
    assert get_delta_calculator.covid_dashboard_data['West Bengal']['state_code'] == "WB"

    district_details = \
        get_delta_calculator.covid_dashboard_data['West Bengal']['district_data']['Cooch Behar']

    assert district_details['confirmed'] == 27974
    assert district_details['recovered'] == 27345
    assert district_details['migrated_other'] == 0

    with pytest.raises(KeyError):
        get_delta_calculator.covid_dashboard_data['West Bengal']['district_data']['Kolkata']
    with pytest.raises(KeyError):
        get_delta_calculator.covid_dashboard_data['Uttar Pradesh']


def test_load_meta_data(get_delta_calculator):
    """
    Test load_meta_data with both positive and negative values
    :return:
    """

    assert get_delta_calculator.name_mapping['Himachal Pradesh']['Sirmour'] == 'Sirmaur'
    assert get_delta_calculator.name_mapping['Himachal Pradesh']['L & Spiti'] == 'Lahaul and Spiti'
    with pytest.raises(KeyError) as error:
        get_delta_calculator.name_mapping['Uttar Pradesh']


def test_print_deltas(get_delta_calculator):
    captured_output = io.StringIO()  # Create StringIO object
    sys.stdout = captured_output

    bulletin_data = [
        {
            'district_name': 'Birbhum',
            'confirmed': 40005,
            'recovered': 39005,
            'deceased': 205,
            'migrated': 5,
        },
        {
            'district_name': 'Cooch Behar_modified',
            'confirmed': 27975,
            'recovered': 27345,
            'deceased': 95,
            'migrated': 0,
        },
        {
            'district_name': 'Dakshin Dinajpur',
            'confirmed': 16991,
            'recovered': 16712,
            'deceased': 168,
            'migrated': 0,
        },
        # Wrong district passed
        {
            'district_name': 'Dakshin Dinajpur Random',
            'confirmed': 16991,
            'recovered': 16712,
            'deceased': 168,
            'migrated': 0,
        }
    ]
    options = "full"
    mock_obj = mock.mock_open()
    with mock.patch('delta_calculator.open', mock_obj):
        get_delta_calculator.get_state_data_from_site(
            'West Bengal', bulletin_data, options)
        print(f"{mock_obj.call_count} ------")
        assert 4, mock_obj.call_count

    assert "Birbhum,West Bengal,WB,5,Hospitalized" in captured_output.getvalue()
    assert "Birbhum,West Bengal,WB,5,Recovered" in captured_output.getvalue()
    assert "Birbhum,West Bengal,WB,5,Deceased" in captured_output.getvalue()
    assert "Birbhum,West Bengal,WB,5,Migrated_Other" in captured_output.getvalue()
    assert "Cooch Behar,West Bengal,WB,1,Hospitalized" in captured_output.getvalue()
    assert "Cooch Behar,West Bengal,WB,0,Recovered" not in captured_output.getvalue()
    error_string = \
        "Failed to find key mapping for district: Dakshin Dinajpur Random, state: West Bengal"
    assert error_string in captured_output.getvalue()
    sys.stdout = sys.__stdout__

    # Negative scenario of wrong options passed
    captured_output = io.StringIO()  # Create StringIO object
    sys.stdout = captured_output

    bulletin_data = [
        {
            'district_name': 'Birbhum',
            'confirmed': 40005,
            'recovered': 39005,
            'deceased': 205,
            'migrated': 5,
        },
    ]
    get_delta_calculator.get_state_data_from_site(
        'West Bengal', bulletin_data, "random")

    assert "Birbhum" not in captured_output.getvalue()
    sys.stdout = sys.__stdout__
    # Wrong state passed
    with pytest.raises(KeyError):
        get_delta_calculator.get_state_data_from_site(
            'West B', bulletin_data, "random")
