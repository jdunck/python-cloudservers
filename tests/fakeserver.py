"""
A fake server that "responds" to API methods with pre-canned responses.

All of these responses come from the spec, so if for some reason the spec's
wrong the tests might fail. I've indicated in comments the places where actual
behavior differs from the spec.
"""

from __future__ import absolute_import

import httplib2
import nose.tools as nt
from cloudservers import CloudServers
from cloudservers.client import CloudServersClient
from .utils import fail, assert_in, assert_not_in, assert_has_keys

class FakeServer(CloudServers):
    def __init__(self):
        super(FakeServer, self).__init__('username', 'apikey')
        self.client = FakeClient()

    def assert_called(self, method, url):
        """
        Assert than an API method was just called.
        """
        nt.assert_equal(self.client.callstack[-1], (method, url),
                        'Expected %s %s; got %s %s' % (self.client.callstack[-1] + (method, url)))
        self.client.callstack = []

class FakeClient(CloudServersClient):
    def __init__(self):
        self.username = 'username'
        self.apikey = 'apikey'
        self.callstack = []
    
    def _cs_request(self, url, method, **kwargs):
        # Check that certain things are called correctly
        if method in ['GET', 'DELETE']:
            assert_not_in('body', kwargs)
        elif method in ['PUT', 'POST']:
            assert_in('body', kwargs)
        
        # Call the method
        munged_url = url.strip('/').replace('/', '_').replace('.', '_')
        callback = "%s_%s" % (method.lower(), munged_url)
        if not hasattr(self, callback):
            fail('Called unknown API method: %s %s' % (method, url))
        
        # Note the call
        self.callstack.append((method, url))
        
        status, body = getattr(self, callback)(**kwargs)        
        return httplib2.Response({"status": status}), body

    #
    # Limits
    # 

    def get_limits(self, **kw):
        return (200, {"limits" : { 
            "rate" : [
                {
                    "verb" : "POST",
                    "URI" : "*",
                    "regex" : ".*",
                    "value" : 10,
                    "remaining" : 2,
                    "unit" : "MINUTE",
                    "resetTime" : 1244425439
                }, 
                {
                    "verb" : "POST",
                    "URI" : "*/servers",
                    "regex" : "^/servers",
                    "value" : 50,
                    "remaining" : 49,
                    "unit" : "DAY", "resetTime" : 1244511839
                },
                {
                    "verb" : "PUT",
                    "URI" : "*",
                    "regex" : ".*",
                    "value" : 10,
                    "remaining" : 2,
                    "unit" : "MINUTE",
                    "resetTime" : 1244425439
                },
                {
                    "verb" : "GET",
                    "URI" : "*changes-since*",
                    "regex" : "changes-since",
                    "value" : 3,
                    "remaining" : 3,
                    "unit" : "MINUTE",
                    "resetTime" : 1244425439
                },
                {
                    "verb" : "DELETE",
                    "URI" : "*",
                    "regex" : ".*",
                    "value" : 100,
                    "remaining" : 100,
                    "unit" : "MINUTE",
                    "resetTime" : 1244425439
                }
            ], 
            "absolute" : {
                "maxTotalRAMSize" : 51200,
                "maxIPGroups" : 50,
                "maxIPGroupMembers" : 25
            }
        }})
        
    #
    # Servers
    #
        
    def get_servers(self, **kw):
        return (200, {"servers": [
            {'id': 1234, 'name': 'sample-server'},
            {'id': 5678, 'name': 'sample-server2'}
        ]})
        
    def get_servers_detail(self, **kw):
        return (200, {"servers" : [
            {
                "id" : 1234,
                "name" : "sample-server",
                "imageId" : 2,
                "flavorId" : 1,
                "hostId" : "e4d909c290d0fb1ca068ffaddf22cbd0",
                "status" : "BUILD",
                "progress" : 60,
                "addresses" : {
                    "public" : ["67.23.10.132", "67.23.10.131"],
                    "private" : ["10.176.42.16"]
                },
                "metadata" : {
                    "Server Label" : "Web Head 1",
                    "Image Version" : "2.1"
                }
            },
            {
                "id" : 5678,
                "name" : "sample-server2",
                "imageId" : 2,
                "flavorId" : 1,
                "hostId" : "9e107d9d372bb6826bd81d3542a419d6",
                "status" : "ACTIVE",
                "addresses" : {
                    "public" : ["67.23.10.133"],
                    "private" : ["10.176.42.17"]
                },
                "metadata" : {
                    "Server Label" : "DB 1"
                }
            }
        ]})
        
    def post_servers(self, body, **kw):
        nt.assert_equal(body.keys(), ['server'])
        assert_has_keys(body['server'], 
                        required = ['name', 'imageId', 'flavorId'],
                        optional = ['sharedIpGroupId', 'metadata', 'personality'])
        if 'personality' in body['server']:
            for pfile in body['server']['personality']:
                assert_has_keys(pfile, required=['path', 'contents'])
        return (202, self.get_servers_1234()[1])
        
    def get_servers_1234(self, **kw):
        r = {'server': self.get_servers_detail()[1]['servers'][0]}
        return (200, r)

    def put_servers_1234(self, body, **kw):
        nt.assert_equal(body.keys(), ['server'])
        assert_has_keys(body['server'], optional=['name', 'adminPass'])
        return (204, None)
            
    def delete_servers_1234(self, **kw):
        return (202, None)
    
    #
    # Server Addresses
    #
    
    def get_servers_1234_ips(self, **kw):
        return (200, {'addresses': self.get_servers_1234()[1]['server']['addresses']})
            
    def get_servers_1234_ips_public(self, **kw):
        return (200, {'public': self.get_servers_1234_ips()[1]['addresses']['public']})
        
    def get_servers_1234_ips_private(self, **kw):
        return (200, {'private': self.get_servers_1234_ips()[1]['addresses']['private']})
    
    def put_servers_1234_ips_public_1_2_3_4(self, body, **kw):
        nt.assert_equal(body.keys(), ['shareIp'])
        assert_has_keys(body['shareIp'], required=['sharedIpGroupId', 'configureServer'])
        return (202, None)
    
    def delete_servers_1234_ips_public_1_2_3_4(self, **kw):
        return (202, None)
        
    #
    # Server actions
    #
    
    def post_servers_1234_action(self, body, **kw):
        nt.assert_equal(len(body.keys()), 1)
        action = body.keys()[0]
        if action == 'reboot':
            nt.assert_equal(body[action].keys(), ['type'])
            assert_in(body[action]['type'], ['HARD', 'SOFT'])
        elif action == 'rebuild':
            nt.assert_equal(body[action].keys(), ['imageId'])
        elif action == 'resize':
            nt.assert_equal(body[action].keys(), ['flavorId'])
        elif action == 'confirmResize':
            nt.assert_equal(body[action], None)
            # This one method returns a different response code
            return (204, None)
        elif action == 'revertResize':
            nt.assert_equal(body[action], None)
        else:
            nt.assert_(False, "Unexpected server action: %s" % action)
        return (202, None)
        
    #
    # Flavors
    #
    
    def get_flavors(self, **kw):
        return (200, {'flavors': [
            {'id': 1, 'name': '256 MB Server'},
            {'id': 2, 'name': '512 MB Server'}
        ]})
        
    def get_flavors_detail(self, **kw):
        return (200, {'flavors': [
            {'id': 1, 'name': '256 MB Server', 'ram': 256, 'disk': 10},
            {'id': 2, 'name': '512 MB Server', 'ram': 512, 'disk': 20}
        ]})
        
    def get_flavors_1(self, **kw):
        return (200, {'flavor': self.get_flavors_detail()[1]['flavors'][0]})
    
    #
    # Images
    #
    def get_images(self, **kw):
        return (200, {'images': [
            {'id': 1, 'name': 'CentOS 5.2'},
            {'id': 2, 'name': 'My Server Backup'}
        ]})
        
    def get_images_detail(self, **kw):
        return (200, {'images': [
            {
                'id': 1, 
                'name': 'CentOS 5.2',
                "updated" : "2010-10-10T12:00:00Z",
                "created" : "2010-08-10T12:00:00Z",
                "status" : "ACTIVE"
            },
            {
                "id" : 743,
                "name" : "My Server Backup",
                "serverId" : 12,
                "updated" : "2010-10-10T12:00:00Z",
                "created" : "2010-08-10T12:00:00Z",
                "status" : "SAVING",
                "progress" : 80
            }
        ]})
        
    def get_images_1(self, **kw):
        return (200, {'image': self.get_images_detail()[1]['images'][0]})
        
    def post_images(self, body, **kw):
        nt.assert_equal(body.keys(), ['image'])
        assert_has_keys(body['image'], required=['serverId', 'name'])
        return (202, self.get_images_1()[1])
        
    def delete_images_1(self, **kw):
        return (204, None)
    
    #
    # Backup schedules
    #
    def get_servers_1234_backup_schedule(self, **kw):
        return (200, {"backupSchedule" : {
            "enabled" : True,
            "weekly" : "THURSDAY",
            "daily" : "H_0400_0600"
        }})
        
    def post_servers_1234_backup_schedule(self, body, **kw):
        nt.assert_equal(body.keys(), ['backupSchedule'])
        assert_has_keys(body['backupSchedule'], required=['enabled'], optional=['weekly', 'daily'])
        return (204, None)
        
    def delete_servers_1234_backup_schedule(self, **kw):
        return (204, None)
        
    #
    # Shared IP groups
    #
    def get_shared_ip_groups(self, **kw):
        return (200, {'sharedIpGroups': [
            {'id': 1, 'name': 'Shared IP Group 1'},
            {'id': 2, 'name': 'Shared IP Group 2'},
        ]})
        
    def get_shared_ip_groups_detail(self, **kw):
        return (200, {'sharedIpGroups': [
            {'id': 1, 'name': 'Shared IP Group 1', 'servers': [1234]},
            {'id': 2, 'name': 'Shared IP Group 2', 'servers': [5678]},
        ]})
        
    def get_shared_ip_groups_1(self, **kw):
        return (200, {'sharedIpGroup': self.get_shared_ip_groups_detail()[1]['sharedIpGroups'][0]})

    def post_shared_ip_groups(self, body, **kw):
        nt.assert_equal(body.keys(), ['sharedIpGroup'])
        assert_has_keys(body['sharedIpGroup'], required=['name', 'server'])
        return (201, {'sharedIpGroup': {
            'id': 10101,
            'name': body['sharedIpGroup']['name'],
            'servers': [body['sharedIpGroup']['server']]
        }})
        
    def delete_shared_ip_groups_1(self, **kw):
        return (204, None)