#!/usr/bin/python3

import json
import argparse
from ocr import Ocr
from ocr import GoogleVision
from automation import Automation


def read_configurations():
    with open("ocr_configs.json") as config_file:
        data = json.load(config_file)
        return data


def main():
    epilog = '''Example:
    ./orchestrator.py --state="Andhra Pradesh" --type="ocr" --image="/home/Downloads/ap.jpeg"
    ./orchestrator.py --state="West Bengal" --type="pdf" --url="wbhealth.gov.in/covid/bulletin.pdf" --page_id=2
    ./orchestrator.py --state="Odisha" --type="dashboard" 
    '''
    configurations = read_configurations()
    parser = argparse.ArgumentParser(epilog=epilog)
    parser.add_argument('--state', type=str, required=True, help="state name")
    parser.add_argument('--type', type=str, required=True)
    parser.add_argument('--image', type=str, required=False)
    parser.add_argument('--start_end_string', type=str, required=False)
    parser.add_argument('--skip_stages', type=str, required=False)
    parser.add_argument('--url', type=str, required=False)
    parser.add_argument('--page_id', type=str, required=False)

    args = parser.parse_args()
    start = end = ""

    if args.start_end_string is not None:
        start = args.start_end_string.split(",")[0].strip()
        end = args.start_end_string.split(",")[1].strip()

    if args.type == "ocr":
        google_vision = GoogleVision(args.image)
        ocr = Ocr(google_vision, args.state, start, end)
        if configurations[args.state.strip().title()]["hough_transform"]:
            ocr.config_min_line_length = \
                configurations[args.state.strip().title()]["min_line_length"]
            ocr.hough_transform()
        ocr.print_lines()

    automation = Automation(args.type, args.url, args.page_id)

    try:
        eval(automation.meta_dictionary[args.state].state_code.lower() + "_get_data()")
        print("Dashboard url: " + automation.meta_dictionary[args.state].url)
    except KeyError:
        print(f"No entry found for state {args.state} in automation.meta file")


if __name__ == '__main__':
    main()
