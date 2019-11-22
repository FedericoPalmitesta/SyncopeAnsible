#!/usr/bin/python

# Copyright (C) 2019 Tirasa (info@tirasa.net)
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)

__metaclass__ = type

ANSIBLE_METADATA = {
    'metadata_version': '1.0',
    'status': ['preview'],
    'supported_by': 'Tirasa S.r.l.'
}

DOCUMENTATION = '''

module: syncope_user_handler
short_description: Handle user on Apache Syncope
version_added: '2.4'
description:
    - Module handle user on Apache Syncope.

author: Tirasa Ansible Team (@mat-ale) (@FedericoPalmitesta) (@mdisabatino) (@ilgrosso)

options:

    action:
        required: true
        type: str
        description:
        - This is the message to send to the modules.
        choices: ['change status']

    adminUser:
        required: true
        type: str
        description:
        - Username of the Admin User to login to Syncope

    adminPwd:
        required: true
        type: str
        description:
        - Password of the Admin User to login to Syncope

    serverName:
        required: true
        type: str
        description:
        - Domain url of the Syncope instance

    syncopeUser:
        required: true
        type: str
        description:
        - Key of the user on Syncope whose status will be updated

    changeStatusOnSyncope:
        required: true
        type: str
        description:
        - In case the status update must be executed on Syncope too ('true') or only to the resources, if any ('false')

    newStatus:
        required: true
        type: str
        description:
        - Value of the new status
        choices: ['SUSPEND', 'REACTIVATE', 'ACTIVATE']
'''

EXAMPLES = """
- name: Suspend user
  syncope_user_handler:
    "action": "change status"
    "adminUser": "admin"
    "adminPwd": "password"
    "serverName": "https://syncope-vm.apache.org"
    "syncopeUser": "c9b2dec2-00a7-4855-97c0-d854842b4b24"
    "changeStatusOnSyncope": "true"
    "newStatus": "SUSPEND"

- name: Reactivate user
  syncope_user_handler:
    "action": "change status"
    "adminUser": "admin"
    "adminPwd": "password"
    "serverName": "https://syncope-vm.apache.org"
    "syncopeUser": "c9b2dec2-00a7-4855-97c0-d854842b4b24"
    "changeStatusOnSyncope": "true"
    "newStatus": "REACTIVATE"

- name: Activate user
  syncope_user_handler:
    "action": "change status"
    "adminUser": "admin"
    "adminPwd": "password"
    "serverName": "https://syncope-vm.apache.org"
    "syncopeUser": "c9b2dec2-00a7-4855-97c0-d854842b4b24"
    "changeStatusOnSyncope": "true"
    "newStatus": "ACTIVATE"
"""

RETURN = '''
changed:
    description: The output response from the Apache Syncope endpoint
    type: str
    returned: always
message:
    description: To determine whether this modules made any modifications to the target or not
    type: bool
    returned: always
'''

from ansible.module_utils.basic import json, AnsibleModule

try:
    import requests

    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False


class SyncopeUserHandler(object):

    def __init__(self):
        self.argument_spec = dict(
            action=dict(type='str', choices=['change status'], required=True),
            adminUser=dict(type='str', required=True),
            adminPwd=dict(type='str', required=True),
            serverName=dict(type='str', required=True),
            syncopeUser=dict(type='str', required=True),
            newStatus=dict(type='str', choices=['SUSPEND', 'ACTIVATE', 'REACTIVATE'], required=False),
            changeStatusOnSyncope=dict(type='str', required=False)
        )

        self.module = AnsibleModule(
            argument_spec=self.argument_spec,
            supports_check_mode=True
        )

        self.result = dict(
            ok=False,
            changed=False,
            message=''
        )

    def get_user_rest_call(self):
        url = self.module.params['serverName'] + "/syncope/rest/users/" + self.module.params['syncopeUser']

        headers = {'Accept': 'application/json',
                   'Prefer': 'return-content',
                   'X-Syncope-Domain': 'Master'
                   }

        user = self.module.params['adminUser']
        password = self.module.params['adminPwd']

        try:
            resp = requests.get(url, headers=headers, auth=(user, password))
            resp_json = resp.json()

            if resp_json is None or resp is None or resp.status_code != 200:
                return None
            else:
                return resp_json
        except Exception as e:
            res = json.load(e)
            self.module.fail_json(msg=res)

    def change_user_status_rest_call(self):

        user = self.get_user_rest_call()
        if user is None:
            self.result['message'] = "Error while changing status"
            return self.result
        elif self.module.check_mode and user['entity']['status'] != self.module.params['newStatus']:
            self.result['message'] = "The operation con be executed successfully"
            self.result['ok'] = True
            return self.result

        url = self.module.params['serverName'] + "/syncope/rest/users/" + self.module.params['syncopeUser'] + "/status"

        headers = {'Accept': 'application/json',
                   'Content-Type': 'application/json',
                   'Prefer': 'return-content',
                   'X-Syncope-Domain': 'Master'
                   }
        payload = {
            "operation": "ADD_REPLACE",
            "value": "org.apache.syncope.common.lib.types.StatusPatchType",
            "onSyncope": self.module.params['changeStatusOnSyncope'],
            "key": self.module.params['syncopeUser'],
            "type": self.module.params['newStatus'],
            "resources": user['resources']
        }

        admin = self.module.params['adminUser']
        password = self.module.params['adminPwd']

        try:
            resp = requests.post(url, headers=headers, auth=(admin, password), data=json.dumps(payload))
            resp_json = resp.json()

            if resp_json is None or resp is None or resp.status_code != 200:
                self.result['message'] = "Error while changing status"
                return self.result
            else:
                self.result['message'] = resp_json
                self.result['ok'] = True
                self.result['changed'] = True

        except Exception as e:
            res = json.load(e)
            self.module.fail_json(msg=res)

        return self.result

    def apply(self):
        if not HAS_REQUESTS:
            self.module.fail_json(msg='Please install requests module')

        if self.module.params['action'] == 'change status':
            result = self.change_user_status_rest_call()
            if result['ok']:
                self.module.exit_json(**result)
            else:
                self.module.fail_json(msg=result['message'])
        else:
            self.module.fail_json(msg='The provided action is not supported')


def main():
    change_status = SyncopeUserHandler()
    change_status.apply()


if __name__ == '__main__':
    main()
