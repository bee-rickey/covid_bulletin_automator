#!/usr/local/bin/python3
"""
Class that calls delta calculator for each state
"""
import datetime
import csv
import json
import os
import re
import argparse
import requests
import camelot
from bs4 import BeautifulSoup
from delta_calculator import DeltaCalculator


class AutomationMeta:
    def __init__(self, state_name, state_code, url):
        self.state_name = state_name
        self.state_code = state_code
        self.url = url


class Automation:
    """
    This is refactored code.
    The older one was a script.
    Here, this calls will do all the internal conversions for
    getting per state delta.
    """

    def __init__(self, type_of_automation, pdf_url, page_id):
        self.delta_calculator = DeltaCalculator()
        self.meta_dictionary = {}
        self.option = ""
        self.type_of_automation = type_of_automation
        self.pdf_url = pdf_url
        self.page_id = page_id
        self.load_meta_data()

    def load_meta_data(self):
        """
        Load automation.meta file
        :return:
        """
        with open("automation.meta", "r", encoding="utf-8") as meta_file:
            for line in meta_file:
                if line.startswith('#'):
                    continue
                line_array = line.strip().split(',')
                meta_object = AutomationMeta(
                    line_array[0].strip(),
                    line_array[1].strip(),
                    line_array[2].strip()
                )
                self.meta_dictionary[line_array[0].strip()] = meta_object
        meta_file.close()

    def ct_get_data(self):
        """
        Get chhattisgarh data - This uses column numbers to fetch details
        :return:
        """
        district_array = []
        with open(".tmp/ct.txt", "r", encoding="utf-8") as ct_file:
            for line in ct_file:
                lines_array = line.split('|')[0].split(',')
                available_columns = line.split('|')[1].split(',')

                district_dictionary = {'deceased': 0}
                confirmed_found = False
                recovered_found = False

                for index, data in enumerate(lines_array):
                    if available_columns[index].strip() == "2":
                        district_dictionary['district_name'] = data.strip()
                    if available_columns[index].strip() == "4":
                        district_dictionary['confirmed'] = int(data.strip())
                        confirmed_found = True
                    if available_columns[index].strip() == "9":
                        district_dictionary['recovered'] = int(data.strip())
                        recovered_found = True
                    if available_columns[index].strip() == "12":
                        district_dictionary['deceased'] += int(data.strip())

                if not recovered_found or not confirmed_found:
                    print(f"--> Issue with {lines_array}")
                    continue
                district_array.append(district_dictionary)
        ct_file.close()

        self.delta_calculator.get_state_data_from_site("Chhattisgarh", district_array, self.option)

    def ap_get_data(self):
        """
        Get ap data
        :return:
        """
        if self.type_of_automation == "ocr":
            self.ap_get_data_by_ocr()
        elif self.type_of_automation == "pdf":
            self.ap_get_data_by_pdf()
        else:
            self.ap_get_data_by_url()

    def ap_get_data_by_pdf(self):
        """
        Get ap data by pdf -
        not used since pdfs have stopped
        :return:
        """
        district_array = []
        self.read_file_from_url_v2(
            self.meta_dictionary['Andhra Pradesh'].url,
            "Andhra Pradesh", "Anantapur", ""
        )
        try:
            with open(".tmp/ap.csv", "r", encoding="utf-8") as ap_file:
                for line in ap_file:
                    lines_array = line.split(',')
                    if len(lines_array) != 4:
                        print(f"--> Issue with {lines_array}")
                        continue
                    district_dictionary = {
                        'district_name': lines_array[0].strip(),
                        'confirmed': int(lines_array[1]),
                        'recovered': int(lines_array[2]),
                        'deceased': int(lines_array[3]) if len(
                            re.sub('\n', '', lines_array[3])) != 0 else 0
                    }

                    district_array.append(district_dictionary)

            self.delta_calculator.get_state_data_from_site(
                "Andhra Pradesh",
                district_array, self.option)
        except FileNotFoundError:
            print("ap.csv missing. Generate through pdf or ocr and rerun.")

    def ap_get_data_by_ocr(self):
        """
        AP data using ocr
        :return:
        """
        district_array = []
        with open(".tmp/ap.txt", "r", encoding="utf-8") as ap_file:
            for line in ap_file:
                if 'Total' in line:
                    continue

                lines_array = line.split('|')[0].split(',')
                if len(lines_array) != 6:
                    print(f"--> Issue with {lines_array}")
                    continue

                district_dictionary = {
                    'district_name': lines_array[0].strip(),
                    'confirmed': int(lines_array[2]),
                    'recovered': int(lines_array[4]),
                    'deceased': int(lines_array[5]) if len(
                        re.sub('\n', '', lines_array[3])) != 0 else 0
                }
                district_array.append(district_dictionary)

        self.delta_calculator.get_state_data_from_site(
            "Andhra Pradesh",
            district_array, self.option)

    def ar_get_data(self):
        """
        ar get data
        :return:
        """
        if self.type_of_automation == "ocr":
            self.ar_get_data_by_ocr()
        elif self.type_of_automation == "pdf":
            self.ar_get_data_by_pdf()
        else:
            self.ar_get_data_by_url()

    def ar_get_data_by_ocr(self):
        """
        Papum Pare and capital complex are considered the same district
        :return:
        """
        district_array = []
        additional_district_info = \
            {'district_name': 'Papum Pare', 'confirmed': 0, 'recovered': 0, 'deceased': 0}

        with open(".tmp/ar.txt", "r", encoding="utf-8") as ar_file:
            for line in ar_file:
                if 'Total' in line:
                    continue

                lines_array = line.split('|')[0].split(',')
                if len(lines_array) != 14:
                    print(f"--> Issue with {lines_array}")
                    continue

                if lines_array[0].strip() in ("Capital Complex", "Papum Pare"):
                    additional_district_info['confirmed'] += int(lines_array[5])
                    additional_district_info['recovered'] += int(lines_array[12])
                    additional_district_info['deceased'] += int(lines_array[13]) if len(
                        re.sub('\n', '', lines_array[13])) != 0 else 0
                    continue

                district_dictionary = {
                    'district_name': lines_array[0].strip(),
                    'confirmed': int(lines_array[5]),
                    'recovered': int(lines_array[12]),
                    'deceased': int(lines_array[13]) if len(
                        re.sub('\n', '', lines_array[13])) != 0 else 0
                }

                district_array.append(district_dictionary)

        district_array.append(additional_district_info)

        self.delta_calculator.get_state_data_from_site(
            "Arunachal Pradesh",
            district_array, self.option)

    def or_get_data(self):
        """
        or get data - an ugly hack
        :return:
        """
        os.system(
            "curl -sk https://statedashboard.odisha.gov.in/ | "
            "grep -i string | grep -v legend | "
            "sed 's/var result = JSON.stringify(//' |sed 's/);//' | head -1 > orsite.csv"
        )

        district_array = []
        districts_data = []
        with open("orsite.csv", "r", encoding="utf-8") as meta_file:
            for line in meta_file:
                districts_data = json.loads(line)
        for data in districts_data:
            district_dictionary = {
                'district_name': data['vchDistrictName'],
                'confirmed': int(data['intConfirmed']),
                'recovered': int(data['intRecovered']),
                'deceased': int(data['intDeceased']) + int(data['intOthDeceased'])
            }

            district_array.append(district_dictionary)

        self.delta_calculator.get_state_data_from_site("Odisha", district_array, self.option)

    def mh_get_data(self):
        """
        mh get data
        :return:
        """
        if self.type_of_automation == "ocr":
            self.mh_get_data_by_ocr()
        else:
            self.mh_get_data_by_url()

    def mh_get_data_by_ocr(self):
        """
        migrated category is considered
        :return:
        """
        district_array = []
        try:
            with open(".tmp/mh.txt", "r", encoding="utf-8") as mh_file:
                is_ignore_flag_set = False
                for line in mh_file:
                    lines_array = line.split('|')[0].split(',')
                    if 'Total' in line or is_ignore_flag_set is True:
                        is_ignore_flag_set = True
                        print(f"--> Issue with {lines_array}")
                    if len(lines_array) != 6:
                        print(f"--> Issue with {lines_array}")
                        continue

                    try:
                        if is_number(lines_array[0].strip()):
                            print(f"--> Issue with {lines_array}")
                            continue

                        district_dictionary = {
                            'district_name': lines_array[0].strip().title(),
                            'confirmed': int(lines_array[1]),
                            'recovered': int(lines_array[2]),
                            'deceased': int(lines_array[3]),
                            'migrated': int(lines_array[4])
                        }

                        district_array.append(district_dictionary)
                    except ValueError:
                        print(f"--> Issue with {lines_array}")
                        continue

            self.delta_calculator.get_state_data_from_site(
                "Maharashtra",
                district_array, self.option)
        except FileNotFoundError:
            print("mh.txt missing. Generate through pdf or ocr and rerun.")

    def mh_get_data_by_url(self):
        """
        dashboard updates are slow. However this facility is coded
        :return:
        """
        state_dashboard = requests.request("get", self.meta_dictionary['Maharashtra'].url).json()

        district_array = []
        for district_details in state_dashboard:
            district_dictionary = {
                'district_name': district_details['District'],
                'confirmed': district_details['Positive Cases'],
                'recovered': district_details['Recovered'],
                'deceased': district_details['Deceased'],
            }

            district_array.append(district_dictionary)

        self.delta_calculator.get_state_data_from_site("Maharashtra", district_array, self.option)

    def vcm_get_data(self):
        """
        Pulls from datameet github account. Check automation.meta for vcm entry
        :return:
        """
        print("Date, State, First Dose, Second Dose, Total Doses")

        lookback = int(self.page_id) if len(self.page_id) != 0 else 0
        for day in range(lookback, -1, -1):
            today = (datetime.date.today() - datetime.timedelta(days=day)).strftime("%Y-%m-%d")
            file_name = today + "-at-07-00-AM.pdf"

            self.page_id = "1"

            self.read_file_from_url_v2(
                self.meta_dictionary['VCMohfw'].url
                + file_name, "VCMohfw", "A & N Islands", "")

            dadra = {'firstDose': 0, 'secondDose': 0, 'totalDose': 0}

            try:
                with open(".tmp/vcm.csv", "r", encoding="utf-8") as state_file:
                    for line in state_file:
                        if "Dadra" in line or "Daman" in line:
                            dadra['firstDose'] += int(line.split(',')[1])
                            dadra['secondDose'] += int(line.split(',')[2])
                            dadra['totalDose'] += int(line.split(',')[3])
                            continue
                        print(today + "," + line, end="")

                print(f"{today}, DnH, "
                      f"{dadra['firstDose']}, "
                      f"{dadra['secondDose']}, "
                      f"{dadra['totalDose']}")
            except FileNotFoundError:
                print("br.txt missing. Generate through pdf or ocr and rerun.")

    def hp_get_data(self):
        """
        hp get data
        :return:
        """
        district_array = []

        try:
            with open(".tmp/hp.txt", "r", encoding="utf-8") as hp_file:
                for line in hp_file:
                    line = re.sub(r'\*', '', line)
                    lines_array = line.split('|')[0].split(',')

                    if len(lines_array) != 11:
                        print(f"--> Issue with {lines_array}")
                        continue

                    district_dictionary = {
                        'district_name': lines_array[0].strip(),
                        'confirmed': int(lines_array[1].strip()),
                        'recovered': int(lines_array[8].strip()),
                        'deceased': int(re.sub(r'\*', '', lines_array[9].strip()).strip()),
                    }

                    district_array.append(district_dictionary)

            self.delta_calculator.get_state_data_from_site(
                "Himachal Pradesh",
                district_array, self.option)
        except FileNotFoundError:
            print("hp.txt missing. Generate through pdf or ocr and rerun.")

    def vc_get_data(self):
        """
        pulls from cowin website. Note: This url is not accessible from non indian IP
        :return:
        """
        state_keys = {
            '36': 'West Bengal',
            '7': 'Chhattisgarh',
            '31': 'Tamil Nadu',
            '20': 'Madhya Pradesh',
            '13': 'Himachal Pradesh',
            '4': 'Assam',
            '15': 'Jharkhand',
            '11': 'Gujarat',
            '28': 'Punjab',
            '17': 'Kerala',
            '32': 'Telangana',
            '33': 'Tripura',
            '10': 'Goa',
            '14': 'Jammu and Kashmir',
            '34': 'Uttar Pradesh',
            '29': 'Rajasthan',
            '5': 'Bihar',
            '21': 'Maharashtra',
            '2': 'Andhra Pradesh',
            '16': 'Karnataka',
            '35': 'Uttarakhand',
            '26': 'Odisha',
            '12': 'Haryana',
            '3': 'Arunachal Pradesh',
            '9': 'Delhi',
            '1': 'Andaman and Nicobar Islands',
            '24': 'Mizoram',
            '23': 'Meghalaya',
            '27': 'Puducherry',
            '18': 'Ladakh',
            '30': 'Sikkim',
            '25': 'Nagaland',
            '37': 'Daman and Diu',
            '22': 'Manipur',
            '39': 'Himachal',
            '6': 'Chandigarh',
            '8': 'Dadra and Nagar Haveli',
            '19': 'Lakshadweep',
            '0': 'India'
        }

        lookback = int(self.page_id) if len(self.page_id) != 0 else 0
        lookback_max_date = datetime.date(2021, 5, 21)
        if datetime.date.today() - datetime.timedelta(days=lookback) < lookback_max_date:
            lookback = (datetime.date.today() - lookback_max_date).days
            print(f"------------ Data beyond 21st May has different data "
                  f"ranges hence defaulting max lookback to max {lookback} days--------- ")
        print(
            "date, state, district, daily vaccine count, beneficiaries, "
            "sessions, sites, vaccines given, vaccines given dose two, male, "
            "female, others, covaxin, covishield, sputnik, aefi, 18-45, 45-60, 60+"
        )
        for day in range(lookback, -1, -1):
            today = (datetime.date.today() - datetime.timedelta(days=day)).strftime("%Y-%m-%d")
            today_str = (datetime.date.today() - datetime.timedelta(days=day)).strftime("%d-%m-%Y")
            if self.option == "V2":
                self.meta_dictionary[
                    'Vaccine'].url = "https://api.cowin.gov.in/api/v1/reports/v2/getPublicReports" \
                                     "?state_id=@@state_id@@&district_id=@@district_id@@&date=@@date@@"
            url = re.sub('@@date@@', today, self.meta_dictionary['Vaccine'].url)
            url_nation = re.sub('@@district_id@@', '', re.sub('@@state_id@@', '', url))

            if self.option == "V2":
                self.get_and_print_vaccination_data_v2(url_nation, '0', today_str, state_keys, '')
            else:
                self.get_and_print_vaccination_data_v1(url_nation, '0', today_str, state_keys, '')

            for state_code in range(1, 38, 1):
                url_state = re.sub('@@district_id@@', '', re.sub('@@state_id@@', str(state_code), url))

                if self.option == "V2":
                    district_array = self.get_and_print_vaccination_data_v2(
                        url_state, state_code, today_str, state_keys, '')
                else:
                    district_array = self.get_and_print_vaccination_data_v1(
                        url_state, state_code, today_str, state_keys, '')

                if not district_array:
                    continue
                for district in district_array:
                    url_district = re.sub('@@district_id@@', str(district['district_id']),
                                          re.sub('@@state_id@@', str(state_code), url))
                    if self.option == "V2":
                        self.get_and_print_vaccination_data_v2(
                            url_district, state_code,
                            today_str, state_keys, district['district_name'])
                    else:
                        self.get_and_print_vaccination_data_v1(
                            url_district, state_code,
                            today_str, state_keys,
                            district['district_name'])

    @staticmethod
    def get_and_print_vaccination_data_v1(url, state_code, today_str, state_keys, district_name):
        """
        This uses V1 url of cowin api - not used anymore to pull data
        :param url:
        :param state_code:
        :param today_str:
        :param state_keys:
        :param district_name:
        :return:
        """
        vaccine_dashboard = requests.request("get", url)
        if vaccine_dashboard.status_code != 200:
            while True:
                vaccine_dashboard = requests.request("get", url)
                if vaccine_dashboard.status_code == 200:
                    break
        vaccine_dashboard = vaccine_dashboard.json()
        if not vaccine_dashboard:
            return {}
        gender = {'male': 0, 'female': 0, 'others': 0}

        for i in range(0, 3, 1):
            if vaccine_dashboard['vaccinatedBeneficiaryByGender'][i]['gender_label'].lower() == 'male':
                gender['male'] = \
                    vaccine_dashboard['vaccinatedBeneficiaryByGender'][i]['count']
            if vaccine_dashboard['vaccinatedBeneficiaryByGender'][i]['gender_label'].lower() == 'female':
                gender['female'] = \
                    vaccine_dashboard['vaccinatedBeneficiaryByGender'][i]['count']
            if vaccine_dashboard['vaccinatedBeneficiaryByGender'][i]['gender_label'].lower() == 'others':
                gender['others'] = \
                    vaccine_dashboard['vaccinatedBeneficiaryByGender'][i]['count']

        type_of_vaccine = {'covaxin': 0, 'covishield': 0}
        for i in range(0, 2, 1):
            if vaccine_dashboard['vaccinatedBeneficiaryByMaterial'][i]['material_name'].lower() == 'covaxin':
                type_of_vaccine['covaxin'] = \
                    vaccine_dashboard['vaccinatedBeneficiaryByMaterial'][i]['count']
            if vaccine_dashboard['vaccinatedBeneficiaryByMaterial'][i]['material_name'].lower() == 'covishield':
                type_of_vaccine['covishield'] = \
                    vaccine_dashboard['vaccinatedBeneficiaryByMaterial'][i]['count']

        print(
            f"{today_str}, {state_keys[str(state_code)]}, '{district_name}', "
            f"{vaccine_dashboard['dailyVaccineData']['vaccine_given']}, "
            f"{vaccine_dashboard['overAllReports']['Beneficiaries']}, "
            f"{vaccine_dashboard['overAllReports']['Sessions']}, "
            f"{vaccine_dashboard['overAllReports']['Sites']}, "
            f"{vaccine_dashboard['overAllReports']['Vaccine Given']}, "
            f"{vaccine_dashboard['overAllReports']['Vaccine Given Dose Two']}, "
            f"{gender['male']}, {gender['female']}, {gender['others']}, "
            f"{type_of_vaccine['covaxin']}, "
            f"{type_of_vaccine['covishield']} "
        )
        with open('output.out', 'a', encoding="utf-8") as file:
            print(
                f"{today_str}, {state_keys[str(state_code)]}, "
                f"'{district_name}', {vaccine_dashboard['dailyVaccineData']['vaccine_given']}, "
                f"{vaccine_dashboard['overAllReports']['Beneficiaries']}, "
                f"{vaccine_dashboard['overAllReports']['Sessions']}, "
                f"{vaccine_dashboard['overAllReports']['Sites']}, "
                f"{vaccine_dashboard['overAllReports']['Vaccine Given']}, "
                f"{vaccine_dashboard['overAllReports']['Vaccine Given Dose Two']}, "
                f"{gender['male']}, {gender['female']}, {gender['others']}, "
                f"{type_of_vaccine['covaxin']}, {type_of_vaccine['covishield']} ", file=file)
        return vaccine_dashboard['getBeneficiariesGroupBy']

    @staticmethod
    def get_and_print_vaccination_data_v2(url, state_code, today_str, state_keys, district_name):
        """
        This uses V2 version of cowin api - used to populate data as of now
        :param url:
        :param state_code:
        :param today_str:
        :param state_keys:
        :param district_name:
        :return:
        """
        vaccine_dashboard = requests.request("get", url)
        if vaccine_dashboard.status_code != 200:
            while True:
                vaccine_dashboard = requests.request("get", url)
                if vaccine_dashboard.status_code == 200:
                    break
        vaccine_dashboard = vaccine_dashboard.json()
        if not vaccine_dashboard:
            return {}

        category = vaccine_dashboard['topBlock']['vaccination']
        if 'vaccinationByAge' in vaccine_dashboard.keys():
            category = vaccine_dashboard['vaccinationByAge']

        print(
            f"{today_str}, {state_keys[str(state_code)]}, {district_name}, \
                    {vaccine_dashboard['topBlock']['vaccination']['today']},\
                    {vaccine_dashboard['topBlock']['vaccination']['total']},\
                    {vaccine_dashboard['topBlock']['sessions']['total']},\
                    {vaccine_dashboard['topBlock']['sites']['total']},\
                    {vaccine_dashboard['topBlock']['vaccination']['tot_dose_1']},\
                    {vaccine_dashboard['topBlock']['vaccination']['tot_dose_2']},\
                    {vaccine_dashboard['topBlock']['vaccination']['male']},\
                    {vaccine_dashboard['topBlock']['vaccination']['female']},\
                    {vaccine_dashboard['topBlock']['vaccination']['others']},\
                    {vaccine_dashboard['topBlock']['vaccination']['covaxin']},\
                    {vaccine_dashboard['topBlock']['vaccination']['covishield']},\
                    {vaccine_dashboard['topBlock']['vaccination']['sputnik']},\
                    {vaccine_dashboard['topBlock']['vaccination']['aefi']},\
                    {category['vac_18_45']}, {category['vac_45_60']}, {category['above_60']} ")

        with open('output2.out', 'a', encoding="utf-8") as file:
            print(
                f"{today_str}, {state_keys[str(state_code)]}, {district_name}, "
                f"{vaccine_dashboard['topBlock']['vaccination']['today']}, "
                f"{vaccine_dashboard['topBlock']['vaccination']['total']}, "
                f"{vaccine_dashboard['topBlock']['sessions']['total']}, "
                f"{vaccine_dashboard['topBlock']['sites']['total']}, "
                f"{vaccine_dashboard['topBlock']['vaccination']['tot_dose_1']}, "
                f"{vaccine_dashboard['topBlock']['vaccination']['tot_dose_2']}, "
                f"{vaccine_dashboard['topBlock']['vaccination']['male']}, "
                f"{vaccine_dashboard['topBlock']['vaccination']['female']}, "
                f"{vaccine_dashboard['topBlock']['vaccination']['others']}, "
                f"{vaccine_dashboard['topBlock']['vaccination']['covaxin']}, "
                f"{vaccine_dashboard['topBlock']['vaccination']['covishield']} ", file=file)
        return vaccine_dashboard['getBeneficiariesGroupBy']

    def gj_get_data(self):
        """
        This dashboard is not accessible outside India IP
        :return:
        """
        response = requests.request("GET", self.meta_dictionary['Gujarat'].url)
        soup = BeautifulSoup(response.content, 'html.parser')
        table = soup.find("div", {"class": "table-responsive"}).find_all("tr")

        district_array = []
        for index, row in enumerate(table):
            if index == len(table) - 1:
                continue

            data_points = row.find_all("td")
            if len(data_points) != 6:
                continue

            district_dictionary = {
                'district_name': data_points[0].get_text(),
                'confirmed': int(data_points[1].get_text().strip()),
                'recovered': int(data_points[3].get_text().strip()),
                'deceased': int(data_points[5].get_text().strip())
            }
            district_array.append(district_dictionary)

        self.delta_calculator.get_state_data_from_site("Gujarat", district_array, self.option)

    @staticmethod
    def tg_get_data():
        """
        This just prints out the image values. There's no comparision with dashboard
        """
        with open(".tmp/tg.txt", "r", encoding="utf-8") as tg_file:
            for line in tg_file:
                lines_array = line.split('|')[0].split(',')
                if len(lines_array) != 2:
                    print(f"--> Issue with {lines_array}")
                    continue
                if lines_array[0].strip().capitalize() == "Ghmc":
                    lines_array[0] = "Hyderabad"
                print(f"{lines_array[0].strip().title()},"
                      f"Telangana,TG,"
                      f"{lines_array[1].strip()},Hospitalized")

    def up_get_data(self):
        """
        This supports two formats. UP Uses these interchangeably
        :return:
        """
        error_count = 0
        district_array = []

        if self.type_of_automation == "ocr1":
            length_of_array = 7
            active_index = 6
            recovered_index = 3
            deceased_index = 5
        else:
            self.type_of_automation = "ocr2"
            length_of_array = 8
            active_index = 7
            recovered_index = 4
            deceased_index = 6
        print(f"--> Using format {self.type_of_automation}")

        try:
            with open(".tmp/up.txt", "r", encoding="utf-8") as up_file:
                for line in up_file:
                    split_array = re.sub('\n', '', line.strip()).split('|')
                    lines_array = split_array[0].split(',')

                    if error_count > 10:

                        if self.type_of_automation == "ocr1":
                            self.type_of_automation = "ocr2"
                        else:
                            self.type_of_automation = "ocr1"
                        print(f"--> Switching to version {self.type_of_automation}. "
                              f"Error count breached.")
                        self.up_get_data()
                        return

                    if len(lines_array) != length_of_array:
                        print(f"--> Issue with {lines_array}")
                        error_count += 1
                        continue

                    district_dictionary = {
                        'district_name': lines_array[0].strip(),
                        'confirmed': int(lines_array[recovered_index]) + int(
                            lines_array[deceased_index]) + int(lines_array[active_index]),
                        'recovered': int(lines_array[recovered_index]),
                        'deceased': int(lines_array[deceased_index])
                    }

                    district_array.append(district_dictionary)

            self.delta_calculator.get_state_data_from_site(
                "Uttar Pradesh",
                district_array, self.option)
        except FileNotFoundError:
            print("up.txt missing. Generate through pdf or ocr and rerun.")

    def ut_get_data(self):
        """
        UT get data
        :return:
        """
        district_array = []
        ignore_lines = False
        try:
            with open(".tmp/ut.txt", "r", encoding="utf-8") as ut_file:
                for line in ut_file:
                    if ignore_lines is True:
                        continue

                    if 'Total' in line:
                        ignore_lines = True
                        continue

                    lines_array = line.split('|')[0].split(',')
                    if len(lines_array) != 6:
                        print(f"--> Issue with {lines_array}")
                        continue

                    district_dictionary = {
                        'district_name': lines_array[0].strip(),
                        'confirmed': int(lines_array[1]),
                        'recovered': int(lines_array[2]),
                        'deceased': int(lines_array[4]),
                        'migrated': int(lines_array[5])
                    }

                    district_array.append(district_dictionary)

            self.delta_calculator.get_state_data_from_site(
                "Uttarakhand",
                district_array, self.option)
        except FileNotFoundError:
            print("br.txt missing. Generate through pdf or ocr and rerun.")

    def br_get_data(self):
        """
        BR get data - make sure to crop the image to consist only of the table
        :return:
        """
        district_array = []
        try:
            with open(".tmp/br.txt", "r", encoding="utf-8") as br_file:
                for line in br_file:
                    lines_array = line.split('|')[0].split(',')
                    if len(lines_array) != 5:
                        print(f"--> Issue with {lines_array}")
                        continue

                    district_dictionary = {
                        'district_name': lines_array[0].strip(),
                        'confirmed': int(lines_array[1]),
                        'recovered': int(lines_array[2]),
                        'deceased': int(lines_array[3])
                    }

                    district_array.append(district_dictionary)

            self.delta_calculator.get_state_data_from_site("Bihar", district_array, self.option)
        except FileNotFoundError:
            print("br.txt missing. Generate through pdf or ocr and rerun.")

    def jh_get_data(self):
        """
        JH Get data
        :return:
        """
        if self.type_of_automation == "ocr":
            self.jh_get_data_by_ocr()
        else:
            self.jh_get_data_by_url()

    @staticmethod
    def jh_get_data_by_url():
        """
        Newly discovered dashboard. Updates do not match with bulletins
        :return:
        """
        url = "https://covid19dashboard.jharkhand.gov.in/Bulletin/GetTestCaseData?date=2021-03-25"

        payload = "date=" + (datetime.date.today()
                             - datetime.timedelta(days=0)).strftime("%Y-%m-%d")
        headers = {
            'Host': 'covid19dashboard.jharkhand.gov.in',
            'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
            'Content-Length': '15',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Cookie': 'ci_session=i6qt39o41i7gsopt23ipm083hla6994c'
        }

        response = requests.request("POST", url, headers=headers, data=payload)
        soup = BeautifulSoup(response.content, 'html.parser')
        districts = soup.find("table").find_all("tr")

        district_start = False
        for district in districts:

            if "Bokaro" in district.get_text() and district_start is False:
                district_start = True

            if district_start is False:
                continue

            data = district.find_all("td")

            if int(data[3].get_text()) != 0:
                print(f"{data[1].get_text()},Jharkhand,JH,{data[3].get_text()},Hospitalized")
            if int(data[4].get_text()) != 0:
                print(f"{data[1].get_text()},Jharkhand,JH,{data[4].get_text()},Recovered")
            if int(data[6].get_text()) != 0:
                print(f"{data[1].get_text()},Jharkhand,JH,{data[6].get_text()},Deceased")

    def jh_get_data_by_ocr(self):
        """
        jh get data by ocr
        :return:
        """
        district_array = []
        try:
            with open(".tmp/jh.txt", "r", encoding="utf-8") as jh_file:
                for line in jh_file:
                    lines_array = line.split('|')[0].split(',')
                    if len(lines_array) != 8:
                        print(f"--> Issue with {lines_array}")
                        continue

                    district_dictionary = {
                        'district_name': lines_array[0].strip(),
                        'confirmed': int(lines_array[4]) + int(lines_array[5]),
                        'recovered': int(lines_array[2]) + int(lines_array[6]),
                        'deceased': int(lines_array[3]) + int(lines_array[7])
                    }

                    district_array.append(district_dictionary)

            self.delta_calculator.get_state_data_from_site("Jharkhand", district_array, self.option)
        except FileNotFoundError:
            print("jh.txt missing. Generate through pdf or ocr and rerun.")

    def rj_get_data(self):
        """
        rj get data
        :return:
        """
        district_array = []
        skip_values = False
        try:
            with open(".tmp/rj.txt", "r", encoding="utf-8") as rj_file:
                for line in rj_file:
                    if 'Other' in line:
                        skip_values = True
                        continue
                    if skip_values is True:
                        continue

                    lines_array = line.split('|')[0].split(',')

                    if len(lines_array) != 9:
                        print(f"--> Issue with {lines_array}")
                        continue

                    district_dictionary = {
                        'district_name': lines_array[0].strip().title(),
                        'confirmed': int(lines_array[3]),
                        'recovered': int(lines_array[7]),
                        'deceased': int(lines_array[5])
                    }

                    district_array.append(district_dictionary)

            self.delta_calculator.get_state_data_from_site("Rajasthan", district_array, self.option)
        except FileNotFoundError:
            print("rj.txt missing. Generate through pdf or ocr and rerun.")

    def mp_get_data(self):
        """
        Make sure to crop out only the table
        :return:
        """
        district_array = []
        try:
            with open(".tmp/mp.txt", "r", encoding="utf-8") as mp_file:
                is_ignore_flag_set = False
                for line in mp_file:
                    lines_array = line.split('|')[0].split(',')
                    if 'Total' in line or is_ignore_flag_set is True:
                        is_ignore_flag_set = True
                        print(f"--> Issue with {lines_array}")
                    if len(lines_array) != 8:
                        print(f"--> Issue with {lines_array}")
                        continue
                    try:
                        if is_number(lines_array[0].strip()):
                            print(f"--> Issue with {lines_array}")
                            continue

                        district_dictionary = {
                            'district_name': lines_array[0].strip().title(),
                            'confirmed': int(lines_array[2]),
                            'recovered': int(lines_array[6]),
                            'deceased': int(lines_array[4]) if len(
                                re.sub('\n', '', lines_array[4])) != 0 else 0
                        }

                        district_array.append(district_dictionary)
                    except ValueError:
                        print(f"--> Issue with {lines_array}")
                        continue

            self.delta_calculator.get_state_data_from_site(
                "Madhya Pradesh",
                district_array, self.option)
        except FileNotFoundError:
            print("mp.txt missing. Generate through pdf or ocr and rerun.")

    def jk_get_data(self):
        """
        There are rows with Jammu and Kashmir division details.
        Those come out as errors
        :return:
        """
        district_array = []
        try:
            with open(".tmp/jk.txt", "r", encoding="utf-8") as state_file:

                for line in state_file:
                    lines_array = line.split('|')[0].split(',')
                    if len(lines_array) != 11:
                        print(f"--> Issue with {lines_array}")
                        continue

                    try:
                        if is_number(lines_array[0].strip()):
                            print(f"--> Issue with {lines_array}")
                            continue

                        district_dictionary = {
                            'district_name': lines_array[0].strip().title(),
                            'confirmed': int(lines_array[6]),
                            'recovered': int(lines_array[9]),
                            'deceased': int(lines_array[10]) if len(
                                re.sub('\n', '', lines_array[10])) != 0 else 0
                        }

                        district_array.append(district_dictionary)
                    except ValueError:
                        print(f"--> Issue with {lines_array}")
                        continue

            state_file.close()
            self.delta_calculator.get_state_data_from_site(
                "Jammu and Kashmir", district_array, self.option)
        except FileNotFoundError:
            print("rj.txt missing. Generate through pdf or ocr and rerun.")

    def wb_get_data(self):
        """
        wb get data
        :return:
        """
        district_array = []
        self.read_file_from_url_v2(
            self.meta_dictionary['West Bengal'].url,
            "West Bengal", "Alipurduar", "TOTAL")
        try:
            with open(".tmp/wb.csv", "r", encoding="utf-8") as state_file:
                for line in state_file:
                    lines_array = line.split(',')
                    if len(lines_array) != 4:
                        print(f"--> Issue with {lines_array}")
                        continue

                    district_dictionary = {
                        'district_name': lines_array[0].strip().title(),
                        'confirmed': int(lines_array[1]),
                        'recovered': int(lines_array[2]),
                        'deceased': int(lines_array[3]) if len(
                            re.sub('\n', '', lines_array[3])) != 0 else 0
                    }

                    district_array.append(district_dictionary)

            state_file.close()
            self.delta_calculator.get_state_data_from_site(
                "West Bengal",
                district_array, self.option)
        except FileNotFoundError:
            print("wb.txt missing. Generate through pdf or ocr and rerun.")

    def pb_get_data(self):
        """
        pb get data
        :return:
        """
        if self.type_of_automation == "pdf":
            self.pb_get_data_by_pdf()
        else:
            self.pb_get_data_by_ocr()

    def pb_get_data_by_pdf(self):
        """
        pb get data by pdf
        :return:
        """
        district_array = []
        self.read_file_from_url_v2(
            self.meta_dictionary['Punjab'].url,
            "Punjab", "Ludhiana", "Total")
        try:
            with open(".tmp/pb.csv", "r", encoding="utf-8") as state_file:
                for line in state_file:
                    lines_array = line.split(',')
                    if len(lines_array) != 5:
                        print(f"--> Issue with {lines_array}")
                        continue

                    district_dictionary = {
                        'district_name': lines_array[0].strip().title(),
                        'confirmed': int(lines_array[1]),
                        'recovered': int(lines_array[3]),
                        'deceased': int(lines_array[4]) if len(
                            re.sub('\n', '', lines_array[4])) != 0 else 0
                    }

                    district_array.append(district_dictionary)

            state_file.close()
            self.delta_calculator.get_state_data_from_site("Punjab", district_array, self.option)
        except FileNotFoundError:
            print("pb.txt missing. Generate through pdf or ocr and rerun.")

    def pb_get_data_by_ocr(self):
        """
        Make sure to crop the exact table.
        :return:
        """
        district_array = []
        try:
            with open(".tmp/pb.txt", "r", encoding="utf-8") as state_file:
                for line in state_file:
                    split_array = re.sub('\n', '', line.strip()).split('|')
                    lines_array = split_array[0].split(',')

                    if len(lines_array) != 5:
                        print(f"--> Issue with {lines_array}")
                        continue
                    if lines_array[0].strip() == "Total":
                        continue
                    district_dictionary = {
                        'district_name': lines_array[0].strip().title(),
                        'confirmed': int(lines_array[1]),
                        'recovered': int(lines_array[3]),
                        'deceased': int(lines_array[4]) if len(
                            re.sub('\n', '', lines_array[4])) != 0 else 0
                    }
                    district_array.append(district_dictionary)

            state_file.close()

            self.delta_calculator.get_state_data_from_site("Punjab", district_array, self.option)
        except FileNotFoundError:
            print("pb.txt missing. Generate through pdf or ocr and rerun.")

    def ka_get_data(self):
        """
        ka get data
        """
        if self.type_of_automation == "ocr":
            self.ka_get_data_by_ocr()
        else:
            self.ka_get_data_by_url()

    def ka_get_data_by_ocr(self):
        """
        This is an alternative solution if pdf image only is available.
        Not used frequently
        :return:
        """
        district_array = []

        with open(".tmp/ka.txt", encoding="utf-8") as ka_file:
            for line in ka_file:
                line = line.replace('"', '').replace('*', '').replace('#', '').replace('$', '')
                lines_array = line.split('|')[0].split(',')
                if len(lines_array) != 9:
                    print(f"--> Issue with {lines_array}")
                    continue

                district_dictionary = {
                    'district_name': lines_array[0].strip().title(),
                    'confirmed': int(lines_array[2]),
                    'recovered': int(lines_array[4]),
                    'deceased': int(lines_array[7]) if len(
                        re.sub('\n', '', lines_array[7])) != 0 else 0
                }

                district_array.append(district_dictionary)
        ka_file.close()
        self.delta_calculator.get_state_data_from_site("Karnataka", district_array, self.option)

    def ka_get_data_by_url(self):
        """
        Make sure you pass the actual GDrive url
        :return:
        """
        district_array = []
        run_deceased = False
        start_id = 0
        end_id = 0

        if ',' in self.page_id:
            start_id = self.page_id.split(',')[1]
            end_id = self.page_id.split(',')[2]
            self.page_id = self.page_id.split(',')[0]
            run_deceased = True
        file_id = 0
        if len(self.pdf_url) != 0:
            url_array = self.pdf_url.split('/')
            for index, parts in enumerate(url_array):
                if parts == "file":
                    if url_array[index + 1] == "d":
                        file_id = url_array[index + 2]
                        break
            self.pdf_url = "https://docs.google.com/uc?export=download&id=" + file_id
            print(f"--> Downloading using: {self.pdf_url}")
        self.read_file_from_url_v2('', "Karnataka", "Bagalakote", "Total")
        try:
            with open(".tmp/ka.csv", "r", encoding="utf-8") as state_file:
                for line in state_file:
                    lines_array = line.split(',')
                    if len(lines_array) != 4:
                        print(f"--> Issue with {lines_array}")
                        continue

                    district_dictionary = {
                        'district_name': lines_array[0].strip().title(),
                        'confirmed': int(lines_array[1]),
                        'recovered': int(lines_array[2]),
                        'deceased': int(lines_array[3]) if len(
                            re.sub('\n', '', lines_array[3])) != 0 else 0
                    }

                    district_array.append(district_dictionary)

            state_file.close()
            self.delta_calculator.get_state_data_from_site("Karnataka", district_array, self.option)

            if run_deceased is True:
                os.system("python3 kaautomation.py d "
                          + str(start_id) + " "
                          + str(end_id)
                          + " && cat kaconfirmed.csv")

        except FileNotFoundError:
            print("ka.txt missing. Generate through pdf or ocr and rerun.")

    def hr_get_data(self):
        """
        Nothing to report here
        :return:
        """
        district_array = []
        if self.type_of_automation == "pdf":
            self.read_file_from_url_v2(
                self.meta_dictionary['Haryana'].url,
                "Haryana", "Gurugram", "Total")
        try:
            with open(".tmp/hr.csv", "r", encoding="utf-8") as state_file:
                for line in state_file:
                    lines_array = line.split(',')
                    if len(lines_array) != 4:
                        print(f"--> Issue with {lines_array}")
                        continue

                    district_dictionary = {
                        'district_name': lines_array[0].strip().title(),
                        'confirmed': int(lines_array[1]),
                        'recovered': int(lines_array[2]),
                        'deceased': int(lines_array[3]) if len(
                            re.sub('\n', '', lines_array[3])) != 0 else 0
                    }

                    district_array.append(district_dictionary)

            state_file.close()
            self.delta_calculator.get_state_data_from_site("Haryana", district_array, self.option)
        except FileNotFoundError:
            print("hr.csv missing. Generate through pdf or ocr and rerun.")

    def tn_get_data(self):
        """
        tn get data
        :return:
        """
        district_array = []
        if self.type_of_automation == "ocr":
            self.tn_get_data_by_ocr()
            return

        self.convert_tn_pdf_to_csv()
        try:
            with open(".tmp/tn.csv", "r", encoding="utf-8") as state_file:
                for line in state_file:
                    lines_array = line.split(',')
                    if len(lines_array) != 4:
                        print(f"--> Issue with {lines_array}")
                        continue
                    lines_array[3] = lines_array[3].replace('$', '')
                    district_dictionary = {
                        'district_name': lines_array[0].strip().title(),
                        'confirmed': int(lines_array[1]),
                        'recovered': int(lines_array[2]),
                        'deceased': int(lines_array[3]) if len(
                            re.sub('\n', '', lines_array[3])) != 0 else 0
                    }

                    district_array.append(district_dictionary)

            state_file.close()
            self.delta_calculator.get_state_data_from_site(
                "Tamil Nadu",
                district_array,
                self.option)
        except FileNotFoundError:
            print("tn.txt missing. Generate through pdf or ocr and rerun.")

    def tn_get_data_by_ocr(self):
        """
        This is an alternative in case only image of pdf is present.
        Airport and railway entries might need tweaking
        :return:
        """
        district_array = []
        airport_dictionary = {'district_name': 'Airport Quarantine',
                              "confirmed": 0,
                              "recovered": 0,
                              "deceased": 0}
        with open(".tmp/tn.txt", encoding="utf-8") as tn_file:
            for line in tn_file:
                line = line.replace('"', '').replace('*', '').replace('#', '').replace('$', '')
                lines_array = line.split('|')[0].split(',')
                if len(lines_array) != 5:
                    print(f"--> Issue with {lines_array}")
                    continue

                if 'Airport' in line:
                    airport_dictionary['confirmed'] += int(lines_array[1])
                    airport_dictionary['recovered'] += int(lines_array[2])
                    airport_dictionary['deceased'] += int(lines_array[4]) if len(
                        re.sub('\n', '', lines_array[4])) != 0 else 0
                    continue

                if 'Railway' in line:
                    lines_array[0] = 'Railway Quarantine'

                district_dictionary = {
                    'district_name': lines_array[0].strip().title(),
                    'confirmed': int(lines_array[1]),
                    'recovered': int(lines_array[2]),
                    'deceased': int(lines_array[4]) if len(
                        re.sub('\n', '', lines_array[4])) != 0 else 0
                }
                district_array.append(district_dictionary)

            district_array.append(airport_dictionary)
            tn_file.close()
            self.delta_calculator.get_state_data_from_site(
                "Tamil Nadu",
                district_array,
                self.option
            )

    def convert_tn_pdf_to_csv(self):
        """
        just convert to csv. don't calculate anything
        :return:
        """
        if len(self.pdf_url) > 0:
            response = requests.get(self.pdf_url, allow_redirects=True, verify=False)
            with open(".tmp/tn.pdf", 'wb') as tn_pdf:
                tn_pdf.write(response.content)

        tables = camelot.read_pdf('.tmp/tn.pdf', strip_text='\n', pages="6", split_text=True)
        tables[0].to_csv('.tmp/tn.pdf.txt')

        with open(".tmp/" + 'tn.csv', 'w', encoding="utf-8") as tn_output_file:

            started_reading_districts = False
            airport_run = 1
            airport_confirmed_count = 0
            airport_recovered_count = 0
            airport_deceased_count = 0
            with open('.tmp/tn.pdf.txt', newline='', encoding="utf-8") as csvfile:
                row_reader = csv.reader(csvfile, delimiter=',', quotechar='"')

                for row in row_reader:
                    line = '|'.join(row)

                    if 'Ariyalur' in line:
                        started_reading_districts = True
                    if 'Total' in line:
                        started_reading_districts = False

                    if started_reading_districts is False:
                        continue

                    line = line.replace('"', '') \
                        .replace('*', '') \
                        .replace('#', '') \
                        .replace(',', '').replace('$', '')

                    lines_array = line.split('|')

                    if len(lines_array) < 6:
                        print(f"--> Ignoring line: {line} due to less columns")
                        continue

                    if 'Airport' in line:
                        airport_confirmed_count += int(lines_array[2])
                        airport_recovered_count += int(lines_array[3])
                        airport_deceased_count += int(lines_array[5])
                        if airport_run == 1:
                            airport_run += 1
                        else:
                            print(
                                f"{'Airport Quarantine'}, "
                                f"{airport_confirmed_count}, "
                                f"{airport_recovered_count}, "
                                f"{airport_deceased_count}\n", file=tn_output_file)
                        continue
                    if 'Railway' in line:
                        print(f"{'Railway Quarantine'}, "
                              f"{lines_array[2]}, "
                              f"{lines_array[3]}, {lines_array[5]}",
                              file=tn_output_file)
                        continue

                    print(f"{lines_array[1]}, {lines_array[2]}, {lines_array[3]}, {lines_array[5]}",
                          file=tn_output_file)

    def nl_get_data(self):
        """
        NL bulletins are of bad quality
        :return:
        """
        district_array = []
        if self.type_of_automation == "ocr":
            try:
                with open(".tmp/nl.txt", "r", encoding="utf-8") as state_file:
                    for line in state_file:
                        lines_array = line.split('|')[0].split(',')
                        if len(lines_array) != 13:
                            print(f"--> Issue with {lines_array}")
                            continue

                        district_dictionary = {
                            'district_name': lines_array[0].strip().title(),
                            'confirmed': int(lines_array[12]),
                            'recovered': int(lines_array[7]),
                            'migrated': int(lines_array[11]),
                            'deceased': int(lines_array[8]) if len(
                                re.sub('\n', '', lines_array[8])) != 0 else 0
                        }

                        district_array.append(district_dictionary)

                state_file.close()
                self.delta_calculator.get_state_data_from_site(
                    "Nagaland", district_array, self.option
                )
            except FileNotFoundError:
                print("hr.csv missing. Generate through pdf or ocr and rerun.")

    def ga_get_data(self):
        pass

    @staticmethod
    def as_get_data_through_ocr():
        """
        Doesn't do anything more than print out image in text format
        :return:
        """
        try:
            with open(".tmp/as.txt", "r", encoding="utf-8") as state_file:
                for line in state_file:
                    split_array = re.sub('\n', '', line.strip()).split('|')
                    lines_array = split_array[0].split(',')
                    if int(lines_array[len(lines_array) - 1]) > 0:
                        print(
                            f"{lines_array[0].strip()},"
                            f"Assam,AS,"
                            f"{lines_array[len(lines_array) - 1].strip()},"
                            f"Hospitalized")

        except FileNotFoundError:
            print("pb.txt missing. Generate through pdf or ocr and rerun.")

    def as_get_data(self):
        """
        AS dashboard is defunct now. Code is retained for legacy purposes
        :return:
        """
        if self.type_of_automation == "ocr":
            self.as_get_data_through_ocr()
            return
        response = requests.request("GET", self.meta_dictionary['Assam'].url)
        soup = BeautifulSoup(response.content, 'html.parser')
        table = soup.find("tbody").find_all("tr")

        district_array = []
        for index, row in enumerate(table):
            data_points = row.find_all("td")

            district_dictionary = {'district_name': data_points[0].get_text().strip(),
                                   'confirmed': int(data_points[1].get_text().strip())
                                   if '-' not in data_points[1].get_text().strip() else 0,
                                   'recovered': int(data_points[3].get_text().strip())
                                   if '-' not in data_points[3].get_text().strip() else 0,
                                   'deceased': int(data_points[4].get_text().strip())
                                   if '-' not in data_points[4].get_text().strip() else 0}
            district_array.append(district_dictionary)

        self.delta_calculator.get_state_data_from_site("Assam", district_array, self.option)

    def tr_get_data(self):
        """
        Nothing to report here
        :return:
        """
        response = requests.request("GET", self.meta_dictionary['Tripura'].url)
        soup = BeautifulSoup(response.content, 'html.parser')
        table = soup.find("tbody").find_all("tr")

        district_array = []
        for index, row in enumerate(table):
            data_points = row.find_all("td")

            district_dictionary = {
                'district_name': data_points[1].get_text().strip(),
                'confirmed': int(data_points[8].get_text().strip()),
                'recovered': int(data_points[10].get_text().strip()),
                'deceased': int(data_points[12].get_text().strip())
            }

            district_array.append(district_dictionary)

        self.delta_calculator.get_state_data_from_site("Tripura", district_array, self.option)

    def py_get_data(self):
        """
        Not sure how often the dashboard is updated now
        :return:
        """
        response = requests.request("GET", self.meta_dictionary['Puducherry'].url)
        soup = BeautifulSoup(response.content, 'html.parser')
        table = soup.find_all("tbody")[1].find_all("tr")

        district_array = []
        for index, row in enumerate(table):
            data_points = row.find_all("td")

            district_dictionary = {
                'district_name': data_points[0].get_text().strip(),
                'confirmed': int(data_points[1].get_text().strip()),
                'recovered': int(data_points[2].get_text().strip()),
                'deceased': int(data_points[4].get_text().strip())
            }

            district_array.append(district_dictionary)

        self.delta_calculator.get_state_data_from_site("Puducherry", district_array, self.option)

    def ch_get_data(self):
        """
        Not sure how often the dashboard is updated now
        :return:
        """
        response = requests.request("GET", self.meta_dictionary['Chandigarh'].url)
        soup = BeautifulSoup(response.content, 'html.parser')
        divs = soup.find("div", {"class": "col-lg-8 col-md-9 form-group pt-10"}) \
            .find_all("div", {"class": "col-md-3"})

        district_dictionary = {}
        district_array = []
        district_dictionary['district_name'] = 'Chandigarh'

        for index, row in enumerate(divs):

            if index > 2:
                continue

            data_points = row.find("div", {"class": "card-body"}).get_text()

            if index == 0:
                district_dictionary['confirmed'] = int(data_points)
            if index == 1:
                district_dictionary['recovered'] = int(data_points)
            if index == 2:
                district_dictionary['deceased'] = int(data_points)

        district_array.append(district_dictionary)
        self.delta_calculator.get_state_data_from_site("Chandigarh", district_array, self.option)

    def kl_get_data(self):
        """
        KL get data
        :return:
        """
        if self.type_of_automation == "pdf":
            self.kl_get_data_through_pdf()
        elif self.type_of_automation == "url":
            self.kl_get_data_through_url()

    def kl_get_data_through_pdf(self):
        """
        Prints only the confirmed and recovery numbers based on bulletin
        :return:
        """

        self.read_file_from_url_v2(
            self.meta_dictionary['Kerala'].url,
            "Kerala", "District", "Total"
        )

        try:
            with open(".tmp/kl.csv", "r", encoding="utf-8") as state_file:
                for line in state_file:
                    lines_array = line.split(',')
                    if len(lines_array) != 3:
                        print(f"--> Issue with {lines_array}")
                        continue
                    print(f"{lines_array[0].strip().title()},"
                          f"Kerala,KL,"
                          f"{lines_array[1].strip()},"
                          f"Hospitalized")
                    print(f"{lines_array[0].strip().title()},"
                          f"Kerala,KL,"
                          f"{lines_array[2].strip()},"
                          f"Recovered")

            state_file.close()
        except FileNotFoundError:
            print("ap.csv missing. Generate through pdf or ocr and rerun.")

    def kld_get_data(self):
        """
        Prints only the deceased details based on bulletin
        :return:
        """
        self.read_file_from_url_v2(
            self.meta_dictionary['KeralaDeaths'].url,
            "KeralaDeaths", "District", ""
        )
        try:
            with open(".tmp/kld.csv", "r", encoding="utf-8") as state_file:
                for line in state_file:
                    lines_array = line.split(',')
                    if len(lines_array) != 3:
                        print(f"--> Issue with {lines_array}")
                        continue
                    gender = "M" if lines_array[2].strip() == "Male" else "F"
                    print(
                        f"{lines_array[1]},{gender},,"
                        f"{lines_array[0].strip().title()},"
                        f"Kerala,KL,1,Deceased"
                    )

            state_file.close()
        except FileNotFoundError:
            print("ap.csv missing. Generate through pdf or ocr and rerun.")

    def ml_get_data(self):
        """
        Dashboard is heavily used.
        OCR is occasionally used.
        :return:
        """
        if self.type_of_automation == "ocr":
            self.ml_get_data_through_ocr()
            return

        response = requests.request("GET", "https://mbdasankalp.in/auth/local/embed")
        auth_key = json.loads(response.text)['key']

        url = "https://mbdasankalp.in/api/elasticsearch" \
              "/aggregation/or/db/merge?access_token=" + auth_key

        payload = "{\"aggregation\":{\"XAxisHeaders\":[{\"TagId\":\"5dd151b22fc63e490ca55ad6\"," \
                  "\"Header\":false,\"dbId\":\"5f395a260deffa1bd752be4e\"}]," \
                  "\"IsXaxisParallel\":false,\"YAxisHeaders\":[{\"Operator\":" \
                  "\"COUNT_DISTINCT\",\"isHousehold\":true,\"Header\":false," \
                  "\"dbId\":\"5f395a260deffa1bd752be4e\"}],\"IsYaxisParallel\":true," \
                  "\"YAxisFormulae\":[{\"isHousehold\":false,\"Instance\":\"\"," \
                  "\"axisId\":\"9100b461-5d86-47f9-b11c-6d48f90f9cf9\",\"isFormulaAxis\":true," \
                  "\"formulaId\":\"5f395d6f0deffa1bd752bee8\"," \
                  "\"dbIds\":[\"5f395a260deffa1bd752be4e\"]}," \
                  "{\"isHousehold\":false,\"Instance\":\"\"," \
                  "\"axisId\":\"5b94c49f-7c8e-4bdf-9c8b-e7af4e53e14d\"," \
                  "\"isFormulaAxis\":true,\"formulaId\":\"5f395dba0deffa1bd752bef2\"," \
                  "\"dbIds\":[\"5f395a260deffa1bd752be4e\"]}," \
                  "{\"isHousehold\":false,\"Instance\":\"\"," \
                  "\"axisId\":\"3a36866c-956d-48b2-a47c-1149a0334f29\"," \
                  "\"isFormulaAxis\":true,\"formulaId\":\"5f395dd80deffa1bd752bef5\"," \
                  "\"dbIds\":[\"5f395a260deffa1bd752be4e\"]},{\"isHousehold\":false," \
                  "\"Instance\":\"\",\"axisId\":\"a714425e-e78f-4dd7-833a-636a3bb850ca\"," \
                  "\"isFormulaAxis\":true,\"formulaId\":\"5f395d9a0deffa1bd752beef\"," \
                  "\"dbIds\":[\"5f395a260deffa1bd752be4e\"]}]}," \
                  "\"dbId\":\"5f395a260deffa1bd752be4e\",\"tagFilters\":[]," \
                  "\"sorting\":{\"axis\":{\"id\":\"5f395d6f0deffa1bd752bee8\"," \
                  "\"axisId\":\"9100b461-5d86-47f9-b11c-6d48f90f9cf9\"," \
                  "\"operator\":\"rowcount\"},\"sort\":{\"orderBy\":\"count\"," \
                  "\"order\":\"desc\"},\"size\":9999,\"enabled\":true," \
                  "\"histogram\":false,\"timeseries\":false},\"customBins\":[]," \
                  "\"tagStatus\":true,\"boxplot\":false," \
                  "\"requestedDbs\":{\"5f395a260deffa1bd752be4e\":{}}}"
        headers = {
            'Origin': 'https://mbdasankalp.in',
            'Referer': 'https://mbdasankalp.in/render'
                       '/chart/5f4a8e961dbba63b625ff002?c=f7f7f7&bc=121212&key=' + auth_key,
            'Host': 'mbdasankalp.in',
            'Content-Type': 'application/json',
            'Accept': 'application/json, text/plain, */*',
            'Content-Length': '1399'
        }

        response = requests.request("POST", url, headers=headers, data=payload)
        state_dashboard = json.loads(response.text.encode('utf8'))

        district_array = []
        for data in state_dashboard[0]:
            district_dictionary = {'district_name': data["name"]}
            for value in data["value"]:
                try:
                    if value["formulaId"] == "5f395d6f0deffa1bd752bee8":
                        district_dictionary['confirmed'] = int(value["value"])
                    if value["formulaId"] == "5f395dba0deffa1bd752bef2":
                        district_dictionary['recovered'] = int(value["value"])
                    if value["formulaId"] == "5f395dd80deffa1bd752bef5":
                        district_dictionary['deceased'] = int(value["value"])
                except KeyError:
                    continue
            district_array.append(district_dictionary)
        self.delta_calculator.get_state_data_from_site("Meghalaya", district_array, self.option)

    def ml_get_data_through_ocr(self):
        """
        Not used that often given that dashboard is functional
        :return:
        """
        district_array = []
        with open(".tmp/ml.txt", "r", encoding="utf-8") as ml_file:
            for line in ml_file:
                lines_array = line.split('|')[0].split(',')
                if len(lines_array) != 5:
                    print(f"--> Issue with {lines_array}")
                    continue

                district_dictionary = {
                    'district_name': lines_array[0].strip(),
                    'confirmed': int(lines_array[1].strip()),
                    'recovered': int(lines_array[3].strip()),
                    'deceased': int(lines_array[4]) if len(
                        re.sub('\n', '', lines_array[4])) != 0 else 0
                }

                district_array.append(district_dictionary)
            self.delta_calculator.get_state_data_from_site("Meghalaya", district_array, self.option)

    def mz_get_data(self):
        """
        Image has to be cropped twice.
        Once per each table.
        :return:
        """
        district_array = []
        with open(".tmp/mz.txt", encoding="utf-8") as mz_file:
            for line in mz_file:
                line = line.replace('Nil', '0')
                lines_array = line.split('|')[0].split(',')
                if len(lines_array) != 4:
                    print(f"--> Issue with {lines_array}")
                    continue

                district_dictionary = \
                    {
                        'district_name': lines_array[0].strip(),
                        'confirmed': int(lines_array[1]) +
                                     int(lines_array[2]) + int(lines_array[3]),
                        'recovered': int(lines_array[2]),
                        'deceased': int(lines_array[3]) if len(
                            re.sub('\n', '', lines_array[3])) != 0 else 0
                    }
                district_array.append(district_dictionary)

            mz_file.close()
            self.delta_calculator.get_state_data_from_site("Mizoram", district_array, self.option)

    def la_get_data(self):
        """
        Dashboard has become defunct.
        Might not get used again
        :return:
        """
        response = requests.request("GET", self.meta_dictionary['Ladakh'].url)
        soup = BeautifulSoup(response.content, 'html.parser')
        table = soup.find("table", id="tableCovidData2").find_all("tr")

        district_array = []
        district_dictionary = {}
        confirmed = table[9].find_all("td")[1]
        discharged = table[11].find_all("td")[1]
        confirmed_array = re.sub('\\r', '',
                                 re.sub(':', '',
                                        re.sub(' +', ' ',
                                               re.sub("\n", " ",
                                                      confirmed.get_text().strip()
                                                      )
                                               )
                                        )
                                 ).split(' ')

        discharged_array = re.sub('\\r', '',
                                  re.sub(':', '',
                                         re.sub(' +', ' ',
                                                re.sub("\n", " ",
                                                       discharged.get_text().strip()
                                                       )
                                                )
                                         )
                                  ).split(' ')

        district_dictionary['district_name'] = confirmed_array[0]
        district_dictionary['confirmed'] = int(confirmed_array[1])
        district_dictionary['recovered'] = int(discharged_array[1])
        district_dictionary['deceased'] = -999
        district_array.append(district_dictionary)

        district_dictionary = \
            {
                'district_name': confirmed_array[2],
                'confirmed': int(confirmed_array[3]),
                'recovered': int(discharged_array[3]),
                'deceased': -999
            }
        district_array.append(district_dictionary)

        self.delta_calculator.get_state_data_from_site("Ladakh", district_array, self.option)

    @staticmethod
    def vcm_format_line(row):
        """
        Formats line for vaccination data from MOHFW bulletin
        :param row:
        :return:
        """
        if len(row) < 5:
            row = re.sub(r"\s+", " ", " ".join(row)).split(" ")
        state = row[1]
        first_dose = re.sub(",", "", row[2])
        second_dose = re.sub(",", "", row[3])
        total_dose = re.sub(",", "", row[4])

        return state + "," + first_dose + "," + second_dose + "," + total_dose + "\n"

    @staticmethod
    def pb_format_line(row):
        """
        PB format line for pdf
        :param row:
        :return:
        """
        return row[1] + "," + row[2] + "," + row[3] + "," + row[4] + "," + row[5] + "\n"

    @staticmethod
    def kld_format_line(row):
        """
        KL format line for deaths
        :param row:
        :return:
        """
        return row[1] + "," + row[2] + "," + row[3] + "\n"

    def ka_format_line(self, row):
        """
        KA format line for pdf
        :param row:
        :return:
        """
        modified_row = []
        for value in row:
            if len(value) > 0:
                modified_row.append(value)

        if not is_number(modified_row[0]):
            district = " ".join(re.sub(' +', ' ', modified_row[0]).split(' ')[1:])
            modified_row.insert(0, 'a')
        else:
            district = re.sub(r'\*', '', modified_row[1])
        print(modified_row)

        return district + "," + modified_row[3] + \
               "," + modified_row[5] + "," + modified_row[8] + "\n"

    @staticmethod
    def hr_format_line(row):
        """
        HR format lines for pdf
        :param row:
        :return:
        """
        row[1] = re.sub(r'\*', '', row[1])
        if '[' in row[3]:
            row[3] = row[3].split('[')[0]
        if '[' in row[4]:
            row[4] = row[4].split('[')[0]
        if '[' in row[7]:
            row[7] = row[7].split('[')[0]
        if '[' in row[6]:
            row[6] = row[6].split('[')[0]

        line = row[1] + "," + row[3] + "," + row[4] + "," + str(int(row[6]) + int(row[7])) + "\n"
        return line

    @staticmethod
    def ap_format_line(row):
        """
        ap format line for pdf
        :param row:
        :return:
        """
        line = row[1] + "," + row[3] + "," + row[5] + "," + row[6] + "\n"
        return line

    @staticmethod
    def wb_format_line(row):
        """
        wb format line for pdf
        :param row:
        :return:
        """
        row[2] = re.sub(',', '', re.sub(r'\+.*', '', row[2]))
        row[3] = re.sub(',', '', re.sub(r'\+.*', '', row[3]))
        row[4] = re.sub('#', '', re.sub(',', '', re.sub(r'\+.*', '', row[4])))
        row[5] = re.sub(',', '', re.sub(r'\+.*', '', row[5]))
        line = row[1] + "," + row[2] + "," + row[3] + "," + row[4] + "\n"
        return line

    '''
        This method uses camelot package to read a pdf and then parse it into a csv file.
        In this method, we read the pdf either from the meta file or from the self.pdf_url global variable. This variable can be set from the cmd line.
        The method also takes user input for page number or allows for page number to be used from the self.page_id global variable.
        The method, reads a specific page, then for that page, decides if a line has to be ignored using starting and ending keys.
        Then the method calls a "<state_code>_format_line(row)" function that calls the corresponding function to allow for any row/line to be manipulated.
        The outputs are written to a <state_code>.csv file. This is read inside the corresponding <state_code>_get_data() functions which call delta_calculator to calculate deltas.
    '''

    def read_file_from_url_v2(self, url, state_name, start_key, end_key):
        """
        This is used for all pdf reads
        :param url:
        :param state_name:
        :param start_key:
        :param end_key:
        :return:
        """
        state_file_name = self.meta_dictionary[state_name].state_code

        if len(self.pdf_url) > 0:
            url = self.pdf_url
        if len(url) > 0:
            # print("--> Requesting download from {} ".format(url))
            response = requests.get(url, allow_redirects=True, verify=False)
            with open(".tmp/" + state_file_name + ".pdf", 'wb') as file:
                file.write(response.content)
        if len(self.page_id) > 0:
            pid = ""
            if ',' in self.page_id:
                start_page = int(self.page_id.split(',')[0])
                end_page = int(self.page_id.split(',')[1])
                for pages in range(start_page, end_page + 1, 1):
                    print(pages)
                    pid = pid + "," + str(pages) if len(pid) > 0 else str(pages)
                    print(pid)
            else:
                pid = self.page_id
        else:
            pid = input("Enter district page:")
        print(f"Running for {pid} pages")
        tables = camelot.read_pdf(".tmp/" + state_file_name +
                                  ".pdf", strip_text='\n', pages=pid, split_text=True)
        for index, table in enumerate(tables):
            tables[index].to_csv('.tmp/' + state_file_name + str(index) + '.pdf.txt')

        with open('.tmp/' + state_file_name.lower() +
                  '.csv', 'w', encoding="utf-8") as state_output_file:

            started_reading_districts = False
            for index, table in enumerate(tables):
                with open('.tmp/' + state_file_name + str(index)
                          + '.pdf.txt', newline='', encoding="utf-8") as state_csv_file:
                    row_reader = csv.reader(state_csv_file, delimiter=',', quotechar='"')
                    for row in row_reader:
                        line = "|".join(row)
                        line = re.sub(r"\|+", '|', line)
                        if start_key in line:
                            started_reading_districts = True
                        if len(end_key) > 0 and end_key in line:
                            started_reading_districts = False
                            continue
                        if not started_reading_districts:
                            continue

                        line = eval(state_file_name.lower() + "_format_line")(line.split('|'))
                        if line == "\n":
                            continue
                        print(line, file=state_output_file, end="")

    def ap_get_data_by_url(self):
        """
        placeholder
        :return:
        """

    def ar_get_data_by_pdf(self):
        """
        placeholder
        :return:
        """

    def ar_get_data_by_url(self):
        """
        placeholder
        :return:
        """

    def kl_get_data_through_url(self):
        """
        placeholder
        :return:
        """


def is_number(string):
    """
    helper function
    :param s:
    :return:
    """
    try:
        int(string)
        return True
    except ValueError:
        return False


def main():
    """
    read arguments, invoke automation class.
    Get delta printed out.
    :return:
    """
    parser = argparse.ArgumentParser()
    parser.add_argument('--state', type=str, required=True)
    parser.add_argument('--type', type=str, required=True)
    parser.add_argument('--url', type=str, required=False)
    parser.add_argument('--page_number', type=str, required=False)

    args = parser.parse_args()

    state_name = args.state
    type_of_automation = args.type
    pdf_url = args.url if args.url is not None else ""
    page_id = args.page_number if args.page_number is not None else ""

    automation = Automation(type_of_automation, pdf_url, page_id)

    try:
        eval(automation.meta_dictionary[state_name].state_code.lower() + "_get_data()")
        print("Dashboard url: " + automation.meta_dictionary[state_name].url)
    except KeyError:
        print(f"No entry found for state {state_name} in automation.meta file")


if __name__ == '__main__':
    main()
