from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import unittest
import json

from ansible.module_utils import basic
from ansible.module_utils._text import to_bytes
from unittest.mock import patch
from plugins.modules.syncope_user_handler import SyncopeUserHandler


class AnsibleExitJson(Exception):
    """Exception class to be raised by module.exit_json and caught by the test case"""
    pass


class AnsibleFailJson(Exception):
    """Exception class to be raised by module.fail_json and caught by the test case"""
    pass


def exit_json(*args, **kwargs):
    """function to patch over exit_json; package return data into an exception"""
    if 'changed' not in kwargs:
        kwargs['changed'] = False
    raise AnsibleExitJson(kwargs)


def fail_json(*args, **kwargs):
    """function to patch over fail_json; package return data into an exception"""
    kwargs['failed'] = True
    raise AnsibleFailJson(kwargs)


class MockResponse:
    def __init__(self, json_data, status_code):
        self.json_data = json_data
        self.status_code = status_code

    def json(self):
        return self.json_data


def mock_succeeded_post(*args, **kwargs):
    return MockResponse([], 200)


def mock_failed_post(*args, **kwargs):
    return MockResponse([], 500)


def mock_succeeded_get(*args, **kwargs):
    json_user = """{"@class": "org.apache.syncope.common.lib.to.UserTO",
        "key": "c9b2dec2-00a7-4855-97c0-d854842b4b24",
        "username": "bellini", "status": "suspended",
        "plainAttrs": [
            { "schema": "firstname", "values": ["Vincenzo"]}, {"schema": "surname", "values": ["Bellini"]}
        ],
        "resources": []
    }"""
    data = json.loads(json_user)
    return MockResponse(data, 200)


def mock_failed_get(*args, **kwargs):
    return MockResponse([], 500)


def set_module_args(args):
    """prepare arguments so that they will be picked up during module creation"""
    args = json.dumps({'ANSIBLE_MODULE_ARGS': args})
    basic._ANSIBLE_ARGS = to_bytes(args)


class TestMyModule(unittest.TestCase):

    def setUp(self):
        self.mock_module_helper = patch.multiple(basic.AnsibleModule,
                                                 exit_json=exit_json,
                                                 fail_json=fail_json)
        self.mock_module_helper.start()
        self.addCleanup(self.mock_module_helper.stop)

    def set_default_args(self):
        return dict({
            'action': 'change status',
            'adminUser': 'admin',
            'adminPwd': 'pwd',
            'serverName': 'url',
            'syncopeUser': 'id',
            'newAttributeValue': 'firstname=test;surname=test',
            'newStatus': 'SUSPEND',
            'changeStatusOnSyncope': True
        })

    @patch('plugins.modules.syncope_user_handler.requests.post', side_effect=mock_succeeded_post)
    @patch('plugins.modules.syncope_user_handler.requests.get', side_effect=mock_succeeded_get)
    def test_change_status_success(self, mock_post, mock_get):
        module_args = {}
        module_args.update(self.set_default_args())
        set_module_args(module_args)
        my_obj = SyncopeUserHandler()
        result = my_obj.change_user_status_rest_call()
        self.assertTrue(result['changed'])

    @patch('plugins.modules.syncope_user_handler.requests.post', side_effect=mock_failed_post)
    @patch('plugins.modules.syncope_user_handler.requests.get', side_effect=mock_succeeded_get)
    def test_change_status_failure(self, mock_post, mock_get):
        module_args = {}
        module_args.update(self.set_default_args())
        set_module_args(module_args)
        my_obj = SyncopeUserHandler()
        result = my_obj.change_user_status_rest_call()
        self.assertFalse(result['changed'])

    @patch('plugins.modules.syncope_user_handler.requests.get', side_effect=mock_succeeded_get)
    def test_get_user_success(self, mock_get):
        module_args = {}
        module_args.update(self.set_default_args())
        set_module_args(module_args)
        my_obj = SyncopeUserHandler()
        result = my_obj.get_user_rest_call()
        self.assertTrue(result['username'] == 'bellini')

    @patch('plugins.modules.syncope_user_handler.requests.get', side_effect=mock_failed_get)
    def test_get_user_failure(self, mock_get):
        module_args = {}
        module_args.update(self.set_default_args())
        set_module_args(module_args)
        my_obj = SyncopeUserHandler()
        result = my_obj.get_user_rest_call()
        self.assertTrue(result is None)

    @patch('plugins.modules.syncope_user_handler.requests.get', side_effect=mock_succeeded_get)
    @patch('plugins.modules.syncope_user_handler.requests.put', side_effect=mock_succeeded_post)
    def test_modify_user_success(self, mock_get, mock_put):
        module_args = {}
        module_args.update(self.set_default_args())
        set_module_args(module_args)
        my_obj = SyncopeUserHandler()
        result = my_obj.modify_user_rest_call()
        self.assertTrue(result['changed'])

    @patch('plugins.modules.syncope_user_handler.requests.get', side_effect=mock_failed_get)
    @patch('plugins.modules.syncope_user_handler.requests.put', side_effect=mock_failed_post)
    def test_modify_user_failure(self, mock_get, mock_put):
        module_args = {}
        module_args.update(self.set_default_args())
        set_module_args(module_args)
        my_obj = SyncopeUserHandler()
        result = my_obj.modify_user_rest_call()
        self.assertFalse(result['changed'])

    @patch('plugins.modules.syncope_user_handler.requests.get', side_effect=mock_succeeded_get)
    @patch('plugins.modules.syncope_user_handler.requests.put', side_effect=mock_succeeded_post)
    def test_set_must_change_password_success(self, mock_get, mock_put):
        module_args = {}
        module_args.update(self.set_default_args())
        set_module_args(module_args)
        my_obj = SyncopeUserHandler()
        result = my_obj.set_must_change_password_rest_call()
        self.assertTrue(result['changed'])

    @patch('plugins.modules.syncope_user_handler.requests.get', side_effect=mock_failed_get)
    @patch('plugins.modules.syncope_user_handler.requests.put', side_effect=mock_failed_post)
    def test_set_must_change_password_failure(self, mock_get, mock_put):
        module_args = {}
        module_args.update(self.set_default_args())
        set_module_args(module_args)
        my_obj = SyncopeUserHandler()
        result = my_obj.set_must_change_password_rest_call()
        self.assertFalse(result['changed'])
