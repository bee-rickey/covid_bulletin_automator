import os
import sys
import io
import json
import operator
import pickle
import cv2
import numpy as np
from google.cloud import vision
from google.protobuf.json_format import MessageToJson

import argparse


class GoogleVision:
    """
    Read google vision output and build an array of dictionaries
    containing text information
    """

    def detect_text(self, path):
        """Detects text in the file."""

        client = vision.ImageAnnotatorClient()

        with io.open(path, 'rb') as image_file:
            content = image_file.read()

        image = vision.Image(content=content)

        response = client.document_text_detection(image=image)
        output = MessageToJson(response._pb)
        temporary_array = []

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

            temporary_array.append(text_item)

        self.text_array = sorted(temporary_array, key=lambda item: (item['x_mid'], -item['y_mid']))

        if response.error.message:
            raise Exception(
                '{}\nFor more info on error messages, check: '
                'https://cloud.google.com/apis/design/errors'.format(
                    response.error.message))

    def __init__(self, file_name):
        """
        Call detect_text
        :param file_name:
        """
        self.file_name = file_name
        self.text_array = []
        os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = "../../../visionapi.json"
        self.detect_text(file_name)


class Ocr:
    """
    Arrange the image data into rows and cols.
    Remove unwanted rows (assuming district name is part of row)
    Display image with texts matched
    """

    def __init__(self, google_vision, state_name, start_string, end_string):
        self.rows_found = {}
        self.filtered_rows = {}
        self.translation_dictionary = {}
        self.district_dictionary = []
        self.start_string = start_string
        self.end_string = end_string
        self.google_vision = google_vision

        self.read_districts(state_name)
        self.assign_rows(google_vision.text_array)
        self.mark_unwanted_rows()
        self.assign_columns()

    def hough_transform(self):
        img = cv2.imread(self.google_vision.image_name)
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        edges = cv2.Canny(img, 50, 150)
        config_min_line_length = 400
        lines = cv2.HoughLinesP(edges, 1, np.pi / 135, config_min_line_length, maxLineGap=250)


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
                self.district_dictionary.append(line[0].strip().title())

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
                text['row'] = row
                previous_text = text
                self.rows_found[row] = {
                    'number': row,
                    'values': [text]
                }
                continue
            # Next text block lies within ranges of the previous text block
            # Essentially they are on the same row
            if previous_text['upper_right']['y'] > text['y_mid'] > previous_text['lower_left']['y']:
                text['row'] = row
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

    def is_district_present(self, text_block):
        if text_block['text'].strip().title() in self.district_dictionary:
            return True
        else:
            False

    def mark_unwanted_rows(self):
        for item in self.rows_found.values():
            item['valid_row'] = False
            for text_block in item['values']:
                if self.is_district_present(text_block):
                    item['valid_row'] = True
                    break

        self.filtered_rows = {key: value
                              for key, value in self.rows_found.items()
                              if value['valid_row'] is True}

    def assign_columns(self):
        print("Hello")




def main():
    """
    Call ocr related classes.
    :return:
    """
    parser = argparse.ArgumentParser()
    parser.add_argument('--state', type=str, required=True)
    parser.add_argument('--image', type=str, required=True)
    parser.add_argument('--start_end', type=str, required=True)
    parser.add_argument('--translation_required', type=str, required=False)
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

    translation_required = args.translation_required

    ocr = Ocr(google_vision, state_name, start_string, end_string)


if __name__ == '__main__':
    main()
