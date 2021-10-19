import io
import sys
sys.path.insert(0, '../')
from unittest import mock
from unittest.mock import Mock
from ocr import GoogleVision
from ocr import Ocr
import numpy as np


class MockClient():
    """
    Mock class to mimick google vision
    """

    def document_text_detection(self, image):
        mock = Mock()
        mock._rb = Mock(return_value='wheeeeee')
        mock.error = Mock()
        mock.error.message = False
        return mock


def get_json_object():
    json_obj = {
        "textAnnotations": [
            {
                "locale": "hi",
                "description": "17.\n\u0915\u093f\u0936\u0928\u0917"
                               "\u0902\u091c\n4322\n4306\n13\n3\n18."
                               "\n\u0932\u0916\u0940\u0938\u0930\u093e\u092f",
                "boundingPoly": {
                    "vertices": [
                        {
                            "x": 28,
                            "y": 16
                        },
                        {
                            "x": 1177,
                            "y": 16
                        },
                        {
                            "x": 1177,
                            "y": 824
                        },
                        {
                            "x": 28,
                            "y": 824
                        }
                    ]
                }
            },
            {
                "description": ".",
                "boundingPoly": {
                    "vertices": [
                        {
                            "x": 75,
                            "y": 23
                        },
                        {
                            "x": 78,
                            "y": 23
                        },
                        {
                            "x": 77,
                            "y": 50
                        },
                        {
                            "x": 74,
                            "y": 50
                        }
                    ]
                }
            },
            {
                "description": "17",
                "boundingPoly": {
                    "vertices": [
                        {
                            "x": 33,
                            "y": 21
                        },
                        {
                            "x": 62,
                            "y": 22
                        },
                        {
                            "x": 61,
                            "y": 49
                        },
                        {
                            "x": 32,
                            "y": 48
                        }
                    ]
                }
            },
            {
                "description": "\u0915\u093f\u0936\u0928\u0917\u0902\u091c",
                "boundingPoly": {
                    "vertices": [
                        {
                            "x": 182,
                            "y": 16
                        },
                        {
                            "x": 302,
                            "y": 17
                        },
                        {
                            "x": 302,
                            "y": 53
                        },
                        {
                            "x": 182,
                            "y": 52
                        }
                    ]
                }
            }
        ]
    }
    return json_obj


def test_google_vision():
    mock_open = mock.mock_open(read_data="blah")
    with mock.patch('os.environ') as mock_env:
        mock_env.return_value = True
        with mock.patch('ocr.vision') as mock_vision:
            mock_vision.ImageAnnotatorClient.return_value = MockClient()
            mock_vision.Image.return_value = True

            json_object = get_json_object()

            with mock.patch('ocr.io.open', mock_open):
                with mock.patch('ocr.MessageToJson') as mock_json_message:
                    mock_json_message.return_value = json_object
                    google_vision_json = GoogleVision("file_name")

                    assert 3 == len(google_vision_json.text_array)

                    first_poly = [
                        {'x': 33, 'y': 21}, {'x': 62, 'y': 22},
                        {'x': 61, 'y': 49}, {'x': 32, 'y': 48}
                    ]

                    assert google_vision_json.text_array[0]['vertices'][0] == first_poly[0]
                    assert google_vision_json.text_array[0]['vertices'][1] == first_poly[1]
                    assert google_vision_json.text_array[0]['vertices'][2] == first_poly[2]
                    assert google_vision_json.text_array[0]['vertices'][3] == first_poly[3]

                    last_poly = [{"x": 182, "y": 16}, {"x": 302, "y": 17}, {"x": 302, "y": 53}, {"x": 182, "y": 17}]

                    assert google_vision_json.text_array[2]['lower_left'] == last_poly[0]
                    assert google_vision_json.text_array[2]['upper_right'] == last_poly[2]


def test_row_assignment():
    mock_state_code = mock.mock_open(read_data='Karnataka, KA\n' \
                                               'Tamil Nadu, TN\n'
                                               'West Bengal, WB')

    mock_district_mapping = mock.mock_open(read_data='Bangalore, Bengaluru\n'
                                                     'Tumakuru, Tumkur')

    google_vision_json = [
        {'text': 'first row',
         'y_mid': 51,
         'upper_right': {'x': 0, 'y': 55},
         'lower_left': {'x': 0, 'y': 45}
         },
        {'text': 'first row - 2nd entry',
         'y_mid': 50,
         'upper_right': {'x': 0, 'y': 56},
         'lower_left': {'x': 0, 'y': 46}
         },
        {'text': 'first row - 3rd entry',
         'y_mid': 50,
         'upper_right': {'x': 0, 'y': 54},
         'lower_left': {'x': 0, 'y': 46},
         },
        {'text': 'second row - 1st entry',
         'y_mid': 44,
         'upper_right': {'x': 0, 'y': 49},
         'lower_left': {'x': 0, 'y': 40},
         },
        {'text': 'second row - 2nd entry',
         'y_mid': 44,
         'upper_right': {'x': 0, 'y': 50},
         'lower_left': {'x': 0, 'y': 40},
         },

    ]

    with mock.patch("ocr.open", mock_state_code):
        with mock.patch("ocr.GoogleVision") as mock_google_vision:
            mock_google_vision.text_array = google_vision_json
            ocr = Ocr(mock_google_vision, "Karnataka", "", "")
            assert len(ocr.rows_found) == 2
            assert len(ocr.rows_found[1]['values']) == 3
            assert ocr.rows_found[1]['number'] == 1
            assert ocr.rows_found[1]['values'][2]['text'] == "first row - 3rd entry"
            assert ocr.rows_found[2]['number'] == 2
            assert len(ocr.rows_found[2]['values']) == 2
            assert ocr.rows_found[2]['values'][0]['text'] == "second row - 1st entry"


def test_row_validation():
    mock_state_code = mock.mock_open(read_data='Karnataka, KA\n' \
                                               'Tamil Nadu, TN\n'
                                               'West Bengal, WB')

    district_string = 'Bangalore, Bengaluru\nTumakuru, Tumkur'

    google_vision_json = [
        {'text': 'Bangalore',
         'y_mid': 51,
         'upper_right': {'x': 0, 'y': 55},
         'lower_left': {'x': 0, 'y': 45}
         },
        {'text': 'first row - 2nd entry',
         'y_mid': 50,
         'upper_right': {'x': 0, 'y': 56},
         'lower_left': {'x': 0, 'y': 46}
         },
        {'text': 'first row - 3rd entry',
         'y_mid': 50,
         'upper_right': {'x': 0, 'y': 54},
         'lower_left': {'x': 0, 'y': 46},
         },
        {'text': 'second row - 1st entry',
         'y_mid': 44,
         'upper_right': {'x': 0, 'y': 49},
         'lower_left': {'x': 0, 'y': 40},
         },
        {'text': 'second row - 2nd entry',
         'y_mid': 44,
         'upper_right': {'x': 0, 'y': 50},
         'lower_left': {'x': 0, 'y': 40},
         },

    ]

    with mock.patch("ocr.open", mock_state_code):
        with mock.patch("ocr.GoogleVision") as mock_google_vision:
            mock_google_vision.text_array = google_vision_json
            handlers = (mock_state_code.return_value, mock.mock_open(read_data=district_string).return_value)
            mock_state_code.side_effect = handlers
            ocr = Ocr(mock_google_vision, "Karnataka", "", "")
            assert len(ocr.rows_found) == 2
            assert len(ocr.rows_found[1]['values']) == 3
            assert ocr.rows_found[1]['number'] == 1
            assert ocr.rows_found[1]['values'][2]['text'] == "first row - 3rd entry"
            assert ocr.rows_found[2]['number'] == 2
            assert len(ocr.rows_found[2]['values']) == 2
            assert ocr.rows_found[2]['values'][0]['text'] == "second row - 1st entry"

            filtered_rows = {key: value
                             for key, value in ocr.rows_found.items()
                             if value['valid_row'] is True}
            assert len(filtered_rows) == 1
            assert filtered_rows[1]['valid_row'] == True
            assert (ocr.rows_found[2]['valid_row']) == False
            assert ocr.rows_found[1]['valid_row'] == True


def test_hough_transform():
    mock_state_code = mock.mock_open(read_data='Karnataka, KA\n' \
                                               'Tamil Nadu, TN\n'
                                               'West Bengal, WB')
    with mock.patch("ocr.open", mock_state_code):
        with mock.patch("ocr.GoogleVision") as mock_google_vision:
            with mock.patch("ocr.cv2") as mock_cv2:
                mock_cv2.imread.return_value = True
                mock_cv2.cvtColor.return_value = True
                mock_cv2.Canny.return_value = True
                mock_cv2.HoughLinesP.return_value = \
                    np.array([
                        [[100, 120, 100, 10]],
                        [[91, 120, 91, 10]],
                        [[110, 120, 110, 10]],
                        [[90, 120, 90, 10]]
                    ])
                mock_google_vision.text_array = []
                mock_google_vision.image_name = ""
                ocr = Ocr(mock_google_vision, "Karnataka", "", "")
                ocr.hough_transform()
                column_list_expected = [
                    {
                        "col_left_x": 90,
                        "col_left_y": 120,
                        "col_right_x": 100,
                        "col_right_y": 120
                    },
                    {
                        "col_left_x": 100,
                        "col_left_y": 120,
                        "col_right_x": 110,
                        "col_right_y": 120
                    },
                ]
                assert column_list_expected, ocr.column_list


def test_print_output_without_hough():
    mock_state_code = mock.mock_open(read_data='Karnataka, KA\n' \
                                               'Tamil Nadu, TN\n'
                                               'West Bengal, WB')

    district_string = 'Bangalore, Bengaluru\nTumakuru, Tumkur'

    google_vision_json = [
        {'text': 'Bangalore',
         'y_mid': 51,
         'upper_right': {'x': 10, 'y': 55},
         'lower_left': {'x': 5, 'y': 45}
         },
        {'text': '100',
         'y_mid': 50,
         'upper_right': {'x': 25, 'y': 56},
         'lower_left': {'x': 20, 'y': 46}
         },
        {'text': '200',
         'y_mid': 50,
         'upper_right': {'x': 40, 'y': 54},
         'lower_left': {'x': 35, 'y': 46},
         },
        {'text': 'second row - 1st entry',
         'y_mid': 44,
         'upper_right': {'x': 10, 'y': 49},
         'lower_left': {'x': 5, 'y': 40},
         },
        {'text': 'second row - 2nd entry',
         'y_mid': 44,
         'upper_right': {'x': 25, 'y': 50},
         'lower_left': {'x': 20, 'y': 40},
         },
        {'text': 'Tumakuru',
         'y_mid': 51,
         'upper_right': {'x': 10, 'y': 55},
         'lower_left': {'x': 5, 'y': 45}
         },
        {'text': '100',
         'y_mid': 50,
         'upper_right': {'x': 25, 'y': 56},
         'lower_left': {'x': 20, 'y': 46}
         },
        {'text': '200',
         'y_mid': 50,
         'upper_right': {'x': 40, 'y': 54},
         'lower_left': {'x': 35, 'y': 46},
         },
    ]

    with mock.patch("ocr.open", mock_state_code):
        with mock.patch("ocr.GoogleVision") as mock_google_vision:
            mock_google_vision.text_array = google_vision_json
            handlers = (mock_state_code.return_value, mock.mock_open(read_data=district_string).return_value)
            mock_state_code.side_effect = handlers
            ocr = Ocr(mock_google_vision, "Karnataka", "", "")
            assert len(ocr.rows_found) == 3

            captured_output = io.StringIO()  # Create StringIO object
            sys.stdout = captured_output

            ocr.print_lines()

            expected_output = "Bengaluru,100,200\nTumkur,100,200\n"
            assert captured_output.getvalue() == expected_output

            sys.stdout = sys.__stdout__


def test_print_output_with_multiple_texts():
    mock_state_code = mock.mock_open(read_data='Karnataka, KA\n' \
                                               'Tamil Nadu, TN\n'
                                               'West Bengal, WB')

    district_string = 'Dakshin Dinajpur, Dakshin Dinajpur\nKolkata, Kolkata'

    google_vision_json = [
        {'text': 'Dakshin Dinajpur',
         'y_mid': 51,
         'upper_right': {'x': 10, 'y': 55},
         'lower_left': {'x': 5, 'y': 45}
         },
        {'text': '100',
         'y_mid': 50,
         'upper_right': {'x': 25, 'y': 56},
         'lower_left': {'x': 20, 'y': 46}
         },
        {'text': '200',
         'y_mid': 50,
         'upper_right': {'x': 40, 'y': 54},
         'lower_left': {'x': 35, 'y': 46},
         },
        {'text': 'second row - 1st entry',
         'y_mid': 44,
         'upper_right': {'x': 10, 'y': 49},
         'lower_left': {'x': 5, 'y': 40},
         },
        {'text': 'second row - 2nd entry',
         'y_mid': 44,
         'upper_right': {'x': 25, 'y': 50},
         'lower_left': {'x': 20, 'y': 40},
         },
        {'text': 'Kolkata',
         'y_mid': 51,
         'upper_right': {'x': 10, 'y': 55},
         'lower_left': {'x': 5, 'y': 45}
         },
        {'text': '100',
         'y_mid': 50,
         'upper_right': {'x': 25, 'y': 56},
         'lower_left': {'x': 20, 'y': 46}
         },
        {'text': '200',
         'y_mid': 50,
         'upper_right': {'x': 40, 'y': 54},
         'lower_left': {'x': 35, 'y': 46},
         },
    ]

    with mock.patch("ocr.open", mock_state_code):
        with mock.patch("ocr.GoogleVision") as mock_google_vision:
            mock_google_vision.text_array = google_vision_json
            handlers = (mock_state_code.return_value, mock.mock_open(read_data=district_string).return_value)
            mock_state_code.side_effect = handlers
            ocr = Ocr(mock_google_vision, "West Bengal", "", "")
            assert len(ocr.rows_found) == 3

            captured_output = io.StringIO()  # Create StringIO object
            sys.stdout = captured_output

            ocr.print_lines()

            expected_output = "Dakshin Dinajpur,100,200\nKolkata,100,200\n"
            assert captured_output.getvalue() == expected_output
                
            sys.stdout = sys.__stdout__

