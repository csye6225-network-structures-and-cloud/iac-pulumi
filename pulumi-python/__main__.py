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
databasesecuritygroup = data.get("databasesecuritygroup")
username = data.get("username")
password =data.get("password")
name = data.get("name")

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


# Database Security Group
db_security_group = aws.ec2.SecurityGroup(f"{databasesecuritygroup}",
    description="Allow inbound traffic for RDS PostgreSQL",
    vpc_id=Virtual_private_cloud.id,
    ingress=[
        aws.ec2.SecurityGroupIngressArgs(
            description="PostgreSQL",
            from_port=data.get("postgresport"),
            to_port=data.get("postgresport"),
            protocol="tcp",
            security_groups=[app_security_group.id]
        )
    ],
    egress=[
        aws.ec2.SecurityGroupEgressArgs(
            from_port=0,
            to_port=0,
            protocol="-1",
            cidr_blocks=["0.0.0.0/0"]
        )
    ],
    tags={"Name": "f{databasesecuritygroup}"}
)

rds_subnetgroup = aws.rds.SubnetGroup(data.get("rds_subnetgroup"),
    subnet_ids=[
        private_subnets[0].id,
        private_subnets[1].id,
    ],
    tags={
        "Name": "My DB subnet group",
    })


rds_parameter_group = aws.rds.ParameterGroup(data.get("rdsresourcename"),
    name=data.get("csye6225-rdsparameter-group"),  # Unique identifier for the DB parameter group
    family=data.get("rdsfamily"), 
    description="Custom rds parameter group for csye6225",
    tags={"Name": data.get("rdsresourcename")}
)


# RDS Instance
rds_instance = aws.rds.Instance(data.get("rdsinstancename"),
    allocated_storage=data.get("allocated_storage"),
    engine=data.get("engine"),
    engine_version=data.get("engine_version"),  
    instance_class=data.get("instance_class"),
    multi_az=data.get("multi_az"),
    db_name=data.get("db_name"),
    username=username,
    password=password,
    parameter_group_name=rds_parameter_group.name,
    skip_final_snapshot=True,
    vpc_security_group_ids=[db_security_group.id], 
    db_subnet_group_name=rds_subnetgroup.name,
    publicly_accessible=data.get("publicly_accessible"),
    performance_insights_enabled=False,
    tags={"Name": data.get("rds_instance_name")}
)

db_host_output = rds_instance.address.apply(lambda v: v)
db_name=data.get("db_name")
def format_user_data(db_host_value):
    return user_data_template.format(
        db_host=db_host_value,
        db_name=db_name,
        username=username,
        password=password
    )
user_data = db_host_output.apply(format_user_data)


user_data_template = """#!/bin/bash
echo "app.environment=production" >> /home/admin/application.properties
echo "spring.datasource.url=jdbc:postgresql:\/\/{db_host}:5432\/{db_name}" >> /home/admin/application.properties
echo "spring.datasource.username={username}" >> /home/admin/application.properties
echo "spring.datasource.password={password}" >> /home/admin/application.properties
echo "spring.jpa.hibernate.ddl-auto=update" >> /home/admin/application.properties
echo "server.servlet.session.persistent=false" >> /home/admin/application.properties
echo "spring.mvc.throw-exception-if-no-handler-found=true" >> /home/admin/application.properties
echo "spring.web.resources.add-mappings=false" >> /home/admin/application.properties
echo "spring.security.authentication.disable-session-creation=true" >> /home/admin/application.properties
echo "server.port=8080" >> /home/admin/application.properties
echo "spring.jpa.properties.hibernate.dialect= org.hibernate.dialect.PostgreSQLDialect" >> /home/admin/application.properties

chown admin:admin /home/admin/application.properties
chmod 764 /home/admin/application.properties

java -jar /home/admin/webapplication-0.0.1-SNAPSHOT.jar --spring.profiles.active=production --spring.config.location=file:///home/admin/application.properties
"""



ec2_instance = aws.ec2.Instance(f"{vpc_name}-webAppInstance",                                
    instance_type=data.get("instance_type"),
    ami=data.get("ami_id"),
    subnet_id=public_subnets[0].id,  # Placing in the first public subnet
    vpc_security_group_ids=[app_security_group.id],
    key_name = data.get("keyname"),  # Using security group name
    disable_api_termination=False,
    user_data=user_data,
    root_block_device=
        aws.ec2.InstanceRootBlockDeviceArgs(
            delete_on_termination=True,
            volume_size=data.get("volume_size"),
            volume_type=data.get("volume_type")
        ),
    
    tags={"Name": f"{vpc_name}-webAppInstance"}
)