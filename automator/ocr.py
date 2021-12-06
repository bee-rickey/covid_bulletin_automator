import os
import io
import cv2
import re
import json
import numpy as np
from google.cloud import vision
from google.protobuf.json_format import MessageToJson
import argparse


class GoogleVision:
    """
    Read google vision output and build an array of dictionaries
    containing text information
    Object format for texts:
    text: "actual text from image",
    vertices: array of four corners of text
    lower_left: lower left vertex of text
    upper_right: upper right vertex of text
    x-mid: midpoint x coordinate of text
    y-mid: midpoint y coordinate of text
    """

    def detect_text(self, path):
        """Detects text in the file."""

        client = vision.ImageAnnotatorClient()

        with io.open(path, 'rb') as image_file:
            content = image_file.read()

        image = vision.Image(content=content)

        response = client.document_text_detection(image=image)
        output = json.loads(MessageToJson(response._pb))

        for index, text in enumerate(output['textAnnotations']):
            if index == 0:
                continue
            vertices = text['boundingPoly']['vertices']
            text_item = {
                "text": f"{text['description']}",
                "vertices": vertices,
                "lower_left": vertices[0],
                "upper_right": vertices[2],
                "y_mid": (vertices[0]['y'] + vertices[2]['y']) / 2,
                "x_mid": (vertices[0]['x'] + vertices[2]['x']) / 2
            }

            self.text_array.append(text_item)

        self.text_array.sort(key=lambda item: (item['y_mid']))
        """
        if response.error.message:
            raise Exception(
                '{}\nFor more info on error messages, check: '
                'https://cloud.google.com/apis/design/errors'.format(
                    response.error.message))
        """

    def __init__(self, image_name):
        """
        Call detect_text
        :param file_name:
        """
        self.image_name = image_name
        self.text_array = []
        os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = "../visionapi.json"
        self.detect_text(image_name)


class Ocr:
    """
    Arrange the image data into rows.
    Remove unwanted rows (assuming district name is part of row)
    Display image with texts matched
    """

    def __init__(self, google_vision, state_name, start_string, end_string):
        self.vertical_lines = []
        self.rows_found = {}
        self.column_list = []
        self.config_min_line_length = 400
        self.translation_dictionary = {}
        self.district_dictionary = []
        self.start_string = start_string
        self.end_string = end_string
        self.google_vision = google_vision
        self.read_districts(state_name)
        self.assign_rows(google_vision.text_array)

    def hough_transform(self):
        img = cv2.imread(self.google_vision.image_name)
        edges = cv2.Canny(img, 50, 150)
        lines = cv2.HoughLinesP(edges, 1, np.pi / 135, int(self.config_min_line_length), maxLineGap=250)
        vertical_lines = []
        for line in lines:
            x1, y1, x2, y2 = line[0]
            line_coordinates = \
                {
                    "x1": x1,
                    "y1": y1,
                    "x2": x2,
                    "y2": y2
                }
            vertical_lines.append(line_coordinates)

        vertical_lines.sort(key=lambda item: item["x1"])
        column_number = 1
        for index, lines in enumerate(vertical_lines):
            # If first vertical line, then just move ahead
            if index == 0:
                previous_x = lines["x1"]
                previous_y = lines["y1"]
                continue

            # This condition checks if two detected
            # lines are too close to each other. If so, ignore.
            if lines["x1"] - previous_x < 5:
                continue

            # Add the column definition to the column_list
            self.column_list.append({
                "col_left_x": previous_x,
                "col_left_y": previous_y,
                "col_right_x": lines["x1"],
                "col_right_y": lines["y1"],
                "column_number": column_number
            })
            previous_x = lines["x1"]
            previous_y = lines["y1"]

            column_number += 1

    def read_districts(self, state_name):
        name_to_code = {}

        with open("state_codes.csv", "r") as state_codes:
            for lines in state_codes:
                line = lines.split(',')
                name_to_code[line[0].strip().lower()] = line[1].strip().lower()

        with open(f"{name_to_code[state_name.lower()]}_districts.csv", "r") as districts:
            for lines in districts:
                line = lines.split(',')
                self.translation_dictionary[line[0].strip().title()] \
                    = line[1].strip().title()
                self.district_dictionary.append(line[1].strip().title())

    def assign_rows(self, google_vision_output):
        """
        Read each entry which is sorted by x_mid asc and y_mid desc
        If y_mid shifts more than the previous text's upper right y or lower right y,
        Assign it a new row number and continue.
        :param google_vision_output:
        :return:
        """
        row = 1
        previous_text = None

        for text in google_vision_output:
            if previous_text is None:
                text['row'] = row
                previous_text = text
                self.rows_found[row] = {
                    'number': row,
                    'values': [text]
                }
                continue
            # Next text block lies within ranges of the previous text block
            # Essentially they are on the same row
            tolerance_upper = previous_text['y_mid'] + 5
            tolerance_lower = previous_text['y_mid'] - 5
            if tolerance_lower < text['y_mid'] < tolerance_upper:
                self.rows_found[row]['values'].append(text)
            else:
                # Seems to be a new row, so start off with the first text.
                previous_text = text
                row += 1
                text['row'] = row
                self.rows_found[row] = {
                    'values': [text],
                    'number': row
                }

    def is_district_present(self, text):
        for district in self.district_dictionary:
            if district.lower() in text.strip().lower():
                return True
        return False

    def check_coordinates(self, previous_text, current_text):
        for column in self.column_list:
            if column['col_left_x'] \
                    < previous_text['lower_left']['x'] \
                    < column['col_right_x'] \
                    and column['col_left_x'] \
                    < current_text['lower_left']['x'] \
                    < column['col_right_x']:
                return True

    def is_numeric(self, text):
        try:
            int(text)
            return True
        except ValueError:
            return False
        except Exception:
            return False

    @staticmethod
    def replace_special_characters(text):
        return re.sub(r"[*.#,]", '', text)

    def print_lines(self):
        """
        take rows found,
        for each row
        translate/map texts if it's present in dictionary.
        Check the coordinates of all these texts with columns (if defined),
        Append string.
        Print if the string has a district string in it.
        """

        for key, row in self.rows_found.items():
            string_output = ""

            row['values'].sort(key=lambda item: item['lower_left']["x"])

            for index, text in enumerate(row['values']):
                text['text'] = Ocr.replace_special_characters(text['text'])
                if text['text'] in self.translation_dictionary:
                    text['text'] = \
                        self.translation_dictionary[text['text']]

                if index == 0:
                    string_output = Ocr.replace_special_characters(text['text'])
                    continue

                if self.check_coordinates(row['values'][index - 1], text) \
                        or \
                        (self.is_numeric(string_output) is False
                         and self.is_numeric(text['text']) is False):
                    string_output += f" {text['text']}"
                    continue

                string_output += "," + text['text']

            print(f"{string_output}")

def main():
    """
    Call ocr related classes.
    :return:
    """
    parser = argparse.ArgumentParser()
    parser.add_argument('--state', type=str, required=True)
    parser.add_argument('--image', type=str, required=True)
    parser.add_argument('--start_end', type=str, required=True)
    parser.add_argument('--skip_stages', type=str, required=False)

    args = parser.parse_args()

    state_name = args.state
    image = args.image

    google_vision = GoogleVision(image)

    start_end = "auto,auto"
    if args.start_end is not None:
        start_end = args.start_end

    start_string = start_end.start_end.split(',')[0]
    end_string = start_end.start_end.split(',')[1]

    ocr = Ocr(google_vision, state_name, start_string, end_string)
    ocr.hough_transform()
    ocr.print_lines()


if __name__ == '__main__':
    main()
