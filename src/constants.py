#####################CONSTANTS#######################

### argparser

## Init
DESCRIPTION = "A script that imports a Robot Framework output file to JIRA's Test Execution.\n\n"\
              "Preconditions:\n"\
              "\tIn the Robot Framework, it is required to set for each test case the corresponding Jira's Test Issue. "\
              "With the prefix: \'JIRA_TEST:\', followed by the Issue's code.\n"\
              "\t\tExample:\n"\
              "\t\t\t[Tags]     JIRA_TEST:POC-000\n\n"\
              "\tAdditionally, it is possible to set an option Tag that states the Jira's Test Execution Issue to update. "\
              "With the prefix: \'JIRA_TEXTEXEC:\', followed by the Issue's code. If this tag is not set, a new Test Execution is created.\n"\
              "\t\tExample:\n"\
              "\t\t\t[Tags]     JIRA_TEST:POC-000 JIRA_TESTEXEC:POC-001\n\n\n"\
              u"\u00a9" + "2018 Altran PT All Rights Reserved"
              
EPILOG = "\n\n\nExamples: \n" \
         "Import the whole Robot Framework test execution, creating a test plan and associate the test execution to the test plan:\n" \
         "./rfw2xray_results output.xml http://127.0.0.1 myusername mypassword\n\n" \
         "Import the whole Robot Framework test execution, without creating a test plan and associate the test execution to it:\n" \
         "./rfw2xray_results output.xml http://127.0.0.1 myusername mypassword -adhoc\n\n" \
         "Import tests that have the tag ABC:\n" \
         "./rfw2xray_results output.xml http://127.0.0.1 myusername mypassword -ft ABC\n\n" \
         "Import only the tests that belong to suite DEMOSUITE and ignore their test steps:\n" \
         "./rfw2xray_results output.xml http://127.0.0.1 myusername mypassword -fts DEMOSUITE -ns\n\n" \
         "Import tests without evidences:\n" \
         "./rfw2xray_results output.xml http://127.0.0.1 myusername mypassword -es None\n\n" \
         "Import test execution and associate to a given test plan:\n" \
         "./rfw2xray_results output.xml http://127.0.0.1 myusername mypassword -pk test_plan_key\n\n" \
         "Import test execution with attachments:\n" \
         "./rfw2xray_results output.xml http://127.0.0.1 myusername mypassword -att file1.html,file2.csv"

## Argument and helper

# Positional Arguments
FILE = 'file'
FILE_HELP = 'Robot Framework output XML file'

URL = 'url'
URL_HELP = 'Jira\'s url'

USERNAME = 'username'
USERNAME_HELP = 'Credentials to access JIRA, username.'

PASSWORD = 'password'
PASSWORD_HELP = 'Credentials to access JIRA, password.'

# Optional Arguments
NO_STEPS = '-ns'
NO_STEPS_EXTENDED = '--no-steps'
NO_STEPS_ACTION = 'store_false'
NO_STEPS_HELP = 'Ignore test step status when importing result'

ENDPOINT = '-e'
ENDPOINT_EXTENDED = '--endpoint'
ENDPOINT_DEFAULT = '/rest/raven/1.0/import/execution'
ENDPOINT_HELP = 'XRAY\'s API endpoint to import test executions.\n' \
                'Default value is /rest/raven/1.0/import/execution'

FILTER_TAG = '-ft'
FILTER_TAG_EXTENDED = '--filter-tag'
FILTER_TAG_HELP = 'Apply tag filtering in the importation. Specifying a tag to filter. ' \
                  'Tag filters can be combined.\n' \
                  'Example: --filter-tag FOO --filter-tag BAR'
FILTER_TAG_ACTION = 'append'

FILTER_TEST_SUITE = '-fts'
FILTER_TEST_SUITE_EXTENDED = '--filter-test-suite'
FILTER_TEST_SUITE_HELP = 'Apply test suite filtering in the import. Specifying test suite to filter. ' \
                         'Test suite filters can be combined.\n' \
                         'Example: --filter-test-suite FOO --filter-test-suite BAR'
FILTER_TEST_SUITE_ACTION = 'append'

FILTER_TEST_CASE = '-ftc'
FILTER_TEST_CASE_EXTENDED = '--filter-test-case'
FILTER_TEST_CASE_HELP = 'Apply test case filtering in the import. Specifying test case to filter. ' \
                        'Test case filters can be combined.\n ' \
                        'Example: --filter-test-case FOO --filter-test-case BAR'

FILTER_TEST_CASE_ACTION = 'append'

FILTER_OPTION = '-fo'
FILTER_OPTION_EXTENDED = '--filter-options'
FILTER_OPTION_DEFAULT = 'AND'
FILTER_OPTION_HELP = \
    'Select the relationship among filters. It can take one of these two options:\n' \
    '- AND: The result is the intersection of all filters\n' \
    '- OR: The result is the union of all filters\n' \
    'Default value is AND.' \

FILTER_OPTION_AND = 'AND'
FILTER_OPTION_OR = 'OR'

EVIDENCES_SELECTION = '-es'
EVIDENCES_SELECTION_EXTENDED = '--evidences-selection'
EVIDENCES_SELECTION_DEFAULT = 'All'
EVIDENCES_SELECTION_HELP = 'Apply evidence selection in the importation. It can take 3 option:\n' \
                             '- None: Do not import evidences.\n' \
                             '- Fail: Only import evidences of the failed test step.\n' \
                             '- All: Imports all evidences.\n' \
                           'Default value is All'

EVIDENCES_SELECTION_NONE = 'None'
EVIDENCES_SELECTION_FAIL = 'Fail'
EVIDENCES_SELECTION_ALL = 'All'

DEBUG = '-db'
DEBUG_EXTENDED = '--debug'
DEBUG_ACTION = 'store_true'
DEBUG_HELP = 'Set debug mode ON, logging the behaviour of imports. The debug output is the following:\n' \
             '(Number of tests imported)\n' \
             '(XRAY response content and resulting test execution issues for each import).'

TEST_EXEC_SUMMARY = '-tesum'
TEST_EXEC_SUMMARY_EXTENDED = '--test-exec-summary'
TEST_EXEC_SUMMARY_HELP = 'Set the test execution name if test execution is created.\n' \
                         'Example: -s \"A new test execution of output.xml\"'

TEST_EXEC_DESCRIPTION = '-d'
TEST_EXEC_DESCRIPTION_EXTENDED = '--description'
TEST_EXEC_DESCRIPTION_HELP = 'Set a description if test execution is created.\n' \
                             'Example: -d \"This is a description for a test execution\"'

TEST_EXEC_VERSION = '-x'
TEST_EXEC_VERSION_EXTENDED = '--test-exec-version'
TEST_EXEC_VERSION_HELP = 'Set a version in the test execution issue if a test execution is created.'

TEST_EXEC_USER = '-u'
TEST_EXEC_USER_EXTENDED = '--user'
TEST_EXEC_USER_HELP = 'Set the username responsible for the creation of the test execution ' \
                      'if test execution is created.'

TEST_EXEC_REVISION = '-rv'
TEST_EXEC_REVISION_EXTENDED = '--test-exec-revision'
TEST_EXEC_REVISION_HELP = 'Set a revision in the test execution issue if test execution is created.'

TEST_EXEC_STARTDATE = '-sd'
TEST_EXEC_STARTDATE_EXTENDED = '--start-date'
TEST_EXEC_STARTDATE_HELP = 'Set a start date for the test execution, if created. ' \
                           'This date has to follow a specific format.\n' \
                           'Example: -sd \"2014-08-30T11:47:35+01:00\"'

TEST_EXEC_FINISHDATE = '-fd'
TEST_EXEC_FINISHDATE_EXTENDED = '--finish-date'
TEST_EXEC_FINISHDATE_HELP = 'Set a finish date for the test execution, if created. ' \
                            'This date has to follow a specific format.\n' \
                        'Example:-fd \"2014-08-30T11:53:00+01:00\"'

TEST_EXEC_TESTPLANKEY = '-pk'
TEST_EXEC_TESTPLANKEY_EXTENDED = '--test-plan-key'
TEST_EXEC_TESTPLANKEY_HELP = 'Set a test plan key for the test execution, if created.\n' \
                               'Example: -pk DEMO-001'

TEST_EXEC_TESTENV = '-env'
TEST_EXEC_TESTENV_EXTENDED = '--test-environments'
TEST_EXEC_TESTENV_HELP = 'Set test environments on test execution, if created. If set multiple test environments, ' \
                          'separate them with \"|\".\n' \
                          'Example: -env "iOS|Android"'

CERTIFICATE = '-c'
CERTIFICATE_EXTENDED = '--certificate'
CERTIFICATE_HELP = 'Set path to SSL certificate. If value not set, there will not be any verification of certificates. '\
                   'Exposing this application to security risks.\n'\
                   'Example: -c "/PATH/TO/CERTIFICATE"'


# Adding the version of this tool
TOOL_VERSION = '-v'
TOOL_VERSION_EXTENDED = '--version'
TOOL_VERSION_TAG = 'version'
TOOL_VERSION_ACTION = 'TOOL: %(prog)s\nVERSION: 1.0'

# Adding test summary option
TEST_PLAN_SUMMARY = '-tpsum'
TEST_PLAN_SUMMARY_EXTENDED = '--test-plan-summary'
TEST_PLAN_SUMMARY_HELP = 'Give a custom summary to the test plan'

# Create test exec Ad hoc (create without creating a test plan and associate test exec to test plan)
TEST_EXEC_ADHOC = '-adhoc'
TEST_EXEC_ADHOC_EXTENDED = '--ad-hoc'
TEST_EXEC_ADHOC_HELP = 'Create test execution only, without creating a test plan an associate test exec to it'

# Add files to the attachment field of test execution
ATTACHMENT = '-att'
ATTACHMENT_EXTENDED = '--attachment'
ATTACHMENT_HELP = 'Add file to attachment field of test execution. To add multiple files, separate them by commas. Eg. -att file1.txt,file2.csv,file3.html'



# TEST EXECUTION INFO KEYS
TEST_EXECUTION_INFO_SUMMARY_KEY = 'summary'
TEST_EXECUTION_INFO_DESCRIPTION_KEY = 'description'
TEST_EXECUTION_INFO_VERSION_KEY = 'version'
TEST_EXECUTION_INFO_USER_KEY = 'user'
TEST_EXECUTION_INFO_REVISION_KEY = 'revision'
TEST_EXECUTION_INFO_STARTDATE_KEY = 'startDate'
TEST_EXECUTION_INFO_FINISHDATE_KEY = 'finishDate'
TEST_EXECUTION_INFO_TESTPLANKEY_KEY = 'testPlanKey'
TEST_EXECUTION_INFO_TESTENVIRONMENTS_KEY = 'testEnvironments'

TEST_EXECUTION_INFO_TESTENVIRONMENTS_SEPERATOR = '|'

## Filter Keys

FILTER_TAG_KEY = 'tag'
FILTER_TEST_SUITE_KEY = 'test suite'
FILTER_TEST_CASE_KEY = 'test case'

#### XML PARSER AND CREATION OF TEST EXEC

JIRA_TEST_TAG = 'JIRA_TEST'
JIRA_TESTEXEC_TAG = 'JIRA_TESTEXEC'
NO_TESTEXEC_KEY = '-1'

# XML TAG
TEST_TAG = 'test'
SUITE_TAG = 'suite'
STATUS_TAG = 'status'
KW_TAG = 'kw'
MSG_TAG = 'msg'

# XML ATTRIB
ATTRIB_NAME = 'name'
ATTRIB_STARTTIME = 'starttime'
ATTRIB_ENDTIME = 'endtime'
ATTRIB_STATUS = 'status'
ATTRIB_TYPE = 'type'
ATTRIB_LEVEL = 'level'

# ATTRIB VALUES
NO_VALUE = 'N/A'
SETUP = 'setup'
TEARDOWN = 'teardown'

## XPATH
# XPATH TO CLEAR MEMORY
XPATH_ANCESTOR = 'ancestor-or-self::*'
# XPATH TO GET TEST TAGS TEXT
XPATH_TAG_TEXT = 'tags/tag/text()'
# XPATH TO FIND EVIDENCE MSG
XPATH_EVIDENCE_MSG = 'msg[@level="INFO"]'
# XPATH TO GET ARGUMENTS FROM LOG
XPATH_LOG_ARGS = 'arguments/arg'
#XPATH TO GET FIRST SUITE
XPATH_ANCESTOR_SUITE = 'ancestor::suite'
# TEST TAG SEPARATOR
TEST_TAG_SEPARATOR = ':'

## TEST EXECUTION SUMMARY
# FILTERS
TEST_EXECUTION_SUMMARY_FILTERS = 'Test Execution {} with filters: {}'
# NO FILTER
TEST_EXECUTION_SUMMARY = 'Test Execution {}'

## TEST/KW Status
FAIL = 'FAIL'

# LOG LEVEL
WARN = 'WARN'
ERROR = 'ERROR'

# REGEX TO GET EVIDENCE SOURCE
SRC_REGEX = 'img src="(.*?)"'

## DATE FORMAT

# ROBOT FRAMEWORK FORMAT
DATE_ROBOT_FRAMEWORK_FORMAT = '%Y%m%d %H:%M:%S.%f'
# XRAY FORMAT
DATE_XRAY_FORMAT = '%Y-%m-%dT%H:%M:%S+01:00'

## SEND REQUEST

# HEADERS
CONTENT_TYPE = "Content-Type"
CONTENT_TYPE_JSON = "application/json"
# For attachments
CONTENT_ATLASSIAN_TOKEN = "X-Atlassian-Token"
CONTENT_ATLASSIAN_TOKEN_VALUE = "no-check"


# TEST EXECUTION ISSUE
TEST_EXEC_ISSUE = 'testExecIssue'
TEST_EXECUTION_KEY = 'testExecutionKey'
KEY = 'key'

##DEBUG LOG
DEBUG_UPDATE = 'Update {} tests of test execution {}. Test keys: {}'
DEBUG_CREATE = 'Create a new test execution with name: \"{}\" and \"{}\" tests. Test keys: {}'


# TEST PLAN
# Create test plan
TEST_PLAN_ENDPOINT = '/rest/api/2/issue/'
# Add test exec to test plan
TEST_PLAN_TEST_EXECS_ENDPOINT = '/rest/raven/1.0/api/testplan/{}/testexecution'
# Add tests to test plan
TEST_PLAN_TESTS_ENDPOINT = '/rest/raven/1.0/api/testplan/{}/test'
# Default 
TEST_PLAN_SUMMARY_JIRA = 'Test Plan API'
TEST_PLAN_DESCRIPTION_JIRA = 'Test Plan created from API'
TEST_PLAN_ISSUE_NAME = 'Test Plan'


# ATTACHMENTS
# Attachment endpoint
ATTACHMENT_ENDPOINT = '/rest/api/2/issue/{}/attachments'


