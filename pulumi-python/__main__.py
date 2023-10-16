import pulumi
import pulumi_aws as aws
import ipaddress
import random

# Fetch the configuration values
config = pulumi.Config()
data = config.require_object("data")

# Extract key configuration values
vpc_name = data.get("vpcName")
vpc_cidr = data.get("vpcCidr")
num_subnets = data.get("no_of_subnets")
applicationsecuritygroup = data.get("applicationsecuritygroup")


# Define availability zones
azs = aws.get_availability_zones().names
num_azs = len(azs)

if num_azs >= 3:
    num_public_subnets = 3
    num_private_subnets = 3
    num_subnets = num_public_subnets + num_private_subnets
else:
    num_public_subnets = num_azs
    num_private_subnets = num_azs
    num_subnets = num_public_subnets + num_private_subnets

def get_subnets(vpc_cidr, num_subnets):
    network = ipaddress.ip_network(vpc_cidr, strict=False)
    return [str(subnet) for subnet in network.subnets(new_prefix=24)][:num_subnets]

# Get all subnets
subnet_cidrs = get_subnets(vpc_cidr, num_subnets)

# Create the VPC using the fetched config values
Virtual_private_cloud = aws.ec2.Vpc(vpc_name,
    cidr_block=vpc_cidr,
    instance_tenancy="default",
    tags={
        "Name": vpc_name,
    })

half_subnets = num_subnets // 2

# Create 3 public and 3 private subnets
public_subnets = []
private_subnets = []

for i in range(half_subnets):
    az_index = i % num_azs
    public_subnet = aws.ec2.Subnet(f"{vpc_name}-public-subnet-{i}",
        cidr_block=subnet_cidrs[i],
        availability_zone=azs[az_index],
        vpc_id=Virtual_private_cloud.id,
        map_public_ip_on_launch=True,
        tags={
            "Name": f"{vpc_name}-public-subnet-{i}",
        })

    private_subnet = aws.ec2.Subnet(f"{vpc_name}-private-subnet-{i}",
        cidr_block=subnet_cidrs[i + half_subnets],
        availability_zone=azs[az_index],
        vpc_id=Virtual_private_cloud.id,
        tags={
            "Name": f"{vpc_name}-private-subnet-{i}",
        })

    public_subnets.append(public_subnet)
    private_subnets.append(private_subnet)

# Create an Internet Gateway and attach it to the VPC
internet_gateway = aws.ec2.InternetGateway(f"{vpc_name}-internet-gateway",
    vpc_id=Virtual_private_cloud.id,
    tags={
        "Name": f"{vpc_name}-internet-gateway",
    })

# Create a public route table
public_route_table = aws.ec2.RouteTable(f"{vpc_name}-public-route-table",
    vpc_id=Virtual_private_cloud.id,
    tags={
        "Name": f"{vpc_name}-public-route-table",
    })

# Associate public subnets with the public route table
for subnet in public_subnets:
    aws.ec2.RouteTableAssociation(f"{subnet._name}-association",
        subnet_id=subnet.id,
        route_table_id=public_route_table.id)

# Create a private route table
private_route_table = aws.ec2.RouteTable(f"{vpc_name}-private-route-table",
    vpc_id=Virtual_private_cloud.id,
    tags={
        "Name": f"{vpc_name}-private-route-table",
    })

# Associate private subnets with the private route table
for subnet in private_subnets:
    aws.ec2.RouteTableAssociation(f"{subnet._name}-association",
        subnet_id=subnet.id,
        route_table_id=private_route_table.id)

# Create a public route in the public route table
public_route = aws.ec2.Route(f"{vpc_name}-public-route",
    route_table_id=public_route_table.id,
    destination_cidr_block=data.get("destination_cidr_block"),
    gateway_id=internet_gateway.id)

# Application Security Group
app_security_group = aws.ec2.SecurityGroup(f"{applicationsecuritygroup}",
    description="Allow inbound traffic for application",
    vpc_id=Virtual_private_cloud.id,
    ingress=[
        aws.ec2.SecurityGroupIngressArgs(
            description="SSH",
            from_port=22,
            to_port=22,
            protocol="tcp",
            cidr_blocks=["0.0.0.0/0"]
        ),
        aws.ec2.SecurityGroupIngressArgs(
            description="HTTP",
            from_port=80,
            to_port=80,
            protocol="tcp",
            cidr_blocks=["0.0.0.0/0"]
        ),
        aws.ec2.SecurityGroupIngressArgs(
            description="App Port 8080",
            from_port=8080,
            to_port=8080,
            protocol="tcp",
            cidr_blocks=["0.0.0.0/0"]
            ),
        aws.ec2.SecurityGroupIngressArgs(
            description="HTTPS",
            from_port=443,
            to_port=443,
            protocol="tcp",
            cidr_blocks=["0.0.0.0/0"]
        ),

     
    ],
    egress=[
        aws.ec2.SecurityGroupEgressArgs(
            from_port=0,
            to_port=0,
            protocol="-1",
            cidr_blocks=["0.0.0.0/0"]
        )
    ],
    tags={"Name": f"{applicationsecuritygroup}"}
)


ec2_instance = aws.ec2.Instance("webAppInstance",
    instance_type="t2.micro",
    ami=data.get("ami_id"),
    subnet_id=public_subnets[0].id,  # Placing in the first public subnet
    vpc_security_group_ids=[app_security_group.id],
    key_name = data.get("keyname"),  # Using security group name
    root_block_device=
        aws.ec2.InstanceRootBlockDeviceArgs(
            delete_on_termination=True,
            volume_size=data.get("volume_size"),
            volume_type=data.get("volume_type")
        ),
    tags={"Name": "webAppInstance"}
)