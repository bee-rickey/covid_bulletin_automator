""""
Test out delta calculator logic
"""
import sys
import io
from unittest import mock
import pytest
import requests_mock
from automation import Automation
from automation import AutomationMeta


@pytest.fixture
def get_automation():
    mock_open \
        = mock.mock_open(read_data=
                         'Gujarat, GJ,https://gujcovid19.gujarat.gov.in/DrillDownCharts.aspx/GetDistDataForLineCovidDisrtict\n'
                         'Uttar Pradesh, UP,\n'
                         'Bihar, BR,')

    with mock.patch('automation.DeltaCalculator') as MockClass:
        instance = MockClass.return_value
        instance.load_meta_data.return_value = True
        instance.build_json.return_value = True
        # instance.get_state_data_from_site.return_value = True
        with mock.patch('automation.open', mock_open):
            automation = Automation("", "", "")
            return automation


def helper_for_districts_ocr(get_automation, state_code, file_str, expected_arg, error_array):
    captured_output = io.StringIO()
    sys.stdout = captured_output

    state_mock = mock.mock_open(read_data=file_str)

    with mock.patch("automation.open", state_mock):
        get_automation.type_of_automation = "ocr"
        eval(f"get_automation.{state_code}_get_data()")

    get_automation.delta_calculator.get_state_data_from_site.assert_called_once()
    called_argument = get_automation.delta_calculator.get_state_data_from_site.call_args[0][1]
    assert called_argument == expected_arg

    for error in error_array:
        assert error in captured_output.getvalue()
    sys.stdout = sys.__stdout__


def test_initialisation(get_automation):
    assert get_automation.meta_dictionary['Gujarat']
    assert get_automation.meta_dictionary['Gujarat'].state_name, "Gujarat"
    assert get_automation.meta_dictionary['Gujarat'].state_code, "GJ"
    assert get_automation.meta_dictionary['Gujarat'].url, \
        "https://gujcovid19.gujarat.gov.in/DrillDownCharts.aspx/GetDistDataForLineCovidDisrtict"

    print(len(get_automation.meta_dictionary['Uttar Pradesh'].url))
    assert get_automation.meta_dictionary['Uttar Pradesh']

    with pytest.raises(KeyError) as error:
        get_automation.meta_dictionary['Karnataka']


def test_ct_get_data(get_automation):
    file_str = 'Raipur,3,157893,1,30870,1,123857,154727,27,3139 | 2, 3, , 5, 6, 7, 8, 9, 10, 12\n' \
               'Rajnandgaon,1,56033,0,12733,1,42772,55505,13,515 | 2, 3, 4, 5, 6, 7, 8, 9, 10, 12\n' \
               'Balod,0,27265,0,9304,17564,26868,1,396 | 2, 3, 4, 5, 6, 8, 9, 10, 12\n' \
               'Bametara,0,19946,0,3358,0,16352,19710,0,236 | 2, 3, 4, 5, 6, 7, 8, 9, 10,  12\n'
    expected_args = [
        {'deceased': 515, 'district_name': 'Rajnandgaon', 'confirmed': 56033, 'recovered': 55505},
        {'deceased': 396, 'district_name': 'Balod', 'confirmed': 27265, 'recovered': 26868},
        {'deceased': 236, 'district_name': 'Bametara', 'confirmed': 19946, 'recovered': 19710}]

    helper_for_districts_ocr(get_automation, 'ct', file_str, expected_args, ["Issue with ['Raipur'"])


def test_ap_get_data(get_automation):
    file_str = 'Anantapur , 9 , 157673 , 68 , 156512, 1093 | 2, 3, 4, 5, 6, 7\n' \
               'Chittoor , 93 , 244940 , 1403 , 241613, 1924 | 2, 3, 4, 5, 6, 7\n' \
               'East Godavari , 178 , 292280 , 1784 , 289211, 1285 | 2, 3, 4, 5, 6, 7\n' \
               'Guntur , 91 , 176675 , 762 , 174689, 1224 | 2, 3, 4, 5, 6, 7\n' \
               'YSR Kadapa ,  115172 , 143 , 114389, 640 | 2, 3, 4, 5, 6, 7\n'

    expected_args = [{'district_name': 'Anantapur', 'confirmed': 157673, 'recovered': 156512, 'deceased': 1093},
                     {'district_name': 'Chittoor', 'confirmed': 244940, 'recovered': 241613, 'deceased': 1924},
                     {'district_name': 'East Godavari', 'confirmed': 292280, 'recovered': 289211, 'deceased': 1285},
                     {'district_name': 'Guntur', 'confirmed': 176675, 'recovered': 174689, 'deceased': 1224}
                     ]

    helper_for_districts_ocr(get_automation, 'ap', file_str, expected_args, ["Issue with ['YSR Kadapa"])


def test_ar_get_data(get_automation):
    file_str = 'Anjaw , 0 , 19843 , 19655 , 18593 , 1062 , 6 , 0 , 0 , 0 , 0 , 6 , 1053, 3 ' \
               '| 1, 2, 3, 4, 5, 6, 7, None, 10, 11, 12, 13, 14, 15\n' \
               'Papum Pare , 129 , 95364 , 95204 , 91694 , 2763 , 10 , 0 , 0 , 0 , 0 , 11 , 2744, 9 ' \
               '| 1, 2, 3, 4, 5, 6, 7, 8, 10, 11, 12, 13, 14, 15\n' \
               'Capital Complex , 351 , 270275 , 267849 , 252411 , 15438 , 10 , 0 ' \
               ', 6 , 0 , 0 , 4 , 15340, 88 | 1, 2, 3, 4, 5, 6, 7, 9, 10, 11, 12, 13, 14, 15\n' \
               'Changlang , 79780 , 78593 , 74771 , 3793 , 8 , 0 , 1 , 0 , ' \
               '1 , 6 , 3763, 22 | 1, 2, 3, 4, 5, 6, 7, 9, 10, 11, 12, 13, 14, 15'

    expected_args = [{'district_name': 'Anjaw', 'confirmed': 1062, 'recovered': 1053, 'deceased': 3},
                     {'district_name': 'Papum Pare', 'confirmed': 18201, 'recovered': 18084, 'deceased': 97}
                     ]

    helper_for_districts_ocr(get_automation, "ar", file_str, expected_args, ["Issue with ['Changlang"])


def test_or_get_data(get_automation):
    state_mock = \
        mock.mock_open(read_data=
                       '[{"intId":23848,"intDistid":344,"intCategory":null,'
                       '"vchDistrictName":"Angul","intConfirmed":43366,"intActive":151,'
                       '"intDeceased":332,"intRecovered":42883,"intOthDeceased":0,'
                       '"dtmCreatedOn":"2021-08-23 08:23:04",'
                       '"dtmReportedOn":"2021-08-23","intDistType":0},'
                       '{"intId":23849,"intDistid":346,"intCategory":null,'
                       '"vchDistrictName":"Balasore","intConfirmed":39124,"intActive":468,'
                       '"intDeceased":258,"intRecovered":38393,"intOthDeceased":5,'
                       '"dtmCreatedOn":"2021-08-23 08:23:04","dtmReportedOn":"2021-08-23","intDistType":0'
                       '}]'
                       )
    captured_output = io.StringIO()  # Create StringIO object
    sys.stdout = captured_output

    with mock.patch("automation.os.system") as os_mock:
        with mock.patch("automation.open", state_mock):
            get_automation.or_get_data()
            os_mock.assert_called_once()
            call_args = [{'district_name': 'Angul', 'confirmed': 43366, 'recovered': 42883, 'deceased': 332},
                         {'district_name': 'Balasore', 'confirmed': 39124, 'recovered': 38393, 'deceased': 263}
                         ]
            get_automation.delta_calculator.get_state_data_from_site.assert_called_once()
            get_automation.delta_calculator.get_state_data_from_site.assert_called_once_with(
                "Odisha",
                call_args,
                ''
            )
    sys.stdout = sys.__stdout__


def test_mh_get_data(get_automation):
    file_str = 'Jalgaon , 139892 , 137093 , 2708 , 32, 59 | 2, 3, 4, 5, 1, 6\n' \
               'Nandurbar , 39980 , 39028 , 947 , 3, 2 | 2, 3, 4, 5, 1, 6\n' \
               'Dhule , 46288 , 45600 , 654 , 11, 23 | 2, 3, 4, 5, 1, 6\n' \
               'Aurangabad ,  , 150175 , 4281 , 14, 585 | 2, 3, 4, 5, 1, 6\n'

    expected_args = [
        {'district_name': 'Jalgaon',
         'confirmed': 139892,
         'recovered': 137093,
         'deceased': 2708,
         'migrated': 32
         },
        {'district_name': 'Nandurbar',
         'confirmed': 39980,
         'recovered': 39028,
         'deceased': 947,
         'migrated': 3
         },
        {'district_name': 'Dhule',
         'confirmed': 46288,
         'recovered': 45600,
         'deceased': 654,
         'migrated': 11
         }
    ]

    helper_for_districts_ocr(get_automation, 'mh', file_str, expected_args, ["Issue with ['Aurangabad"])


def test_hp_get_data(get_automation):
    file_str = 'Bilaspur , 13446 , 122 , 19 , 14 , ' \
               '19 , 14 , 1355 , 13241 , 82 *, 0 | 56, 5, 6, 1, 2, 3, 4, 7, 8, 9, 11\n' \
               'Chamba , 13483 , 129 , 8 , 이 , 8 , 22 , ' \
               '1134 , 13194 , 158 **, 0 | 56, 5, 6, 1, ' \
               '2, 3, 4, 4, 7, 8, 9, 11\n' \
               'Hamirpur ,  252 , 18 , 0 , 18 , ' \
               '25 , 944 , 14834 , 260 *, 0 | 56, 5, 6, 1, 2, 3, 4, 7, 8, 9, 11\n' \
               'Kangra , 47733 , 354 , 51 , 0 , 51 , 11 , ' \
               '1421 , 46312 , 1063 ****, 0 | 56, 5, 6, 1, 2, 3, 4, 7, 8, 9, 11'

    expected_args = [
        {
            'district_name': 'Bilaspur',
            'confirmed': 13446,
            'recovered': 13241,
            'deceased': 82
        },
        {
            'district_name': 'Chamba',
            'confirmed': 13483,
            'recovered': 13194,
            'deceased': 158
        },
        {
            'district_name': 'Kangra',
            'confirmed': 47733,
            'recovered': 46312,
            'deceased': 1063
        }
    ]

    helper_for_districts_ocr(get_automation, 'hp', file_str, expected_args, ["Issue with ['Hamirpur"])


def test_ut_get_data(get_automation):
    file_str = 'Almora , 12148 , 11341 , 5 , 195, 607 | 1, 2, 3, 4, 5, 6\n' \
               'Bageshwar , 5747 , 5659 , 3 , 60, 25 | 1, 2, 3, 4, 5, 6\n' \
               'Chamoli , 12173 , 11873 , 35 , 203 | 1, 2, 3, 4, 5, 6\n' \
               'Champawat , 7556 , 7314 , 18 , 53, 171 | 1, 2, 3, 4, 5, 6'

    expected_args = [
        {
            'district_name': 'Almora',
            'confirmed': 12148,
            'recovered': 11341,
            'deceased': 195,
            'migrated': 607
        },
        {
            'district_name': 'Bageshwar',
            'confirmed': 5747,
            'recovered': 5659,
            'deceased': 60,
            'migrated': 25
        },
        {
            'district_name': 'Champawat',
            'confirmed': 7556,
            'recovered': 7314,
            'deceased': 53,
            'migrated': 171
        }
    ]

    helper_for_districts_ocr(get_automation, 'ut', file_str, expected_args, ["Issue with ['Chamoli"])


def test_jk_get_data(get_automation):
    file_str = 'Srinagar , 0 , 23 , 23 , 5066 , 67506 , 72572' \
               ' , 569 , 0 , 71168, 835 | 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12\n' \
               'Baramulla , 0 , 0 , 0 , 890 , 23060 , 23950 , 146 , ' \
               '0 , 23522, 282 | 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12\n' \
               'Budgam , 0 , 27 , 27 , 817 , 22432 , ' \
               '23249 , 180 , 0 , 22862, 207 | 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12\n' \
               'Pulwama ,  0 , 0 , 525 , 14817 , ' \
               '15342 , 47 , 0 , 15101, 194 | 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12'
    expected_args = [
        {
            'district_name': 'Srinagar',
            'confirmed': 72572,
            'recovered': 71168,
            'deceased': 835,
        },
        {
            'district_name': 'Baramulla',
            'confirmed': 23950,
            'recovered': 23522,
            'deceased': 282,
        },
        {
            'district_name': 'Budgam',
            'confirmed': 23249,
            'recovered': 22862,
            'deceased': 207
        }
    ]

    helper_for_districts_ocr(get_automation, 'jk', file_str, expected_args, ["Issue with ['Pulwama"])


def test_wb_get_data(get_automation):
    state_mock = \
        mock.mock_open(read_data=
                       'Alipurduar,15514,15340,101\n' \
                       'Coochbehar,29051,28803,97\n' \
                       'Darjeeling,56636,55754\n' \
                       )
    captured_output = io.StringIO()  # Create StringIO object
    sys.stdout = captured_output

    with mock.patch("automation.Automation.read_file_from_url_v2") as url_mock:
        url_mock.return_value = True
        with mock.patch("automation.open", state_mock):
            get_automation.meta_dictionary['West Bengal'] = AutomationMeta("West Bengal", 'wb', "");
            get_automation.wb_get_data()
            url_mock.assert_called_once()
            call_args = [{'district_name': 'Alipurduar', 'confirmed': 15514, 'recovered': 15340, 'deceased': 101},
                         {'district_name': 'Coochbehar', 'confirmed': 29051, 'recovered': 28803, 'deceased': 97}
                         ]
            get_automation.delta_calculator.get_state_data_from_site.assert_called_once()
            get_automation.delta_calculator.get_state_data_from_site.assert_called_once_with(
                "West Bengal",
                call_args,
                ''
            )
            assert "Issue with ['Darjeeling" in captured_output.getvalue()
    sys.stdout = sys.__stdout__


def test_pb_get_data(get_automation):
    file_str = 'Ludhiana , 87556 , 17 , 85136, 2103 | 1, 2, 3, 4, 5\n' \
               'SAS Nagar , 68753 , 15 , 67670, 1068 | 1, 2, 3, 4, 5\n' \
               'Jalandhar , 63341, 61819, 1495 | 1, 2, 3, 4, 5'

    expected_args = [
        {
            'district_name': 'Ludhiana',
            'confirmed': 87556,
            'recovered': 85136,
            'deceased': 2103
        },
        {
            'district_name': 'Sas Nagar',
            'confirmed': 68753,
            'recovered': 67670,
            'deceased': 1068
        }
    ]

    helper_for_districts_ocr(get_automation, 'pb', file_str, expected_args, ["Issue with ['Jalandhar"])


def test_br_get_data(get_automation):
    file_str = 'Kishanganj,4322,4306,13,3 | 1, 2, 3, 4, 5\n' \
               'Lakhisarai,3860,3847,9 | 1, 2, 3, 4\n' \
               'Madhubani,7750,7710,34,6 | 1, 2, 3, 4, 5'

    expected_args = [
        {
            'district_name': 'Kishanganj',
            'confirmed': 4322,
            'recovered': 4306,
            'deceased': 13
        },
        {
            'district_name': 'Madhubani',
            'confirmed': 7750,
            'recovered': 7710,
            'deceased': 34
        }
    ]

    helper_for_districts_ocr(get_automation, 'br', file_str, expected_args, ["Issue with ['Lakhisarai"])


def test_jh_get_data(get_automation):
    file_str = 'Bokaro , 2 , 19152 , 286 , 19440 , 1 , 1, 1 | 2, 3, 4, 5, 6, 7, 8, 9\n' \
               'Chatra , 3 , 5977 , 53 , 6033 , 1 , 1, 1 | 2, 3, 4, 5, 6, 7, 8, 9\n' \
               'Deoghar  , 10716 , 113 , 10833 , 1 , 1, 0 | 2, 3, 4, 5, 6, 7, 8, 9'

    expected_args = [
        {
            'district_name': 'Bokaro',
            'confirmed': 19441,
            'recovered': 19153,
            'deceased': 287
        },
        {
            'district_name': 'Chatra',
            'confirmed': 6034,
            'recovered': 5978,
            'deceased': 54
        }
    ]

    helper_for_districts_ocr(get_automation, 'jh', file_str, expected_args, ["Issue with ['Deoghar"])


def test_mp_get_data(get_automation):
    file_str = 'Indore , 165 , 59617 , 0 , 933 , 64 , 57730, 954 | 27, 4, 42, 1, 7, 11, 67, 2\n' \
               'Bhopal , 49 , 44082 , 0 , 618 , 58 , 42899, 565 | 27, 4, 42, 1, 7, 11, 67, 2\n' \
               'Jabalpur , 16638 , 0 , 252 , 14 , 16269, 117 | 27, 4, 42, 1, 7, 11, 67, 2\n' \
               'Gwalior, 16536 , 0 , 230 , 1 , 16260, 46 | 27, 4, 42, 1, 7, 11, 67, 2'

    expected_args = [
        {
            'district_name': 'Indore',
            'confirmed': 59617,
            'recovered': 57730,
            'deceased': 933
        },
        {
            'district_name': 'Bhopal',
            'confirmed': 44082,
            'recovered': 42899,
            'deceased': 618
        }
    ]

    helper_for_districts_ocr(get_automation, 'mp', file_str, expected_args,
                             ["Issue with ['Jabalpur", "Issue with ['Gwalior"])


def test_rj_get_data(get_automation):
    file_str = 'AJMER , 276279 , 8 , 17179 , 0 , 222 , 4 , 16901, 56 | 2, 3, 4, 5, 6, 7, 8, 9, 10\n' \
               'ALWAR , 348824 , 21842 , 0 , 78 , 0 , 21750, 14 | 2, 3, 4, 5, 6, 7, 8, 9, 10\n' \
               'BANSWARA , 51281 , 5 , 2390 , 0 , 34 , 5 , 2305, 51 | 2, 3, 4, 5, 6, 7, 8, 9, 10'

    expected_args = [
        {
            'district_name': 'Ajmer',
            'confirmed': 17179,
            'recovered': 16901,
            'deceased': 222
        },
        {
            'district_name': 'Banswara',
            'confirmed': 2390,
            'recovered': 2305,
            'deceased': 34
        }
    ]

    helper_for_districts_ocr(get_automation, 'rj', file_str, expected_args,
                             ["Issue with ['ALWAR"])


def test_tr_get_data(get_automation):
    html_data = '<tbody>\n' \
                '<tr>\n' \
                '    <td>1</td>\n' \
                '    <td>Dhalai</td>\n' \
                '    <td class="text-center">7847</td>\n' \
                '    <td class="text-center">7847</td>\n' \
                '    <td class="text-center">0</td>\n' \
                '    <td class="text-center">0</td>\n' \
                '    <td class="text-center">0</td>\n' \
                '    <td class="text-center text-primary">176405</td>\n' \
                '    <td class="text-center text-danger">7034</td>\n' \
                '    <td class="text-center text-success">169371</td>\n' \
                '    <td class="text-center text-success">6997</td>\n' \
                '    <td class="text-center text-primary">1</td>\n' \
                '    <td class="text-center text-danger">35</td>\n' \
                '</tr>\n' \
                '<tr>\n' \
                '    <td>2</td>\n' \
                '    <td>Gomati</td>\n' \
                '    <td class="text-center">8542</td>\n' \
                '    <td class="text-center">8542</td>\n' \
                '    <td class="text-center">0</td>\n' \
                '    <td class="text-center">0</td>\n' \
                '    <td class="text-center">0</td>\n' \
                '    <td class="text-center text-primary">137640</td>\n' \
                '    <td class="text-center text-danger">8119</td>\n' \
                '    <td class="text-center text-success">129521</td>\n' \
                '    <td class="text-center text-success">8033</td>\n' \
                '    <td class="text-center text-primary">4</td>\n' \
                '    <td class="text-center text-danger">74</td>\n' \
                '</tr>\n'
    with requests_mock.Mocker() as mock_url:
        get_automation.meta_dictionary['Tripura'] = AutomationMeta(
            "Tripura", 'tr', "https://covid19.tripura.gov.in/Visitor/ViewStatus.aspx");
        mock_url.get(get_automation.meta_dictionary['Tripura'].url, text=html_data)
        get_automation.tr_get_data()

        call_args = [
            {"district_name": "Dhalai",
             "confirmed": 7034,
             "recovered": 6997,
             "deceased": 35
             },
            {"district_name": "Gomati",
             "confirmed": 8119,
             "recovered": 8033,
             "deceased": 74
             }
        ]

        get_automation.delta_calculator.get_state_data_from_site.assert_called_once()
        get_automation.delta_calculator.get_state_data_from_site.assert_called_once_with(
            "Tripura",
            call_args,
            ''
        )
