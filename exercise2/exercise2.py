__author__ = 'Geon'
import httplib
import json
import sys
import time
import os
import logging

# Init a simple logger...
logging.basicConfig(level=logging.INFO)
console = logging.StreamHandler()
console.setLevel(logging.DEBUG)
logger = logging.getLogger()
logger.addHandler(console)

# hosts
HOST_AUTH = 'cloud.lab.fi-ware.org:4730'
HOST_CDMI = '130.206.82.9:8080'

TEST_CONTAINER_NAME = 'guilleContainer'
TEST_OBJECT_NAME = 'TestObjectPython2.txt'
TEST_TEXT = 'Hello Developers of FIWARE Developers week!!!'

MAX_FILES_IN_A_CONTAINER = 2

def authentication_request(username, password):
    '''
    Request authentication of user
    '''
    conn = httplib.HTTPConnection(HOST_AUTH)

    # retrieve initial token
    headers = {'Content-Type': 'application/json'}
    body = '{"auth": {"passwordCredentials":{"username": "'+username+'", "password": "'+password+'"}}}'
    conn.request("POST", "/v2.0/tokens", body, headers)
    response = conn.getresponse()
    data = response.read()
    datajson = json.loads(data)
    initialtoken = datajson['access']['token']['id']

    logger.info('Initial Token is: ' + initialtoken)

    # retrieve tenant
    headers = {'x-auth-token': initialtoken}
    conn.request("GET", "/v2.0/tenants", None, headers)
    response = conn.getresponse()
    data = response.read()
    datajson = json.loads(data)
    tenant = datajson['tenants'][0]['id']

    logger.info('Tenant is: ' + tenant)

    # retrieve authentication json
    headers = {'Content-Type': 'application/json'}
    body = '{"auth": {"tenantName": "'+tenant+'", "passwordCredentials":{"username": "'+username+'", "password": "'+password+'"}}}'
    conn.request("POST", "/v2.0/tokens", body, headers)
    response = conn.getresponse()
    data = response.read()

    return json.loads(data)


def cdmi_request(verb, resource, headers, body):
    '''
    Do a HTTP request defined by HTTP verb, a Url, a dict of headers and a body.
    '''
    conn = httplib.HTTPConnection(HOST_CDMI)
    conn.request(verb, "/cdmi/" + resource, body, headers)
    response = conn.getresponse()

    if response.status not in [200, 201, 202, 204]:
        logger.error(response.reason)
        logger.warn(response.read())
        sys.exit(1)

    result = response.read()

    #result = "Status: " + str(response.status) + ", Reason: " + response.reason + ", Body: " +  response.read()

    conn.close()

    return result


def create_container(token, auth, name):
    headers = {"X-Auth-Token": token,
               "Content-Type": "application/cdmi-container",
               "Accept": "application/cdmi-container",
               "X-CDMI-Specification-Version": "1.0.1"}
    body = None
    url = auth + "/" + name + "/"

    return cdmi_request('PUT', url, headers, body)


def list_container(token, auth, name):
    headers = {"X-Auth-Token": token,
               "Content-Type": "application/cdmi-container",
               "Accept": "*/*",
               "X-CDMI-Specification-Version": "1.0.1"}
    body = None
    url = auth + "/" + name + "/"

    return cdmi_request('GET', url, headers, body)


def store_text(token, auth, container_name, object_name, object_text):
    headers = {"X-Auth-Token": token,
               "Content-Type": "application/cdmi-object",
               "Accept": "application/cdmi-object",
               "X-CDMI-Specification-Version": "1.0.1"}
    body = '{"mimetype":"text/plain", "metadata":{}, "value" : "' + object_text + '"}'
    url = auth + "/" + container_name + "/" + object_name

    return cdmi_request('PUT', url, headers, body)


def retrieve_text(token, auth, container_name, object_name):
    headers = {"X-Auth-Token": token,
               "Content-Type": "application/cdmi-object",
               "Accept": "*/*",
               "X-CDMI-Specification-Version": "1.0.1"}
    body = None
    url = auth + "/" + container_name + "/" + object_name

    return cdmi_request('GET', url, headers, body)


if __name__ == '__main__':
    if len(sys.argv) < 3:
        print 'Usage: exercise2.py <username> <password>'
        sys.exit(128)

    username = sys.argv[1]
    password = sys.argv[2]

    # display basic info
    logger.info('Object storage host is: ' + HOST_CDMI)
    logger.info('Authorisation host is: ' + HOST_AUTH)

    # get authentication response
    auth_reponse = authentication_request(username, password)

    # extract token
    token = auth_reponse['access']['token']['id']
    logger.info('Security token is: ' + token)

    # extract authentication string required for addressing users resources
    for i in auth_reponse['access']['serviceCatalog']:
	if i['name'] == 'swift':
		auth_url = i['endpoints'][0]['publicURL']
 		break

    auth = auth_url[auth_url.find("AUTH_"):]
    logger.info('Authentication string is: ' + auth)

    # perform some basic Object Store operations


    response = list_container(token, auth, TEST_CONTAINER_NAME)
    logger.info('List Container Response: ' + response)
    n_files = len(json.loads(response)['children'])
    logger.info('Number of files: %d' % n_files)



    if n_files > MAX_FILES_IN_A_CONTAINER:
        TEST_CONTAINER_NAME = "NewContainer"

    response = create_container(token, auth, TEST_CONTAINER_NAME)
    logger.info('Create Container Response: ' + response)

    response = store_text(token, auth, TEST_CONTAINER_NAME, TEST_OBJECT_NAME, TEST_TEXT)
    logger.info('Store Text Response: ' + response)

    response = retrieve_text(token, auth, TEST_CONTAINER_NAME, TEST_OBJECT_NAME)
    logger.info('Retrieve Text Response: ' + response)

