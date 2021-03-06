#!/usr/bin/python
'''
    azure dynamic inventory for ansible.
'''
import os
import sys
import argparse
import json
import configparser
from pprint import PrettyPrinter
from azure.common.credentials import ServicePrincipalCredentials
from azure.mgmt.compute import ComputeManagementClient
from azure.mgmt.network import NetworkManagementClient


class Azure_Machine:
    def __init__(self, name, location, tags, public_ip, private_ip):
        self.name = unicode(name).encode('ascii', 'ignore')
        self.location = unicode(location).encode('ascii', 'ignore')
        self.tags = unicode(tags).encode('ascii', 'ignore')
        self.public_ip = unicode(public_ip).encode('ascii', 'ignore')
        self.private_ip = unicode(private_ip).encode('ascii', 'ignore')

class Azure_Inventory():
    ''' Dynamic inventory class used to query Azure for virtual machines. '''
    def __init__(self):

        args = self.parse_args()        

        client_id = os.environ['client_id']
        secret = os.environ['secret']
        tenant = os.environ['tenant']
        subscription = os.environ['subscription']

        boundry = 1
        


        credentials = ServicePrincipalCredentials(client_id=client_id,
                                                  secret=secret,
                                                  tenant=tenant)

        self.computeManager = ComputeManagementClient(credentials=credentials,
                                                      subscription_id=subscription)

        self.networkManager = NetworkManagementClient(credentials=credentials,
                                                      subscription_id=subscription)

        inventory = list()

        self.get_machines(inventory)

        if args.prettyPrint:
            self.prettyPrint(inventory)

        if args.list:
            self.output_inventory(inventory, boundry)


    def get_machines(self, inventory_list):

        machines = self.computeManager.virtual_machines.list_all()

        interfaces = self.networkManager.network_interfaces.list_all()
        ip_config = self.networkManager.public_ip_addresses.list_all()


        for m in machines:

            m_name = str()
            m_location = str()
            m_tags = list()
            m_public_ip = str()
            m_private_ip = str()

            m_name = m.name
            m_location = m.location
            m_tags = m.tags


            ### ID In this object, has the ID of the network interface.
            ### Use this to identify ip addresses.
            network = m.network_profile.network_interfaces

            # this is a horrible itteration. want to remove.
            for n in network:

                for inter in interfaces:
                    if inter.id == n.id:
                        for x in inter.ip_configurations:
                            m_private_ip = x.private_ip_address

                            for pip in ip_config:
                                if pip.id == x.public_ip_address.id:
                                    m_public_ip = pip.ip_address

            azure_host = Azure_Machine(name=m_name, location=m_location,
                                       tags=m_tags, public_ip=m_public_ip,
                                       private_ip=m_private_ip)

            inventory_list.append(azure_host)

            interfaces.reset()
            ip_config.reset()



    def parse_args(self):
        parser = argparse.ArgumentParser(description="Azure dynamic inventory script.")
        parser.add_argument('--list', action='store_true')
        parser.add_argument('--host', type=str, required=False)
        parser.add_argument('--toggleBoundry', action='store_true',)
        parser.add_argument('--prettyPrint', action='store_true')
        return parser.parse_args()



    def getConfiguration(self, ini_file):
        config = configparser.RawConfigParser(allow_no_value=False)
        config.read_file(ini_file)
        return config



    def prettyPrint(self, inventory):

        pp = PrettyPrinter(indent=2)

        for i in inventory:
            pp.pprint(vars(i))


    def output_inventory(self, inventory, boundry_toggle):

        inv = {"hosts": [], "_meta": {"hostvars":{}}}

        for i in inventory:

            if boundry_toggle:
                inv["hosts"].append(i.public_ip)


            else:
                inv["hosts"].append(i.private_ip)


        print(json.dumps(inv))

Azure_Inventory()
