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
HOST_OBJECT_STORAGE = 'cloud.lab.fiware.org'

TEST_CONTAINER_NAME = 'guilleContainer'
TEST_OBJECT_NAME = 'fondo.png'

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


def swift_request(verb, resource, headers, body):
    '''
    Do a HTTP request defined by HTTP verb, a Url, a dict of headers and a body.
    '''
    conn = httplib.HTTPSConnection(HOST_OBJECT_STORAGE)
    conn.request(verb, "/Spain/object-store/v1/" + resource, body, headers)
    response = conn.getresponse()

    if response.status not in [200, 201, 202, 204]:
        logger.error(response.reason)
        logger.warn(response.read())
        sys.exit(1)

    result = response.read()

    #result = "Status: " + str(response.status) + ", Reason: " + response.reason + ", Body: " +  response.read()

    conn.close()

    return result


def store_text(token, auth, container_name, object_name, object_text):
    headers = {"X-Auth-Token": token,
               "Content-Type": "application/cdmi-object",
               "Accept": "application/cdmi-object",
               "X-CDMI-Specification-Version": "1.0.1"}
    body = '{"mimetype":"text/plain", "metadata":{}, "value" : "' + object_text + '"}'
    url = auth + "/" + container_name + "/" + object_name

    return swift_request('PUT', url, headers, body)

def upload_file(token, auth, container_name, object_name):
    headers = {"X-Auth-Token": token,
               "Content-type": "application/octet-stream"}

    f = open(object_name, 'rb')
    chunck = f.read()
    f.close()
    url = auth + "/" + container_name + "/" + object_name
    body = chunck.encode(encoding='base64')
    return swift_request('PUT', url, headers, body)


def retrieve_object(token, auth, container_name, object_name):
    headers = {"X-Auth-Token": token,
               "Accept": "*/*"}
    body = None
    url = auth + "/" + container_name + "/" + object_name
    with open(object_name, 'wb') as handle:
        response = swift_request('GET', url, headers, body)
        #for block in response.iter_content(1024):
        #   if not block:
        #      break
        myresponse = response.replace('\\"','"')
        if myresponse.__contains__('"valuetransferencoding":"base64"'):
            myresponse = myresponse[1:-1]
            myresponse = json.loads(myresponse)['value'].decode(encoding='base64')

        handle.write(myresponse)

    return response

if __name__ == '__main__':
    if len(sys.argv) < 3:
        print 'Usage: exercise1_swift.py <username> <password>'
        sys.exit(128)

    username = sys.argv[1]
    password = sys.argv[2]

    # display basic info
    logger.info('Object storage host is: ' + HOST_OBJECT_STORAGE)
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

    #response = store_text(token, auth, TEST_CONTAINER_NAME, TEST_OBJECT_NAME, TEST_TEXT)
    #logger.info('Store Text Response: ' + response)

    response = upload_file(token, auth, TEST_CONTAINER_NAME, TEST_OBJECT_NAME)
    logger.info('Upload File Response: ' + response)

    response = retrieve_object(token, auth, TEST_CONTAINER_NAME, TEST_OBJECT_NAME)
    logger.info('Retrieve Text Response: ' + response)