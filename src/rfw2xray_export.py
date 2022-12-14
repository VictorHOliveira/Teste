#!/usr/bin/env python
"""
    Module that import Robot Framework test execution to XRAY.



    To compile this script we used pyinstaller (https://www.pyinstaller.org/)

    Install it with Python's pip:

        pip install pyinstaller


    Make sure that you have installed every dependencies of the script, such as lxml, requests,etc.

    Go to location path of rfw2xray_results.py and make sure that constants.py are also on that path.

    Compile with the following command:

        pyinstaller --onefile rfw2xray_results.py

    Upon executing this command a folder named 'dist/' will be created.
    The generated executable is located in that folder. It can generate executable for windows or linux.

"""
import argparse
from argparse import RawTextHelpFormatter
import sys 
if sys.version_info[0] < 3: # Python 2
    from urlparse import urljoin
else:
    from urllib.parse import urljoin
import requests
import json
import os
import lxml.etree as ET
import re
import base64
import time
from datetime import datetime
from functools import reduce # Needed for Python 3

# Imports
import constants
from rfw2xray_classes import *



#####################HEADER#######################
__author__ = "Paulo Figueira"
__copyright__ = "Copyright 2018, Altran Portugal"
__credits__ = ["Paulo Figueira", "Bruno Calado", "Rui Pinto"]

__licence__ = ""
__version__ = "1.0"
__maintainer__ = "Paulo Figueira"
__email__ = "paulo.figueira@altran.com"
__status__ = "Development"

#####################################################

#COMO COMPILAR O CODIGO l

#####################################################


# special Keywords
evidence_KWs = ['Capture Page Screenshot']
log_KWs = ['Log']


def todict(obj, classkey=None):
    """
    Methods that transforms Classes to dict

    :param obj: Class to transform to dict
    :param classkey:
    :return:
        Dict with class variables as key-value
    """

    if isinstance(obj, dict):
        data = {}
        for (k, v) in obj.items():
            data[k] = todict(v, classkey)
        return data
    elif hasattr(obj, "_ast"):
        return todict(obj._ast())
    elif hasattr(obj, "__iter__") and not isinstance(obj, str):
        return [todict(v, classkey) for v in obj]
    elif hasattr(obj, "__dict__"):
        data = dict([(key, todict(value, classkey))
                     for key, value in obj.__dict__.items()
                     if not callable(value) and not key.startswith('_')])
        if classkey is not None and hasattr(obj, "__class__"):
            data[classkey] = obj.__class__.__name__
        return data
    else:
        return obj


def _log_step(step, kw_xml, kw_name):
    """
    Check if is a log keyword, if true adds a comment to the respective test step

    :param current_step: Current test step to save log
    :param kw_xml: Current keyword XML element
    :param kw_name: Current keyword name
    :return:
        Boolean value, True if current keyword is a log Keyword, False otherwise
    """
    if kw_name in log_KWs:  # in case step is a LOGGING step
        log_args_text = [log_args.text for log_args in kw_xml.findall(constants.XPATH_LOG_ARGS)]
        if len(log_args_text) >= 2:
            # log_text, log_level, _ = log_args_text  -- Correction. We can not be sure that 3 arguments are received
            log_text = log_args_text[0]
            log_level = log_args_text[1]
            if log_level == constants.WARN or log_level == constants.ERROR:

                # add log to step comment
                step.add_to_comment('{}:{}\n'.format(log_level, log_text))

        return True
    else:
        return False


def _evidence_step(step, xml, kw_name, evidence_dir):
    """
    Check if is a evidence keyword, if true adds a evidence to the respective test step

    :param step: Current test step to save evidence
    :param xml: Current keyword XML element
    :param kw_name: Current keyword name
    :param evidence_dir: Directory where evidences are located
    :return:
        Boolean value, True if current keyword is a evidence Keyword, False otherwise
    """

    if kw_name in evidence_KWs:  # check if test step is in the evidence keywords (e.g. Capture Page Screenshot)

        # get msg from the evedence execution (it contains information regarding the evidence)
        evidence_msg = xml.find(constants.XPATH_EVIDENCE_MSG).text

        # get the evidence source file from the evidence message in html
        evidence_src_search = re.search(constants.SRC_REGEX, evidence_msg, re.IGNORECASE)

        # if found
        if evidence_src_search:
            # get path to the evidence
            evidence_src = os.path.join(os.path.dirname(evidence_dir), evidence_src_search.group(1))

            # opens evidence file to encode to base64
            with open(evidence_src, "rb") as evidence_file:
                # Need to add decode because of Python3. In Python3, without decode, this would be a <class 'bytes'>, while in Pytho2 would be <type 'str'>. Because of that, in Python3 we would have b'string'
                evidence_base64 = base64.b64encode(evidence_file.read()).decode("utf-8") 

            step.add_evidence(TestEvidence(evidence_base64, os.path.basename(evidence_src)))
        
        return True
    else:
        return False


def get_log_and_evidences_from_teststep(step_xml, teststep, xml_file):
    """
    Examine a test step to get logs or evidences and add them to test step

    :param step_xml: XML element of current step
    :param teststep: Test step class of current step
    :param xml_file: XML file

    """
    for kw_xml in step_xml.iter(constants.KW_TAG):
        # verify if is a log keyword and if positive logs the current test step
        _log_step(teststep, kw_xml, kw_xml.attrib[constants.ATTRIB_NAME])
        # verify if is a evidence keyword and if positive, saves evidence in the current test step
        _evidence_step(teststep, kw_xml, kw_xml.attrib[constants.ATTRIB_NAME], xml_file)


def _parse_test_steps(xml_file, test_xml, test, test_steps_filter, evidences_import):
    """
    Parse a test xml element and add steps to test case class

    :param xml_file: XML file
    :param test_xml: Current test xml element
    :param test: Current test class
    :param test_steps_filter: Test steps filtering
    :param evidences_import: Evidences selection
    :return: A test case class with all steps
    """
    # if any of these is TRUE it mean that we have to parse the test steps
    if test_steps_filter or evidences_import != constants.EVIDENCES_SELECTION_NONE:

        previous_step = None

        # parse XML test case steps
        for step_xml in test_xml.findall(constants.KW_TAG):
            if constants.ATTRIB_TYPE in step_xml.attrib and step_xml.attrib[constants.ATTRIB_TYPE] == constants.SETUP:
                 #  Take into accoun if setup of test failed
                if step_xml.find(constants.STATUS_TAG).attrib[constants.ATTRIB_STATUS] == constants.FAIL:
                    break # Leave for
                continue

            # get test step name
            teststep_name = step_xml.attrib[constants.ATTRIB_NAME].replace("{", "\{").replace("}", "\}")

            # get test step status
            teststep_status = step_xml.find(constants.STATUS_TAG).attrib[constants.ATTRIB_STATUS]

            teststep = TestStep(teststep_status)

            if evidences_import == constants.EVIDENCES_SELECTION_NONE:  # if importor of evidences is None continue to next test step
                continue

            elif evidences_import == constants.EVIDENCES_SELECTION_FAIL:
                #   check for special keywords given the previous test step status. Search for log/evidence keywords and
                #   teardown
                if previous_step and previous_step.status == constants.FAIL:
                    if _log_step(previous_step, step_xml, teststep_name) or \
                            _evidence_step(previous_step, step_xml, teststep_name, xml_file):
                        continue

                    if constants.ATTRIB_TYPE in step_xml.attrib:
                        kw_type = step_xml.attrib[constants.ATTRIB_TYPE]

                        #   if a test step has failed, check if the next kw is teardown. If true, treat it as a high keyword
                        if kw_type == constants.TEARDOWN:
                            # for each keyword of the test step
                            get_log_and_evidences_from_teststep(step_xml,teststep, xml_file)
                            continue
                        else:
                            continue

                if teststep_status == constants.FAIL:   # check if the current teststep status is Fail

                    # get the ERROR message from lower KW
                    # go deep to all keywords of the test step
                    for kw in step_xml.iter(constants.KW_TAG):

                        # extract evidences given that evidences filter is Fail
                        # verify if is a log keyword and if positive logs the current test step
                        _log_step(teststep, kw, kw.attrib[constants.ATTRIB_NAME])

                        # verify if is a evidence keyword and if positive, saves evidence in the current test step
                        _evidence_step(teststep, kw, kw.attrib[constants.ATTRIB_NAME], xml_file)

                        # check if the keyword has failed
                        if kw.find(constants.STATUS_TAG).attrib[constants.ATTRIB_STATUS] == constants.FAIL:
                            # get message tags
                            for msg in kw.findall(constants.MSG_TAG):
                                # check if level is failed is the positive case it corresponds to the error message
                                if msg.attrib[constants.ATTRIB_LEVEL] == constants.FAIL:
                                    teststep.add_to_comment('{}:{}\n'.format(msg.attrib[constants.ATTRIB_LEVEL], msg.text))

            else:
                #check current keyword if it is a log/evidence kw add it to the last test step
                if _log_step(previous_step, step_xml, teststep_name) or _evidence_step(previous_step, step_xml, teststep_name, xml_file):
                    continue

                if previous_step and previous_step.status == constants.FAIL:
                    if constants.ATTRIB_TYPE in step_xml.attrib:
                        kw_type = step_xml.attrib[constants.ATTRIB_TYPE]

                        # if a test step has failed, check if the next kw is teardown. If true, treat it as a high keyword
                        if kw_type == constants.TEARDOWN:

                            # for each keyword of the test step
                            get_log_and_evidences_from_teststep(step_xml, teststep, xml_file)

                            continue
                        else:
                            continue

                #in case of failure get the message from lowe kw
                if teststep_status == constants.FAIL:
                    # go deep to all keywords of the test step
                    for kw in step_xml.iter(constants.KW_TAG):
                        # check if the keyword has failed
                        if kw.find(constants.STATUS_TAG).attrib[constants.ATTRIB_STATUS] == constants.FAIL:
                            # get message tags
                            for msg in kw.findall(constants.MSG_TAG):
                                # check if level is failed is the positive case it corresponds to the error message
                                if msg.attrib[constants.ATTRIB_LEVEL] == constants.FAIL:
                                    teststep.add_to_comment('{}:{}\n'.format(msg.attrib[constants.ATTRIB_LEVEL], msg.text))

                # for each keyword of the test step
                get_log_and_evidences_from_teststep(step_xml,teststep, xml_file)

            previous_step = teststep

            if test_steps_filter:
                test.add_step(teststep)
            else:
                for evidence in teststep.evidences:
                    test.add_evidence(evidence)
                if teststep.comment:
                    test.comment += teststep.comment

            # Start of Changing
            test_status_elem = step_xml.find(constants.STATUS_TAG)
            test_step_duration = datetime.strptime(test_status_elem.attrib[constants.ATTRIB_ENDTIME], constants.DATE_ROBOT_FRAMEWORK_FORMAT) - datetime.strptime(test_status_elem.attrib[constants.ATTRIB_STARTTIME], constants.DATE_ROBOT_FRAMEWORK_FORMAT)
            teststep.add_to_comment("\nDuration of test step (h:m:s.ms) = " + str(test_step_duration)[:-3]) # present the milisseconds with only 3 digits
            # End of Changing

    return test


def _create_test_case(test_xml, test_key):
    """
    Create a test case class given the xml and the JIRA ISSUE
    :param test_xml: Current test XML element
    :param test_key: Test key of the test to create
    :return: A test case class
    """
    # get test status
    test_status_elem = test_xml.find(constants.STATUS_TAG)
    test_status_value = test_status_elem.attrib[constants.ATTRIB_STATUS]
    test_status_text = test_xml.find(constants.STATUS_TAG).text

    # get stat date time
    test_start_date = datetime.strptime(test_status_elem.attrib[constants.ATTRIB_STARTTIME],
                                        constants.DATE_ROBOT_FRAMEWORK_FORMAT).strftime(constants.DATE_XRAY_FORMAT)
    # get end date time
    test_finish_date = datetime.strptime(test_status_elem.attrib[constants.ATTRIB_ENDTIME],
                                         constants.DATE_ROBOT_FRAMEWORK_FORMAT).strftime(constants.DATE_XRAY_FORMAT)

    # create a new TestClass object
    test = TestCase(test_key, test_status_value)
    test.start = test_start_date
    test.finish = test_finish_date
    if test_status_text:
        test.comment = test_status_text

    # Start of Changing
    test_duration = datetime.strptime(test_status_elem.attrib[constants.ATTRIB_ENDTIME], constants.DATE_ROBOT_FRAMEWORK_FORMAT) - datetime.strptime(test_status_elem.attrib[constants.ATTRIB_STARTTIME], constants.DATE_ROBOT_FRAMEWORK_FORMAT)
    if (test.comment) : # Something was already written
        test.comment += "\n\nDuration of test execution (h:m:s.ms) = " + str(test_duration)[:-3] # present the milisseconds with only 3 digits
    else:
        test.comment = "Duration of test execution (h:m:s.ms) = " + str(test_duration)[:-3] # present the milisseconds with only 3 digits
    # End of Changing

    return test


def _parse_test(element, tag_filter, filter_tests, test_steps_filter, evidences_import, xml_file):
    """
    Parse a test case XML element and create a Test Case class with its steps
    :param element: Current test XML element
    :param tag_filter: Filtering of tags
    :param filter_tests: Dict to add the filtered tests
    :param test_steps_filter: Filtering of test steps
    :param evidences_import: Evidences selection
    :param xml_file: XML file
    :return: A test case class with all its steps; a JIRA test execution key if found
    """
    tag_found = ''
    testexec_key = constants.NO_TESTEXEC_KEY
    test_key = ''
    tags_text = element.xpath(constants.XPATH_TAG_TEXT)

    for tag_text in tags_text:

        if tag_filter:
            if tag_text in import_filters[constants.FILTER_TAG_KEY]:
                tag_found = tag_text

        splitted_tag_text = tag_text.split(constants.TEST_TAG_SEPARATOR)
        # verify if tag has the label JIRA_TEST
        if constants.JIRA_TEST_TAG == splitted_tag_text[0]:
            test_key = splitted_tag_text[1]  # extract tag value
            # print tag_text
            # verify if tag has the label JIRA_TESTEXEC
        if constants.JIRA_TESTEXEC_TAG == splitted_tag_text[0]:
            testexec_key = splitted_tag_text[1]

    test_case = _create_test_case(element, test_key)
    test_case = _parse_test_steps(xml_file, element, test_case, test_steps_filter,
                                  evidences_import)  # create a test case object and adds steps to it

    if tag_filter:
        if tag_found:
            filter_tests[constants.FILTER_TAG_KEY].append(test_case)


    return test_case, testexec_key


def _get_test_date(element, date_attrib):
    status = element.find(constants.STATUS_TAG)
    if status is not None:
        if status.attrib[constants.ATTRIB_ENDTIME] != constants.NO_VALUE:
            # get end date time
            return datetime.strptime(status.attrib[date_attrib],
                                                  constants.DATE_ROBOT_FRAMEWORK_FORMAT).strftime(
                constants.DATE_XRAY_FORMAT)


def filtering_import(xml_file, test_steps_filter, evidences_import, import_filters, filter_option, **kwargs):
    """
    Imports with filtering and return a test execution
    :param xml_file: Robot Framework output XML file
    :param test_steps_filter: Filtering of test steps
    :param evidences_import: Evidences Selection
    :param import_filters: Importation filters
    :param filter_option: Filter option, either intersaction or union
    :return: Test execution with the filters applied
    """
    filters_tests = {}

    test_suite_filter = False
    test_case_filter = False
    tag_filter = False

    if constants.FILTER_TEST_SUITE_KEY in import_filters:
        test_suite_filter = True
        filters_tests[constants.FILTER_TEST_SUITE_KEY] = []

    if constants.FILTER_TEST_CASE_KEY in import_filters:
        test_case_filter = True
        filters_tests[constants.FILTER_TEST_CASE_KEY] = []

    if constants.FILTER_TAG_KEY in import_filters:
        tag_filter = True
        filters_tests[constants.FILTER_TAG_KEY] = []


    tests = []
    test_execs = {}
    test_testexec_key = {}
    name = ''

    for event, element in ET.iterparse(xml_file, tag=(constants.TEST_TAG, constants.SUITE_TAG)):

        if element.tag == constants.TEST_TAG:
            test_case, testexec_key = _parse_test(element, tag_filter, filters_tests, test_steps_filter,
                                                  evidences_import, xml_file)

            test_testexec_key[test_case.testKey] = testexec_key

            if test_case_filter:
                if element.attrib[constants.ATTRIB_NAME] in import_filters[constants.FILTER_TEST_CASE_KEY]:
                    filters_tests[constants.FILTER_TEST_CASE_KEY].append(test_case)
            tests.append(test_case)

        if element.tag == constants.SUITE_TAG and constants.ATTRIB_NAME in element.attrib:
            if test_suite_filter:
                for ancestor in element.xpath(constants.XPATH_ANCESTOR):
                    if constants.ATTRIB_NAME in ancestor.attrib:
                        if ancestor.attrib[constants.ATTRIB_NAME] in import_filters[constants.FILTER_TEST_SUITE_KEY]:
                            filters_tests[constants.FILTER_TEST_SUITE_KEY] += tests

            tests = []

        #get test execution name
        if not name:
            for ancestor in element.xpath(constants.XPATH_ANCESTOR_SUITE):
                name = ancestor.attrib[constants.ATTRIB_NAME]
                break

        element.clear()
        for ancestor in element.xpath(constants.XPATH_ANCESTOR):
            while ancestor.getprevious() is not None:
                del ancestor.getparent()[0]

    if test_suite_filter or test_case_filter or tag_filter:
        filter_key_value = []
        tests = []
        for key, value in import_filters.items():
            value_filters = '_'.join(value)
            filter_key_value.append('{}_{}'.format(key, value_filters))
            tests.append(set(filters_tests[key]))
        

        if filter_option == constants.FILTER_OPTION_AND:
            result = reduce(set.intersection, tests)
        else:
            result = reduce(set.union,tests)

        result = sorted(list(result), key=lambda test: test.testKey)

        for test in result:
            testexec_key = test_testexec_key[test.testKey]
            if testexec_key in test_execs:
                test_execs[testexec_key].tests.append(test)
            else:
                test_exec = TestExec([test])
                if testexec_key != constants.NO_TESTEXEC_KEY:
                    test_exec.testExecutionKey = testexec_key
                else:
                    test_exec_info = TestExecInfo(**kwargs)

                    test_exec_info.summary = test_exec_info.summary.format(name, ':'.join(filter_key_value) + '-' +
                                                                           str(time.time()))
                    test_exec.info = test_exec_info

                test_execs[testexec_key] = test_exec

    return test_execs


def no_filtering_import(xml_file, test_steps_filter, evidences_import, **kwargs):
    """
    Import XML file with no filtering
    :param xml_file: Robot Framework XML output file
    :param test_steps_filter: Filtering of test steps
    :param evidences_import: Evidences selection
    :return: Test executions to import
    """
    test_execs = {}
    test_case_list = []

    for event, element in ET.iterparse(xml_file, tag=(constants.TEST_TAG, constants.SUITE_TAG)):

        if element.tag == constants.TEST_TAG:
            test_case, testexec_key = _parse_test(element, False, {},
                                                  test_steps_filter, evidences_import, xml_file)
            if testexec_key in test_execs:
                test_exec.add_test(test_case)

            else:
                test_exec = TestExec([test_case])

                if testexec_key != constants.NO_TESTEXEC_KEY:
                    test_exec.testExecutionKey = testexec_key
                else:
                    test_exec_info = TestExecInfo(**kwargs)
                    if not hasattr(test_exec_info, constants.TEST_EXECUTION_INFO_STARTDATE_KEY):
                        test_exec_info.startDate = _get_test_date(element, constants.ATTRIB_STARTTIME)
                    if not hasattr(test_exec_info, constants.TEST_EXECUTION_INFO_FINISHDATE_KEY):
                        test_exec_info.finishDate = _get_test_date(element, constants.ATTRIB_ENDTIME)

                    name = ''
                    for ancestor in element.xpath(constants.XPATH_ANCESTOR_SUITE):
                        name = ancestor.attrib[constants.ATTRIB_NAME]
                        break
                    test_exec_info.summary = test_exec_info.summary.format(name + ' ' + str(time.time()))
                    test_exec.info = test_exec_info
                test_execs[testexec_key] = test_exec 

        element.clear()
        for ancestor in element.xpath(constants.XPATH_ANCESTOR):
            while ancestor.getprevious() is not None:
                del ancestor.getparent()[0]

    return test_execs


def create_test_exec(data):
    """
    Sends a request to import test execution via JIRA-XRAY API

    :param data: JSON data
    :return:
        API Response
    """
    headers = {constants.CONTENT_TYPE: constants.CONTENT_TYPE_JSON}
    # Endpoit default
    url = urljoin(jira_address, endpoint)
    response = requests.post(url, headers=headers, data=data, auth=(username, password), verify = False)
    return response


def add_attachment_test_exec(test_exec_key, file):
    """
    Sends a request to add attachments to test execution

    :param test_exec_key : string
    :param file          : string
    :return:
        API Response
    """

    attachment = Attachmet(file)
    endpoint = constants.ATTACHMENT_ENDPOINT.format(test_exec_key)
    url = urljoin(jira_address, endpoint)
    headers = {constants.CONTENT_TYPE: attachment.content_type, constants.CONTENT_ATLASSIAN_TOKEN : constants.CONTENT_ATLASSIAN_TOKEN_VALUE}
    response = requests.post(url, headers=headers, data=attachment.data, auth=(username, password), verify=False)
    return response

def create_test_plan(data):
    """
    Sends a request to create test plan via JIRA-XRAY API

    :param listTestCases: data in JSON to create test plan
    :return:
        API Response
    """
    headers = {constants.CONTENT_TYPE: constants.CONTENT_TYPE_JSON}
    endpoint = constants.TEST_PLAN_ENDPOINT
    url = urljoin(jira_address, endpoint)
    response = requests.post(url, headers=headers, data=data, auth=(username, password), verify = False)
    return response


def add_test_exec_to_test_plan(data, test_plan_key):
    """
    Sends a request to add a test execution to a given test plan via JIRA-XRAY API

    :param 
        data: data in JSON to add test exec to test plan
        test_plan_key: key of test plan (it exists in JIRA)
    :return:
        API Response
    """
    headers = {constants.CONTENT_TYPE: constants.CONTENT_TYPE_JSON}
    endpoint = constants.TEST_PLAN_TEST_EXECS_ENDPOINT.format(test_plan_key)
    url = urljoin(jira_address, endpoint)
    response = requests.post(url, headers=headers, data=data, auth=(username, password), verify = False)
    return response


def add_tests_to_test_plan(data, test_plan_key):
    """
    Sends a request to add a list of tests to a given test plan via JIRA-XRAY API

    :param 
        data: data in JSON to add a list of tests to test plan
        test_plan_key: key of test plan (it exists in JIRA)
    :return:
        API Response
    """
    headers = {constants.CONTENT_TYPE: constants.CONTENT_TYPE_JSON}
    endpoint = constants.TEST_PLAN_TESTS_ENDPOINT.format(test_plan_key)
    url = urljoin(jira_address, endpoint)
    response = requests.post(url, headers=headers, data=data, auth=(username, password), verify = False)
    return response


def parse_arguments():

    if sys.version_info[0] < 3: # Python 2
        description=constants.DESCRIPTION.encode('utf-8')
    else:
        description=constants.DESCRIPTION

    parser = argparse.ArgumentParser(
        description=description,
        epilog=constants.EPILOG,
        formatter_class=RawTextHelpFormatter
    )

    parser.add_argument(constants.FILE, help=constants.FILE_HELP)
    parser.add_argument(constants.URL, help=constants.URL_HELP)
    parser.add_argument(constants.USERNAME, help=constants.USERNAME_HELP)
    parser.add_argument(constants.PASSWORD, help=constants.PASSWORD_HELP)

    parser.add_argument(constants.NO_STEPS, constants.NO_STEPS_EXTENDED, action=constants.NO_STEPS_ACTION,
                        help=constants.NO_STEPS_HELP)

    parser.add_argument(constants.ENDPOINT, constants.ENDPOINT_EXTENDED,
                        default=constants.ENDPOINT_DEFAULT, help=constants.ENDPOINT_HELP)

    parser.add_argument(constants.FILTER_TAG, constants.FILTER_TAG_EXTENDED, help=constants.FILTER_TAG_HELP,
                        action=constants.FILTER_TAG_ACTION)

    parser.add_argument(constants.FILTER_TEST_SUITE, constants.FILTER_TEST_SUITE_EXTENDED,
                        help=constants.FILTER_TEST_SUITE_HELP, action=constants.FILTER_TEST_SUITE_ACTION)

    parser.add_argument(constants.FILTER_TEST_CASE, constants.FILTER_TEST_CASE_EXTENDED,
                        help=constants.FILTER_TEST_CASE_HELP, action=constants.FILTER_TEST_CASE_ACTION)

    parser.add_argument(constants.FILTER_OPTION, constants.FILTER_OPTION_EXTENDED,
                        default=constants.FILTER_OPTION_DEFAULT, help=constants.FILTER_OPTION_HELP)

    parser.add_argument(constants.EVIDENCES_SELECTION, constants.EVIDENCES_SELECTION_EXTENDED,
                        default=constants.EVIDENCES_SELECTION_DEFAULT, help=constants.EVIDENCES_SELECTION_HELP)

    parser.add_argument(constants.DEBUG, constants.DEBUG_EXTENDED, action=constants.DEBUG_ACTION,
                        help=constants.DEBUG_HELP)

    parser.add_argument(constants.TEST_EXEC_SUMMARY, constants.TEST_EXEC_SUMMARY_EXTENDED,
                        help=constants.TEST_EXEC_SUMMARY_HELP)

    parser.add_argument(constants.TEST_EXEC_DESCRIPTION,constants.TEST_EXEC_DESCRIPTION_EXTENDED,
                        help=constants.TEST_EXEC_DESCRIPTION_HELP)

    parser.add_argument(constants.TEST_EXEC_VERSION, constants.TEST_EXEC_VERSION_EXTENDED,
                        help=constants.TEST_EXEC_VERSION_HELP)

    parser.add_argument(constants.TEST_EXEC_REVISION, constants.TEST_EXEC_REVISION_EXTENDED,
                        help=constants.TEST_EXEC_REVISION_HELP)

    parser.add_argument(constants.TEST_EXEC_USER, constants.TEST_EXEC_USER_EXTENDED,
                        help=constants.TEST_EXEC_USER_HELP)

    parser.add_argument(constants.TEST_EXEC_STARTDATE, constants.TEST_EXEC_STARTDATE_EXTENDED,
                        help=constants.TEST_EXEC_STARTDATE_HELP)

    parser.add_argument(constants.TEST_EXEC_FINISHDATE, constants.TEST_EXEC_FINISHDATE_EXTENDED,
                        help=constants.TEST_EXEC_FINISHDATE_HELP)

    parser.add_argument(constants.TEST_EXEC_TESTPLANKEY, constants.TEST_EXEC_TESTPLANKEY_EXTENDED,
                        help=constants.TEST_EXEC_TESTPLANKEY_HELP)

    parser.add_argument(constants.TEST_EXEC_TESTENV, constants.TEST_EXEC_TESTENV_EXTENDED,
                        help=constants.TEST_EXEC_TESTENV_HELP)
    
    #parser.add_argument(constants.CERTIFICATE, constants.CERTIFICATE_EXTENDED,
    #                    help=constants.CERTIFICATE_HELP)

    # Add tool version option
    parser.add_argument(constants.TOOL_VERSION, constants.TOOL_VERSION_EXTENDED, action=constants.TOOL_VERSION_TAG,
                        version=constants.TOOL_VERSION_ACTION)

    # Add test plan summary option
    parser.add_argument(constants.TEST_PLAN_SUMMARY, constants.TEST_PLAN_SUMMARY_EXTENDED,
                        help=constants.TEST_PLAN_SUMMARY_HELP)

    # Add option to create test exec ad hoc
    parser.add_argument(constants.TEST_EXEC_ADHOC, constants.TEST_EXEC_ADHOC_EXTENDED, action='store_true',
                        help=constants.TEST_EXEC_ADHOC_HELP)
    
    # Add option to add attachment
    parser.add_argument(constants.ATTACHMENT, constants.ATTACHMENT_EXTENDED, help=constants.ATTACHMENT_HELP)

    args = parser.parse_args()

    return args

def get_list_arguments(attachments):
    try:
        list_attachments = attachments.split(',')
        return list_attachments
    except Exception: # May be None. In this case return empty list
        return []


if __name__ == '__main__':

    args = parse_arguments()

    # output XML file
    file = args.file

    # JIRA server configuration
    jira_address = args.url   # 'http://10.12.7.54:8080'  # CHANGE
    endpoint = args.endpoint  # '/rest/raven/1.0/import/execution'
    username = args.username  # CHANGE
    password = args.password  # CHANGE


    # Test Filtering, filters output file to only import the required test execution.

    # filter test steps
    test_steps_filter = args.no_steps  # boolean value

    import_filters = {}

    # filter tests by tag
    filter_tag = args.filter_tag
    if filter_tag:
        import_filters[constants.FILTER_TAG_KEY] = filter_tag  # list with tag filters

    # filter tests by test suite name
    filter_test_suite = args.filter_test_suite
    if filter_test_suite:
        import_filters[constants.FILTER_TEST_SUITE_KEY] = filter_test_suite  # list with test suite filters

    # filter tests by test case name
    filter_test_case = args.filter_test_case
    if filter_test_case:
        import_filters[constants.FILTER_TEST_CASE_KEY] = filter_test_case  # list with test case filters

    # option for the relationship between filters
    filter_option = args.filter_options

    # filter evidences. None; Fail only; or All
    evidences_import = args.evidences_selection

    # debug flag
    debug_mode = args.debug

    # path to certicate
    #certificate = args.certificate if args.certificate else False

    # Test Execution Info
    test_exec_info_values = {}

    if args.test_exec_summary:
        test_exec_info_values[constants.TEST_EXECUTION_INFO_SUMMARY_KEY] = args.test_exec_summary

    if args.description:
        test_exec_info_values[constants.TEST_EXECUTION_INFO_DESCRIPTION_KEY] = args.description

    if args.test_exec_version:
        test_exec_info_values[constants.TEST_EXECUTION_INFO_VERSION_KEY] = args.test_exec_version

    if args.user:
        test_exec_info_values[constants.TEST_EXECUTION_INFO_USER_KEY] = args.user

    if args.test_exec_revision:
        test_exec_info_values[constants.TEST_EXECUTION_INFO_REVISION_KEY] = args.test_exec_revision

    if args.start_date:
        test_exec_info_values[constants.TEST_EXECUTION_INFO_STARTDATE_KEY] = args.start_date

    if args.finish_date:
        test_exec_info_values[constants.TEST_EXECUTION_INFO_FINISHDATE_KEY] = args.finish_date

    if args.test_plan_key:
        test_exec_info_values[constants.TEST_EXECUTION_INFO_TESTPLANKEY_KEY] = args.test_plan_key

    if args.test_environments:
        test_exec_info_values[constants.TEST_EXECUTION_INFO_TESTENVIRONMENTS_KEY] = args.test_environments.\
            split(constants.TEST_EXECUTION_INFO_TESTENVIRONMENTS_SEPERATOR)


    if filter_test_suite or filter_test_case or filter_tag:
        if constants.TEST_EXECUTION_INFO_SUMMARY_KEY not in test_exec_info_values:
            test_exec_info_values[constants.TEST_EXECUTION_INFO_SUMMARY_KEY] = constants.TEST_EXECUTION_SUMMARY_FILTERS

        test_execs = filtering_import(file, test_steps_filter,
                                      evidences_import, import_filters, filter_option, **test_exec_info_values)
    else:

        if constants.TEST_EXECUTION_INFO_SUMMARY_KEY not in test_exec_info_values:
            test_exec_info_values[constants.TEST_EXECUTION_INFO_SUMMARY_KEY] = constants.TEST_EXECUTION_SUMMARY

        test_execs = no_filtering_import(file, test_steps_filter, evidences_import, **test_exec_info_values)


    # Default value of test_exec_key
    test_exec_key = "Undefined"
    list_test_cases = []

    for key, test_exec in test_execs.items():
        json_data = json.dumps(todict(test_exec))
        response = create_test_exec(json_data)
        if response:
            json_response = json.loads(response.text)
            if debug_mode:
                test_keys = []
                for test in test_exec.tests:
                    test_keys.append(test.testKey)
                if hasattr(test_exec, constants.TEST_EXECUTION_KEY):

                    print(constants.DEBUG_UPDATE.format(len(test_keys), test_exec.testExecutionKey, ",".join(test_keys)))
                else:
                    print(constants.DEBUG_CREATE.format(test_exec.info.summary, len(test_exec.tests), ",".join(test_keys)))
                print(json_response)
            test_exec_key = json_response[constants.TEST_EXEC_ISSUE][constants.KEY]
            # Prepare msg before print. Makes python2 more readable
            msg = "Test Exec created: " + test_exec_key
            print(msg)
        else:
            # Prepare msg before print. Makes python2 more readable
            msg = "Error: " + str(response.status_code)
            print(msg)
            #sys.exit(1) Does not work with executable
            raise Exception(response.text)

    # Get list of attachments from arguments
    list_arguments = get_list_arguments(args.attachment)

    # Add attachements to test executions if were given as arguments.
    for filepath in list_arguments:
        response = add_attachment_test_exec(test_exec_key, filepath)
        file = os.path.basename(filepath) # get file name for better message
        if response:
            msg = file + " was added to test execution " + test_exec_key
            print(msg)
        else:
            # Prepare msg before print. Makes python2 more readable
            msg = "Could not add " + file + " to test execution. Error: " + str(response.status_code)
            print(msg)
            print(response.text)

    # Create test plan if such was not given as argument. Associate test execution created to the test plan
    # The test exec created should be done ad hoc, which means, without associated to any test plan. So, no test plan will be created and no test plan will be associated to the test execution
    if not args.test_plan_key and not args.ad_hoc:

        # Get Project Name from text_exec_key. Format: "ROBRX-123", e.g
        project_key = test_exec_key.split('-')[0]

        # Create Test Plan object, taking into account if the name was given as argument
        if args.test_plan_summary:
            newTestPlan = TestPlan(project_key,summary=args.test_plan_summary)
        else:
            newTestPlan = TestPlan(project_key)

        response = create_test_plan(newTestPlan.test_plan_json)
        test_plan_key = "Undefined"
        if response:
            json_response = json.loads(response.text)
            test_plan_key = json_response[constants.KEY]
            # Prepare msg before print. Makes python2 more readable
            msg = "Test Plan created: " + test_plan_key
            print(msg)
        else:
            # Prepare msg before print. Makes python2 more readable
            msg = "Error: " + str(response.status_code)
            print(msg)
            #sys.exit(1) Does not work with executable
            raise Exception(response.text)

        # Add test exec created to the test plan created
        newTestPlan.add_test_exec([test_exec_key])
        response = add_test_exec_to_test_plan(newTestPlan.test_plan_add_test_exec_json, test_plan_key)
        if response:
            # Prepare msg before print. Makes python2 more readable
            msg = "Test Exec " + test_exec_key + " was sucessfully linked to Test Plan " + test_plan_key
            print(msg)
        else:
            # Prepare msg before print. Makes python2 more readable
            msg = "Error: " + str(response.status_code)
            print(msg)
            #sys.exit(1) Does not work with executable
            raise Exception(response.text)

        # Get list of test cases
        dict_test_cases = todict(test_exec)
        for test_case in dict_test_cases.get("tests",""):
            list_test_cases.append(test_case.get("testKey",""))

        # Add test cases, from xml of execution (e.g output.xml), to the test plan created
        newTestPlan.add_tests(list_test_cases)
        response = add_tests_to_test_plan(newTestPlan.test_plan_add_tests_json, test_plan_key)
        if response:
            # Prepare msg before print. Makes python2 more readable
            msg = "Tests " + str(list_test_cases) + " were sucessfully linked to Test Plan " + test_plan_key
            print(msg)
        else:
            # Prepare msg before print. Makes python2 more readable
            msg = "Error: " + str(response.status_code)
            print(msg)
            #sys.exit(1) Does not work with executable
            raise Exception(response.text)