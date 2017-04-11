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
    parser.add_argument('-b', '--batch', action='store_true')
    return parser.parse_args()

def get_regions(session, selected_region):
    """returns an array of region names for all regions supporting ec2 services"""
    if selected_region:
        return [selected_region]

    ec2 = session.client('ec2')
    regions = ec2.describe_regions()
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
    if len(response['Vpcs']) > 1:
        raise "Unexpected Condition - more than one default VPC found!"
    elif len(response['Vpcs']) == 0:
        return None

    return response['Vpcs'][0]

def get_ec2_instances(ec2_client, vpc_id):
    """
    Gets all the ec2 instances in the specified vpc.
    Note this function will return a max of 1000 instances.  This is sufficient for our purposes.
    You must use pagination if you need to get ALL instances
    """
    matches = []
    response = ec2_client.describe_instances(
        Filters=[
            {
                'Name': 'vpc-id',
                'Values': [
                    vpc_id,
                ]
            },
        ],
        MaxResults=1000
    )
    for instances in response['Reservations']:
        matches.extend(instances['Instances'])

    return matches




def get_rds_instances(rds_client, vpc_id):
    """
    Gets all the rds instances in the specified vpc.
    """
    matching_instances = []

    paginator = rds_client.get_paginator('describe_db_instances')
    page_iterator = paginator.paginate()

    for page in page_iterator:
        #PP.pprint(page['DBInstances'])
        for db_instance in page['DBInstances']:
            if db_instance['DBSubnetGroup']['VpcId'] == vpc_id:
                matching_instances.append(db_instance)

    return matching_instances



def get_redshift_instances(redshift_client, vpc_id):
    """
    Gets all the redshift instances in the specified vpc.
    """
    matching_instances = []

    paginator = redshift_client.get_paginator('describe_clusters')
    page_iterator = paginator.paginate()

    for page in page_iterator:
        #PP.pprint(page['Clusters'])
        for cluster in page['Clusters']:
            if cluster['VpcId'] == vpc_id:
                matching_instances.append(cluster)

    return matching_instances




def get_lambda_instances(lambda_client, vpc_id):
    """
    Gets all the lambda instances in the specified vpc.
    """
    matching_instances = []

    try:
        paginator = lambda_client.get_paginator('list_functions')
        page_iterator = paginator.paginate()

        for page in page_iterator:
            #PP.pprint(page['Functions'])
            for lambda_function in page['Functions']:
                if lambda_function.has_key('VpcConfig') and \
                        lambda_function['VpcConfig'].has_key('VpcId') and \
                        lambda_function['VpcConfig']['VpcId'] == vpc_id:
                    matching_instances.append(lambda_function)

    except botocore.exceptions.EndpointConnectionError as err:
        print err.message + "(lambda is probably not supported in this region)"

    return matching_instances


def get_elb_instances(elb_client, vpc_id):
    """
    Gets all the elb instances in the specified vpc.
    """
    matching_instances = []

    paginator = elb_client.get_paginator('describe_load_balancers')
    page_iterator = paginator.paginate()

    for page in page_iterator:
        #PP.pprint(page['LoadBalancerDescriptions'])
        for load_balancer in page['LoadBalancerDescriptions']:
            if load_balancer['VPCId'] == vpc_id:
                matching_instances.append(load_balancer)

    return matching_instances


def get_elbv2_instances(elb_client, vpc_id):
    """
    Gets all the elb instances in the specified vpc.
    """
    matching_instances = []

    paginator = elb_client.get_paginator('describe_load_balancers')
    page_iterator = paginator.paginate()

    for page in page_iterator:
        #PP.pprint(page['LoadBalancers'])
        for load_balancer in page['LoadBalancers']:
            if load_balancer['VpcId'] == vpc_id:
                matching_instances.append(load_balancer)

    return matching_instances


def get_asg_instances(asg_client, vpc_id):
    """
    Gets all the autoscale groups in the specified vpc.
    """
    matching_instances = []

    paginator = asg_client.get_paginator('describe_auto_scaling_groups')
    page_iterator = paginator.paginate()

    for page in page_iterator:
        PP.pprint(page['AutoScalingGroups'])
        for load_balancer in page['AutoScalingGroups']:
            if load_balancer['VPCZoneIdentifier'] == vpc_id:
                matching_instances.append(load_balancer)

    return matching_instances





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
    if len(response['InternetGateways']) == 0:
        return []

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
    if len(response['Subnets']) == 0:
        return []

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
    #PP.pprint(response['RouteTables'])
    if len(response['RouteTables']) == 0:
        return []

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
    if len(response['NetworkAcls']) == 0:
        return []

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
    if len(response['SecurityGroups']) == 0:
        return []

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
        print "Subnet: " + subnet['SubnetId'] + " (" + get_name_tag(subnet) + " - " + \
              "Cidr: " + subnet['CidrBlock'] + ", " + \
              "VpcId: " + subnet['VpcId'] +  ")"

def print_route_tables(route_tables):
    """ print the route table info """
    for route_table in route_tables:
        print "Route Table: " + route_table['RouteTableId'] + " (" + \
              get_name_tag(route_table) + " - " + \
              "VpcId: " + route_table['VpcId'] +  ")"

def print_nacls(nacls):
    """ print the nacl info """
    for nacl in nacls:
        print "Network ACL: " + nacl['NetworkAclId'] + " (" + \
              get_name_tag(nacl) + " - " + \
              "VpcId: " + nacl['VpcId'] +  ")"

def print_security_groups(security_groups):
    """ print the security group info """
    for security_group in security_groups:
        print "Subnet: " + security_group['GroupId'] + " (" + \
              get_name_tag(security_group) + " - " + \
              "GroupName: " + security_group['GroupName'] + ", " + \
              "Description: " + security_group['Description'] + ", " + \
              "VpcId: " + security_group['VpcId'] +  ")"





def delete_vpc(ec2_client, vpc_id, dry_run=False):
    """deletes the specified vpc"""
    print "Deleting the vpc:" + vpc_id
    response = ec2_client.delete_vpc(
        DryRun=dry_run,
        VpcId=vpc_id
    )
    return response


def delete_internet_gateway(ec2_client, igw, vpc_id, dry_run=False):
    """ deletes the specified internet gateway """

    print "Detaching internet gateway: " + igw['InternetGatewayId'] + \
          " from vpc " + vpc_id
    try:
        response = ec2_client.detach_internet_gateway(
            DryRun=dry_run,
            InternetGatewayId=igw['InternetGatewayId'],
            VpcId=vpc_id
        )
    except botocore.exceptions.ClientError as err:
        print err.message

    print "Deleting internet gateway: " + igw['InternetGatewayId']
    response = ec2_client.delete_internet_gateway(
        DryRun=dry_run,
        InternetGatewayId=igw['InternetGatewayId']
    )

    return response


def delete_subnet(ec2_client, subnet, dry_run=False):
    """ deletes specified subnet """

    print "Deleting Subnet: " + subnet['SubnetId']
    response = ec2_client.delete_subnet(
        DryRun=dry_run,
        SubnetId=subnet['SubnetId']
    )
    return response


def delete_route_table(ec2_client, route_table, dry_run=False):
    """ deletes Route Table """

    print "Deleting route table: " + route_table['RouteTableId']
    try:
        response = ec2_client.delete_route_table(
            DryRun=dry_run,
            RouteTableId=route_table['RouteTableId']
        )
    except botocore.exceptions.ClientError as err:
        print "\t" + err.message
        print "\tNote that this error is expected if this is the default route table for a VPC"
        return None

    return response

def delete_nacl(ec2_client, nacl, dry_run=False):
    """ deletes network acl """

    print "Deleting Network ACL: " + nacl['NetworkAclId']
    try:
        response = ec2_client.delete_network_acl(
            DryRun=dry_run,
            NetworkAclId=nacl['NetworkAclId']
        )
    except botocore.exceptions.ClientError as err:
        print "\t" + err.message
        print "\tNote that this error is expected if this is the default Network ACL for a VPC"
        return None

    return response

def delete_security_group(ec2_client, security_group, dry_run=False):
    """ deletes the specified security group """

    print "Deleting Security Group:  " + security_group['GroupName'] + \
          "(" + security_group['GroupId'] +")"
    try:
        response = ec2_client.delete_security_group(
            DryRun=dry_run,
            GroupName=security_group['GroupName'],
            GroupId=security_group['GroupId']
        )
    except botocore.exceptions.ClientError as err:
        print "\t" + err.message
        print "\tNote that this error is expected if this is the default network security group for a VPC"
        return None

    return response


def delete_internet_gateways(ec2_client, igw_list, default_vpc_id, dry_run):
    """ deletes an array of internet gateways"""
    return [delete_internet_gateway(ec2_client, x, default_vpc_id, dry_run) for x in igw_list]

def delete_subnets(ec2_client, subnet_list, dry_run):
    """ deletes an array of subnets """
    return [delete_subnet(ec2_client, x, dry_run) for x in subnet_list]

def delete_route_tables(ec2_client, route_table_list, dry_run):
    """ deletes an array of route tables"""
    return [delete_route_table(ec2_client, x, dry_run) for x in route_table_list]

def delete_nacls(ec2_client, nacl_list, dry_run):
    """ deletes an array of network acls """
    return [delete_nacl(ec2_client, x, dry_run) for x in nacl_list]

def delete_security_groups(ec2_client, security_group_list, dry_run):
    """ deletes an array of seciurity groups """
    return [delete_security_group(ec2_client, x, dry_run) for x in security_group_list]


def print_warning():
    """ prints the warning banner """
    print "****************************************************************************" + \
          "****************************************************************************"
    print
    print "*** DELETING THE DEFAULT VPC IS AN IRREVERSIBLE ACTION!!!! " + \
          "IF YOU NEED TO CREATE A NEW DEFAULT VPC, YOU MUST CONTACT AMAZON SUPPORT ***"
    print
    print "****************************************************************************" + \
          "****************************************************************************"
    print

def prompt_to_continue():
    """ watn the user and prompt to continue"""
    do_delete = raw_input("\n\n!!!!!!! Continuing will PERMANENTLY DESTROY " + \
            "all the objects listed above!!!! Are you sure " + \
            "you want to continue? [yes/no]: ")

    if do_delete.strip().lower() == "yes":
        return True

    return False

def get_vpc_tenants(session, vpc_id):
    """ checks a vpc for dependent ec2, rds, redshift instances"""
    tenants = []

    print "...checking for ec2 instances on this vpc..."
    client = session.client('ec2')
    ec2_instances = get_ec2_instances(client, vpc_id)
    tenants.extend([{'id_field': 'InstanceId', 'id': x['InstanceId'], 'type': 'instance'} \
            for x in ec2_instances])

    print "...checking for RDS DB instances on this vpc..."
    client = session.client('rds')
    rds_instances = get_rds_instances(client, vpc_id)
    #PP.pprint(rds_instances)
    tenants.extend([{'id_field': 'DBInstanceIdentifier',
                     'id': x['DBInstanceIdentifier'],
                     'type': 'rds'} for x in rds_instances])

    print "...checking for redshift clusters on this vpc..."
    client = session.client('redshift')
    redshift_instances = get_redshift_instances(client, vpc_id)
    #PP.pprint(redshift_instances)
    tenants.extend([{'id_field': 'ClusterIdentifier',
                     'id': x['ClusterIdentifier'],
                     'type': 'redshift'} for x in redshift_instances])

    print "...checking for load balancers on this vpc..."
    client = session.client('elb')
    elb_instances = get_elb_instances(client, vpc_id)
    tenants.extend([{'id_field': 'LoadBalancerName', 'id': x['LoadBalancerName'], 'type': 'elb'} \
            for x in elb_instances])
    #PP.pprint(elb_instances)

    print "...checking for load balancers (v2) on this vpc..."
    client = session.client('elbv2')
    elbv2_instances = get_elbv2_instances(client, vpc_id)
    #PP.pprint(elbv2_instances)
    tenants.extend([{'id_field': 'LoadBalancerName', 'id': x['LoadBalancerName'], 'type': 'elbv2'} \
            for x in elbv2_instances])

    print "...checking for lambda functions on this vpc..."
    client = session.client('lambda')
    lambda_instances = get_lambda_instances(client, vpc_id)
    tenants.extend([{'id_field': 'FunctionName', 'id': x['FunctionName'], 'type': 'lambda'} \
            for x in lambda_instances])

    return tenants

def print_resources(resource_list):
    """ Prints the list of dependent resources"""
    for res in resource_list:
        print "[" + res['type'] +  "]  " + res['id_field'] + ": " + res['id']

def main():
    """
    1.) Delete the internet-gateway
    2.) Delete subnets
    3.) Delete route-tables
    4.) Delete network access-lists
    5.) Delete security-groups
    6.) Delete the VPC
    """

    args = parse_args()
    session = boto3.Session(profile_name=args.profile, region_name=DEFAULT_REGION)
    regions = get_regions(session, args.region)
    dry_run = args.dry_run

    print_warning()

    for region in regions:
        print "----------------------- %s ------------------------" % region
        session = boto3.Session(profile_name=args.profile, region_name=region)
        try:
            ec2_client = session.client('ec2')
            default_vpc = get_default_vpc(ec2_client)
            if default_vpc is None:
                print "No default VPC was found"
            else:
                default_vpc_id = default_vpc['VpcId']

                # check if there are any dependent object that would cause us to stop...
                dependents = get_vpc_tenants(session, default_vpc_id)
                if len(dependents) > 0:
                    print "This VPC has dependent resources, and thus will not be deleted:"
                    print_resources(dependents)

                else:

                    # Get the items to delete
                    igw_list = get_internet_gateways(ec2_client, default_vpc_id)
                    subnet_list = get_subnets(ec2_client, default_vpc_id)
                    route_table_list = get_route_tables(ec2_client, default_vpc_id)
                    nacl_list = get_nacls(ec2_client, default_vpc_id)
                    security_group_list = get_security_groups(ec2_client, default_vpc_id)

                    print "\n\nThe following resources will be deleted:"
                    print_vpc(default_vpc)
                    print_igws(igw_list)
                    print_subnets(subnet_list)
                    print_route_tables(route_table_list)
                    print_nacls(nacl_list)
                    print_security_groups(security_group_list)

                    # Dont take any further action if this is a dry-run
                    if dry_run:
                        print "Taking no action because --dry-run was passed"

                    else:
                        # Delete the VPC!
                        if args.batch or prompt_to_continue():
                            print "Deleting..."
                            delete_internet_gateways(ec2_client, igw_list, default_vpc_id, dry_run)
                            delete_subnets(ec2_client, subnet_list, dry_run)
                            delete_route_tables(ec2_client, route_table_list, dry_run)
                            delete_nacls(ec2_client, nacl_list, dry_run)
                            delete_security_groups(ec2_client, security_group_list, dry_run)
                            delete_vpc(ec2_client, default_vpc_id, dry_run)
                        else:
                            print "Stopping due to user input..."

        except botocore.exceptions.ClientError as err:
            print err.message
            exit(1)



if __name__ == "__main__":

    main()
