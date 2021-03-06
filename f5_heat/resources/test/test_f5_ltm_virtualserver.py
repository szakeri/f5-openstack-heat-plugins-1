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

from f5_heat.resources import f5_ltm_virtualserver
from heat.common import exception
from heat.common import template_format
from heat.engine.hot.template import HOTemplate20150430
from heat.engine import rsrc_defn
from heat.engine import template

import mock
import pytest


vs_defn = '''
heat_template_version: 2015-04-30
description: Testing F5 LTM Virtual Server plugin
resources:
  bigip_rsrc:
    type: F5::BigIP::Device
    properties:
      ip: 10.0.0.1
      username: admin
      password: admin
  partition:
    type: F5::Sys::Partition
    properties:
      name: Common
      bigip_server: bigip_rsrc
  vs:
    type: F5::LTM::VirtualServer
    properties:
      name: testing_vs
      bigip_server: bigip_rsrc
      partition: partition
      ip: 129.0.0.1
      port: 80
      default_pool: test_pool
      vlans: [ test_vlan ]
'''

bad_vs_defn = '''
heat_template_version: 2015-04-30
description: Testing F5 LTM Virtual Server plugin
resources:
  bigip_rsrc:
    type: F5::BigIP::Device
    properties:
      ip: 10.0.0.1
      username: admin
  partition:
    type: F5::Sys::Partition
    properties:
      name: Common
      bigip_server: bigip_rsrc
  vs:
    type: F5::LTM::VirtualServer
    properties:
      name: testing_vs
      bad_prop: bad_prop_name
      partition: partition
      bigip_server: bigip_rsrc
      ip: 129.0.0.1
      port: 80
      extra_port: bad_prop
'''

test_uuid = '5abe95ca-0bc9-4158-b51b-366156ea9448'


versions = ('2015-04-30', '2015-04-30')


@mock.patch.object(template, 'get_version', return_value=versions)
@mock.patch.object(
    template,
    'get_template_class',
    return_value=HOTemplate20150430
)
def mock_template(templ_vers, templ_class, test_templ=vs_defn):
    '''Mock a Heat template for the Kilo version.'''
    templ_dict = template_format.parse(test_templ)
    return templ_dict


def create_resource_definition(templ_dict):
    '''Create resource definition.'''
    rsrc_def = rsrc_defn.ResourceDefinition(
        'test_stack',
        templ_dict['resources']['vs']['type'],
        properties=templ_dict['resources']['vs']['properties']
    )
    return rsrc_def


@pytest.fixture
def F5LTMVirtualServer():
    '''Instantiate the F5SysiAppService resource.'''
    template_dict = mock_template()
    rsrc_def = create_resource_definition(template_dict)
    mock_stack = mock.MagicMock()
    mock_stack.resource_by_refid().get_partition_name.return_value = 'Common'
    f5_vs_obj = f5_ltm_virtualserver.F5LTMVirtualServer(
        'testing_vs', rsrc_def, mock_stack
    )
    f5_vs_obj.uuid = test_uuid
    return f5_vs_obj


@pytest.fixture
def F5LTMVirtualServerExists(F5LTMVirtualServer):
    F5LTMVirtualServer.get_bigip()
    mock_exists = mock.MagicMock(return_value=True)
    F5LTMVirtualServer.bigip.ltm.virtuals.virtual.exists = mock_exists
    return F5LTMVirtualServer


@pytest.fixture
def F5LTMVirtualServerNoExists(F5LTMVirtualServer):
    F5LTMVirtualServer.get_bigip()
    mock_exists = mock.MagicMock(return_value=False)
    F5LTMVirtualServer.bigip.ltm.virtuals.virtual.exists = mock_exists
    return F5LTMVirtualServer


@pytest.fixture
def CreateVirtualServerSideEffect(F5LTMVirtualServer):
    F5LTMVirtualServer.get_bigip()
    F5LTMVirtualServer.bigip.ltm.virtuals.virtual.create.side_effect = \
        exception.ResourceFailure(mock.MagicMock(), None, action='CREATE')
    return F5LTMVirtualServer


@pytest.fixture
def DeleteVirtualServerSideEffect(F5LTMVirtualServer):
    F5LTMVirtualServer.get_bigip()
    F5LTMVirtualServer.bigip.ltm.virtuals.virtual.load.side_effect = \
        exception.ResourceFailure(mock.MagicMock(), None, action='DELETE')
    return F5LTMVirtualServer


def test_handle_create(F5LTMVirtualServer):
    create_result = F5LTMVirtualServer.handle_create()
    assert create_result is None
    assert F5LTMVirtualServer.bigip.ltm.virtuals.virtual.create.call_args == \
        mock.call(
            name=u'testing_vs',
            partition='Common',
            vlans=[u'test_vlan'],
            pool=u'test_pool',
            sourceAddressTranslation={'type': 'automap'},
            destination='/Common/129.0.0.1:80',
            vlansEnabled=True
        )


def test_handle_create_error(CreateVirtualServerSideEffect):
    '''Currently, test exists to satisfy 100% code coverage.'''
    with pytest.raises(exception.ResourceFailure):
        CreateVirtualServerSideEffect.handle_create()


def test_handle_delete(F5LTMVirtualServerExists):
    assert F5LTMVirtualServerExists.handle_delete() is True
    assert F5LTMVirtualServerExists.bigip.ltm.virtuals.virtual.load.call_args == \
        mock.call(
            name=u'testing_vs',
            partition='Common'
        )


def test_handle_delete_no_exists(F5LTMVirtualServerNoExists):
    assert F5LTMVirtualServerNoExists.handle_delete() is True


def test_handle_delete_error(DeleteVirtualServerSideEffect):
    '''Currently, test exists to satisfy 100% code coverage.'''
    with pytest.raises(exception.ResourceFailure):
        DeleteVirtualServerSideEffect.handle_delete()


def test_resource_mapping():
    rsrc_map = f5_ltm_virtualserver.resource_mapping()
    assert rsrc_map == {
        'F5::LTM::VirtualServer': f5_ltm_virtualserver.F5LTMVirtualServer
    }


def test_bad_property():
    template_dict = mock_template(test_templ=bad_vs_defn)
    rsrc_def = create_resource_definition(template_dict)
    f5_ltm_vs_obj = f5_ltm_virtualserver.F5LTMVirtualServer(
        'test',
        rsrc_def,
        mock.MagicMock()
    )
    with pytest.raises(exception.StackValidationFailed):
        f5_ltm_vs_obj.validate()
