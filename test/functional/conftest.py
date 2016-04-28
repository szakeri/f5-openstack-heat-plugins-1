# Copyright 2015-2016 F5 Networks Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#

from f5.bigip import BigIP as BigIPSDK
import heat_client_utils as hc_utils
import plugin_test_utils as plugin_utils

import pytest
from pytest import symbols


def create_stack(symbols, template, parameters={}):
    hc = hc_utils.HeatClientMgr(symbols)
    parameters.update(
        {'bigip_ip': symbols.bigip_ip, 'bigip_un': symbols.bigip_username, 'bigip_pw': symbols.bigip_password}
    )
   # print "bigip ip, username and password are:", %(symbols.bigip_ip, symbols.bigip_username, symbols.bigip_password)
    stack = hc.create_stack(template=template, parameters=parameters)
    return hc, stack


@pytest.fixture
def HeatStack(request, symbols):
    '''Heat stack fixture for creating/deleting a heat stack.'''
    def manage_stack(template_file, parameters={}):
        def teardown():
            hc.delete_stack()
        request.addfinalizer(teardown)

        template = plugin_utils.get_template_file(template_file)
        hc, stack = create_stack(
            symbols, template, parameters
        )
        return hc, stack
    return manage_stack


@pytest.fixture
def HeatStackNoTeardown(request, symbols):
    '''Heat stack fixture for creating/deleting a heat stack.'''
    def manage_stack(template_file):
        template = plugin_utils.get_template_file(template_file)
        hc, stack = create_stack(
            symbols, template
        )

        return hc, stack
    return manage_stack


@pytest.fixture
def HeatStackNoParams(request, symbols):
    '''Heat stack fixture which gives no params to create_stack.'''
    def manage_stack(template_file):
        template = plugin_utils.get_template_file(template_file)
        hc = hc_utils.HeatClientMgr(symbols)
        stack = hc.create_stack(template=template)

        def teardown():
            hc.delete_stack()
        request.addfinalizer(teardown)

        return hc, stack
    return manage_stack


@pytest.fixture
def BigIP(symbols):
    '''BigIP fixture.'''
    return BigIPSDK(symbols.bigip_ip, symbols.bigip_username, symbols.bigip_password)
