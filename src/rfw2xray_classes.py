import json
import constants
# To add attachments
from requests_toolbelt.multipart.encoder import MultipartEncoder
import os

class Attachmet:
    """
    Class that aids in attaching files to JIRA

    """
    def __init__(self, filepath):
        file = os.path.basename(filepath) # get file name
        try:
            self.data = MultipartEncoder(fields={'file':(file, open(filepath, 'rb'), 'text/plain')})
            self.content_type = self.data.content_type
        except Exception:
            msg = "Could not find/open " + filepath
            print(msg)
            exit(0)


class TestPlan:
    """
    Class that represents a XRAY Test Plan

    Args:
        tests (:obj:`list` of :obj:`TestCase`): Test Execution's test cases
    """
    def __init__(self, key, summary=constants.TEST_PLAN_SUMMARY_JIRA, description=constants.TEST_PLAN_DESCRIPTION_JIRA):
        self.test_plan_json = json.dumps({"fields" : 
        {"project" : {"key": key}, 
            "summary" : summary, 
            "description" : description,
            "issuetype" : {"name" : constants.TEST_PLAN_ISSUE_NAME}
        }})

    def add_test_exec(self, test_exec):
        self.test_plan_add_test_exec_json = json.dumps({"add" : test_exec})

    def add_tests(self, list_tests):
        self.test_plan_add_tests_json = json.dumps({"add" : list_tests})

class TestExec:
    """
    Class that represents a XRAY Test Execution

    Args:
        tests (:obj:`list` of :obj:`TestCase`): Test Execution's test cases
    """

    def __init__(self, tests=[]):
        self.tests = tests

    def add_test(self, test):
        self.tests.append(test)


class TestExecInfo:
    """
    Class that represents a XRAY Test Execution's Info

    Args:
        kwargs: Keyord arguments to set the test exec info information:
        (Summary, Description, Version, User, Revision, Start Date, Finish Date, Test Plan Key, Test Environments)
    """

    def __init__(self, **kwargs):
        for key in kwargs:
            setattr(self, key, kwargs[key])


class TestCase:
    """
    Class that represents a XRAY Test Case after execution

    Args:
        test_key (str): Jira's Test Issue key
        status (str); Test Case Execution status
    """

    def __init__(self, test_key, status):
        self.testKey = test_key
        self.status = status
        self.steps = []
        self.evidences = []
        self.comment = ''

    def add_step(self, step):
        self.steps.append(step)

    def add_evidence(self, evidence):
        self.evidences.append(evidence)


class TestStep:
    """
    Class that represents a XRAY Test Step after execution

    Args:
        status (str): Test step execution status
    """

    def __init__(self, status):
        self.status = status
        self.evidences = []
        self.comment = ''

    def add_evidence(self, evidence):
        self.evidences.append(evidence)

    def add_to_comment(self, comment):
        self.comment += comment


class TestEvidence:
    """
    Class that represents a Test Execution evidence

    Args:
        data (str): Base64 encoded string with the evidence data
        filename (str): Evidence file name
    """

    def __init__(self, data, filename):
        self.data = data
        self.filename = filename