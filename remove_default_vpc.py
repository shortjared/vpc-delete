#!/usr/bin/env python
""" deletes default VPC and all objects"""

import argparse
import pprint
import boto3
import botocore

VERBOSE = 1
DEFAULT_REGION = 'us-east-1'
PP = pprint.PrettyPrinter(indent=4)


def parse_args():
    """ parse the arguments from the command line"""
    parser = argparse.ArgumentParser()
    parser.add_argument('-p', '--profile', default='default')
    parser.add_argument('-r', '--region')
    parser.add_argument('-d', '--dry-run', action='store_true')
    return parser.parse_args()

def get_regions(session):
    """returns an array of region names for all regions supporting ec2 services"""
    ec2 = session.client('ec2')
    regions = ec2.describe_regions()
    #PP.pprint(regions)
    #return map((lambda x: x['RegionName']), regions['Regions'])
    return [x['RegionName'] for x in regions['Regions']]


def get_default_vpc(ec2_client):
    """returns the  default vpc"""
    response = ec2_client.describe_vpcs(
        DryRun=False,
        Filters=[
            {
                'Name': 'is-default',
                'Values': [
                    'true',
                ]
            },
        ]
    )
    #PP.pprint(response)
    if len(response['Vpcs']) > 1:
        raise "Unexpected Condition - more than one default VPC found!"
    elif len(response['Vpcs']) == 0:
        return None

    return response['Vpcs'][0]


def get_internet_gateways(ec2_client, vpc_id):
    """ returns an array of internet gateways associated with the specified vpc_id"""

    response = ec2_client.describe_internet_gateways(
        DryRun=False,
        Filters=[
            {
                'Name': 'attachment.vpc-id',
                'Values': [
                    vpc_id,
                ]
            },
        ]
    )
    #PP.pprint(response)
    if len(response['InternetGateways']) == 0:
        return None

    #return [x['InternetGatewayId'] for x in response['InternetGateways']]
    return response['InternetGateways']

def get_subnets(ec2_client, vpc_id):
    """ returns an array of subnets associated with the specified vpc_id"""

    response = ec2_client.describe_subnets(
        DryRun=False,
        Filters=[
            {
                'Name': 'vpc-id',
                'Values': [
                    vpc_id,
                ]
            },
        ]
    )
    #PP.pprint(response)
    if len(response['Subnets']) == 0:
        return None

    #return [x['SubnetId'] for x in response['Subnets']]
    return response['Subnets']

def get_route_tables(ec2_client, vpc_id):
    """ returns an array of Route Tables  associated with the specified vpc_id"""

    response = ec2_client.describe_route_tables(
        DryRun=False,
        Filters=[
            {
                'Name': 'vpc-id',
                'Values': [
                    vpc_id,
                ]
            },
        ]
    )
    #PP.pprint(response)
    if len(response['RouteTables']) == 0:
        return None

    return response['RouteTables']

def get_nacls(ec2_client, vpc_id):
    """ returns an array of network acls associated with the specified vpc_id"""

    response = ec2_client.describe_network_acls(
        DryRun=False,
        Filters=[
            {
                'Name': 'vpc-id',
                'Values': [
                    vpc_id,
                ]
            },
        ]
    )
    #PP.pprint(response)
    if len(response['NetworkAcls']) == 0:
        return None

    return response['NetworkAcls']

def get_security_groups(ec2_client, vpc_id):
    """ returns an array of security groups associated with the specified vpc_id"""

    response = ec2_client.describe_security_groups(
        DryRun=False,
        Filters=[
            {
                'Name': 'vpc-id',
                'Values': [
                    vpc_id,
                ]
            },
        ]
    )
    #PP.pprint(response)
    if len(response['SecurityGroups']) == 0:
        return None

    return response['SecurityGroups']


def get_name_tag(obj):
    """ returns the Name tag  for an ec2 object"""
    if 'Tags' in obj:
        names = [x['Value'] for x in obj['Tags'] if x['Key'] == 'Name']
        if len(names) > 0:
            return names[0]

    return ""

def print_vpc(vpc):
    """ print the vpc info """
    print "VPC: " + vpc['VpcId'] + \
          " (" + get_name_tag(vpc) + " - " + \
          vpc['CidrBlock'] + ")"

def print_igws(igws):
    """ print the internet gateway info """
    for igw in igws:
        print "Internet Gateway: " + igw['InternetGatewayId'] + " (" + get_name_tag(igw) + ")"

def print_subnets(subnets):
    """ print the subnet info """
    for subnet in subnets:
        #PP.pprint(subnet)
        print "Subnet: " + subnet['SubnetId'] + " (" + get_name_tag(subnet) + " - " + \
              "Cidr: " + subnet['CidrBlock'] + ", " + \
              "VpcId: " + subnet['VpcId'] +  ")"

def print_route_tables(route_tables):
    """ print the route table info """
    for route_table in route_tables:
        #PP.pprint(route_table)
        print "Route Table: " + route_table['RouteTableId'] + " (" + \
              get_name_tag(route_table) + " - " + \
              "VpcId: " + route_table['VpcId'] +  ")"

def print_nacls(nacls):
    """ print the nacl info """
    for nacl in nacls:
        #PP.pprint(nacl)
        print "Network ACL: " + nacl['NetworkAclId'] + " (" + \
              get_name_tag(nacl) + " - " + \
              "VpcId: " + nacl['VpcId'] +  ")"

def print_security_groups(security_groups):
    """ print the security group info """
    for security_group in security_groups:
        #PP.pprint(security_group)
        print "Subnet: " + security_group['GroupId'] + " (" + \
              get_name_tag(security_group) + " - " + \
              "GroupName: " + security_group['GroupName'] + ", " + \
              "Description: " + security_group['Description'] + ", " + \
              "VpcId: " + security_group['VpcId'] +  ")"











def delete_vpc(ec2_client, vpc_id, dry_run=False):
    """deletes the specified vpc"""
    response = ec2_client.delete_vpc(
        DryRun=dry_run,
        VpcId=vpc_id
    )
    #PP.pprint(response)
    return response


def delete_internet_gateway(ec2_client, igw, dry_run=False):
    """ deletes the specified internet gateway """


    response = ec2_client.detach_internet_gateway(
        DryRun=dry_run,
        InternetGatewayId=igw['InternetGatewayId'],
        VpcId=igw['VpcId']
    )

    response = ec2_client.delete_internet_gateway(
        DryRun=dry_run,
        InternetGatewayId=igw['InternetGatewayId']
    )
    return response


def delete_subnet(ec2_client, subnet, dry_run=False):
    """ deletes specified subnet """
    response = ec2_client.delete_subnet(
        DryRun=dry_run,
        SubnetId=subnet['SubnetId']
    )
    #PP.pprint(response)
    return response


def delete_route_table(ec2_client, route_table, dry_run=False):
    """ deletes Route Table """
    response = ec2_client.delete_route_table(
        DryRun=dry_run,
        RouteTableId=route_table['RouteTableId']
    )
    #PP.pprint(response)
    return response

def delete_nacl(ec2_client, nacl, dry_run=False):
    """ deletes network acl """

    response = ec2_client.delete_network_acl(
        DryRun=dry_run,
        NetworkAclId=nacl['NetworkAclId']
    )
    return response

def delete_security_groups(ec2_client, security_group, dry_run=False):
    """ deletes the specified security group """
    response = ec2_client.delete_security_group(
        DryRun=dry_run,
        GroupName=security_group['GroupName'],
        GroupId=security_group['GroupId']
    )

    return response





def main():
    """
    Do the work - order of operation

    1.) Delete the internet-gateway
    2.) Delete subnets
    3.) Delete route-tables
    4.) Delete network access-lists
    5.) Delete security-groups
    6.) Delete the VPC
    """

    args = parse_args()
    session = boto3.Session(profile_name=args.profile, region_name=DEFAULT_REGION)
    if args.region is None:
        regions = get_regions(session)
    else:
        regions = [args.region]
    profile = args.profile
    dry_run = args.dry_run

    print "****************************************************************************" + \
          "****************************************************************************"
    print
    print "*** DELETING THE DEFAULT VPC IS AN IRREVERSIBLE ACTION!!!! " + \
          "IF YOU NEED TO CREATE A NEW DEFAULT VPC, YOU MUST CONTACT AMAZON SUPPORT ***"
    print
    print "****************************************************************************" + \
          "****************************************************************************"
    print

    for region in regions:
        print "--------- %s ---------" % region
        session = boto3.Session(profile_name=profile, region_name=region)
        try:
            ec2_client = session.client('ec2')
            default_vpc = get_default_vpc(ec2_client)
            #PP.pprint(default_vpc)
            if default_vpc is None:
                print "No default VPC was found"
            else:
                print "The following resources wil be deleted:"
                default_vpc_id = default_vpc['VpcId']
                print_vpc(default_vpc)

                igw_list = get_internet_gateways(ec2_client, default_vpc_id)
                print_igws(igw_list)

                subnet_list = get_subnets(ec2_client, default_vpc_id)
                print_subnets(subnet_list)

                route_table_list = get_route_tables(ec2_client, default_vpc_id)
                print_route_tables(route_table_list)

                nacl_list = get_nacls(ec2_client, default_vpc_id)
                print_nacls(nacl_list)

                security_group_list = get_security_groups(ec2_client, default_vpc_id)
                print_security_groups(security_group_list)
                #print("Security Groups: " + str(security_group_list))

                do_delete = raw_input("Continuing will permanently destroy all the objects listed above! are you sure you want to continue? [yes/no]: ")
                if do_delete.strip().lower() == "yes":
                    print "Deleting..."
                else:
                    print "Stopping - You entered '" + do_delete +"' instead of 'yes'"

        except botocore.exceptions.ClientError as err:
            print err.message
            exit(1)



if __name__ == "__main__":

    main()
