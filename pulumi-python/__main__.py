import pulumi
import pulumi_aws as aws
import ipaddress
import json

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
app_port= data.get("app_port")
http_port = data.get("http_port")
https_port = data.get("https_port")
ssh_port = data.get("ssh_port")
protocol = data.get("protocol")
db_name=data.get("db_name")
hibernate_update=data.get("hibernate_update")
hibernate_dialect=data.get("hibernate_dialect")
app_environment=data.get("app_environment")
security_authentication_disable= data.get("security_authentication_disable")
servlet_session_persistent = data.get("servlet_session_persistent")
no_handler_exception = data.get("no_handler_exception")
resources_mappings = data.get("resources_mappings")
file_path=data.get("file_path")
logging_level=data.get("logging_level")
publish_metrics=data.get("publish_metrics")
metrics_server_hostname=data.get("metrics_server_hostname")
metrics_server_port=data.get("metrics_server_port")
azs_value = data.get("azs_value")
db_name=data.get("db_name")
hibernate_update=data.get("hibernate_update")
hibernate_dialect=data.get("hibernate_dialect")
app_environment=data.get("app_environment")
security_authentication_disable= data.get("security_authentication_disable")
servlet_session_persistent = data.get("servlet_session_persistent")
no_handler_exception = data.get("no_handler_exception")
resources_mappings = data.get("resources_mappings")
file_path=data.get("file_path")
logging_level=data.get("logging_level")
publish_metrics=data.get("publish_metrics")
metrics_server_hostname=data.get("metrics_server_hostname")
metrics_server_port=data.get("metrics_server_port")
azs_value = data.get("azs_value")
# Define availability zones
azs = aws.get_availability_zones().names
num_azs = len(azs)

if num_azs >= azs_value:
    num_public_subnets = azs_value
    num_private_subnets = azs_value
if num_azs >= azs_value:
    num_public_subnets = azs_value
    num_private_subnets = azs_value
    num_subnets = num_public_subnets + num_private_subnets
else:
    num_public_subnets = num_azs
    num_private_subnets = num_azs
    num_subnets = num_public_subnets + num_private_subnets

def get_subnets(vpc_cidr, num_subnets):
    network = ipaddress.ip_network(vpc_cidr, strict=False)
    return [str(subnet) for subnet in network.subnets(new_prefix=data.get("subnet_mask"))][:num_subnets]

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


# Load Balancer Security Group
lb_security_group = aws.ec2.SecurityGroup("loadBalancerSecurityGroup",
    vpc_id=Virtual_private_cloud.id,
    description="Security group for Load Balancer",
    ingress=[
        aws.ec2.SecurityGroupIngressArgs(
            description="HTTP",
            from_port=http_port,  # 80
            to_port=http_port,
            protocol=protocol,
            cidr_blocks=[data.get("cidr_blocks")]
        ),
        aws.ec2.SecurityGroupIngressArgs(
            description="HTTPS",
            from_port=https_port, # 443
            to_port=https_port,
            protocol=protocol,
            cidr_blocks=[data.get("cidr_blocks")]
        ),
    ],

    egress=[
        aws.ec2.SecurityGroupEgressArgs(
            from_port=data.get("egressport"),
            to_port=data.get("egressport"),
            protocol=data.get("egress_protocol"),
            cidr_blocks=[data.get("cidr_blocks")]
        )
    ],
    tags={"Name": "loadBalancerSecurityGroup"}
)



# Load Balancer Security Group
lb_security_group = aws.ec2.SecurityGroup("loadBalancerSecurityGroup",
    vpc_id=Virtual_private_cloud.id,
    description="Security group for Load Balancer",
    ingress=[
        aws.ec2.SecurityGroupIngressArgs(
            description="HTTP",
            from_port=http_port,  # 80
            to_port=http_port,
            protocol=protocol,
            cidr_blocks=[data.get("cidr_blocks")]
        ),
        aws.ec2.SecurityGroupIngressArgs(
            description="HTTPS",
            from_port=https_port, # 443
            to_port=https_port,
            protocol=protocol,
            cidr_blocks=[data.get("cidr_blocks")]
        ),
    ],

    egress=[
        aws.ec2.SecurityGroupEgressArgs(
            from_port=data.get("egressport"),
            to_port=data.get("egressport"),
            protocol=data.get("egress_protocol"),
            cidr_blocks=[data.get("cidr_blocks")]
        )
    ],
    tags={"Name": "loadBalancerSecurityGroup"}
)


# Application Security Group
app_security_group = aws.ec2.SecurityGroup(f"{applicationsecuritygroup}",
    description="Allow inbound traffic for application",
    vpc_id=Virtual_private_cloud.id,
    ingress=[
        aws.ec2.SecurityGroupIngressArgs(
            description="SSH",
            from_port=ssh_port, #22
            to_port=ssh_port,
            protocol=protocol,
            security_groups=[lb_security_group.id]
        ),
        # aws.ec2.SecurityGroupIngressArgs(
        #     description="HTTP",
        #     from_port=http_port,
        #     to_port=http_port,
        #     protocol=protocol,
        #     cidr_blocks=["0.0.0.0/0"]
        # ),
        # aws.ec2.SecurityGroupIngressArgs(
        #     description="HTTP",
        #     from_port=http_port,
        #     to_port=http_port,
        #     protocol=protocol,
        #     cidr_blocks=["0.0.0.0/0"]
        # ),
        aws.ec2.SecurityGroupIngressArgs(
            description="App Port 8080",
            from_port=app_port,
            to_port=app_port,
            protocol=protocol,
            security_groups=[lb_security_group.id]
            ),
        # aws.ec2.SecurityGroupIngressArgs(
        #     description="HTTPS",
        #     from_port=https_port,
        #     to_port=https_port,
        #     protocol=protocol,
        #     cidr_blocks=["0.0.0.0/0"]
        # ),  
        # aws.ec2.SecurityGroupIngressArgs(
        #     description="HTTPS",
        #     from_port=https_port,
        #     to_port=https_port,
        #     protocol=protocol,
        #     cidr_blocks=["0.0.0.0/0"]
        # ),  
    ],
    egress=[
        aws.ec2.SecurityGroupEgressArgs(
            from_port=data.get("egressport"),
            to_port=data.get("egressport"),
            protocol=data.get("egress_protocol"),
            cidr_blocks=[data.get("cidr_blocks")]
           
        )
    ],
    tags={"Name": f"{applicationsecuritygroup}"}
)


# Database Security Group
db_security_group = aws.ec2.SecurityGroup(databasesecuritygroup,
    description="Allow inbound traffic for RDS PostgreSQL",
    vpc_id=Virtual_private_cloud.id,
    ingress=[
        aws.ec2.SecurityGroupIngressArgs(
            description="PostgreSQL",
            from_port=data.get("postgresport"),
            to_port=data.get("postgresport"),
            protocol=protocol,
            security_groups=[app_security_group.id]
        )
    ],
    egress=[
        aws.ec2.SecurityGroupEgressArgs(
            from_port=data.get("egressport"),
            to_port=data.get("egressport"),
            protocol=data.get("egress_protocol"),
            cidr_blocks=[data.get("cidr_blocks")]
            
        )
    ],
    tags={"Name": databasesecuritygroup}
)


#RDS SUBNET GROUP

#RDS SUBNET GROUP
rds_subnetgroup = aws.rds.SubnetGroup(data.get("rds_subnetgroup"),
    subnet_ids=[
        private_subnets[0].id,
        private_subnets[1].id,
    ],
    tags={
        "Name": data.get("rds_subnetgroup"),
    })

#RDS PARAMETER GROUP
#RDS PARAMETER GROUP
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
    skip_final_snapshot=data.get("skip_final_snapshot"),
    vpc_security_group_ids=[db_security_group.id], 
    db_subnet_group_name=rds_subnetgroup.name,
    publicly_accessible=data.get("publicly_accessible"),
    performance_insights_enabled=data.get("performance_insights_enabled"),
    tags={"Name": data.get("rds_instance_name")}
)


#USER DATA

# db_host_output = rds_instance.address.apply(lambda v: v)
# def format_user_data(db_host_value):
#     user_data_decoded = user_data_template.format(
#         db_host=db_host_value,
#         db_name=db_name,
#         username=username,
#         password=password,
#         hibernate_update=hibernate_update,
#         hibernate_dialect=hibernate_dialect,
#         app_environment=app_environment,
#         security_authentication_disable=security_authentication_disable,
#         servlet_session_persistent=servlet_session_persistent,
#         no_handler_exception=no_handler_exception,
#         resources_mappings=resources_mappings,
#         app_port=app_port,
#         file_path=file_path,
#         logging_level=logging_level,
#         publish_metrics=publish_metrics,
#         metrics_server_hostname=metrics_server_hostname,
#         metrics_server_port=metrics_server_port
#     )
#     user_data_encoded = base64.b64encode(user_data_decoded.encode('utf-8')).decode('utf-8')
#     return user_data_encoded

    
# user_data = db_host_output.apply(format_user_data)
# user_data_template = """#!/bin/bash
# # Writing the application.properties file
# cat <<EOL | sudo tee /opt/csye6225/application.properties

#USER DATA

# db_host_output = rds_instance.address.apply(lambda v: v)
# def format_user_data(db_host_value):
#     user_data_decoded = user_data_template.format(
#         db_host=db_host_value,
#         db_name=db_name,
#         username=username,
#         password=password,
#         hibernate_update=hibernate_update,
#         hibernate_dialect=hibernate_dialect,
#         app_environment=app_environment,
#         security_authentication_disable=security_authentication_disable,
#         servlet_session_persistent=servlet_session_persistent,
#         no_handler_exception=no_handler_exception,
#         resources_mappings=resources_mappings,
#         app_port=app_port,
#         file_path=file_path,
#         logging_level=logging_level,
#         publish_metrics=publish_metrics,
#         metrics_server_hostname=metrics_server_hostname,
#         metrics_server_port=metrics_server_port
#     )
#     user_data_encoded = base64.b64encode(user_data_decoded.encode('utf-8')).decode('utf-8')
#     return user_data_encoded

    
# user_data = db_host_output.apply(format_user_data)
# user_data_template = """#!/bin/bash
# # Writing the application.properties file
# cat <<EOL | sudo tee /opt/csye6225/application.properties

# app.environment={app_environment}
# spring.datasource.url=jdbc:postgresql://{db_host}:5432/{db_name}
# spring.datasource.username={username}
# spring.datasource.password={password}
# spring.jpa.hibernate.ddl-auto={hibernate_update}
# server.servlet.session.persistent={servlet_session_persistent}
# spring.mvc.throw-exception-if-no-handler-found={no_handler_exception}
# spring.web.resources.add-mappings={resources_mappings}
# spring.security.authentication.disable-session-creation={security_authentication_disable}
# server.port={app_port}
# spring.jpa.properties.hibernate.dialect={hibernate_dialect}
# logging.file.path={file_path}
# logging.level.root={logging_level}
# logging.level.com.example.webapplication.*={logging_level}
# publish.metrics={publish_metrics}
# metrics.server.hostname={metrics_server_hostname}
# metrics.server.port={metrics_server_port} 
# app.environment={app_environment}
# spring.datasource.url=jdbc:postgresql://{db_host}:5432/{db_name}
# spring.datasource.username={username}
# spring.datasource.password={password}
# spring.jpa.hibernate.ddl-auto={hibernate_update}
# server.servlet.session.persistent={servlet_session_persistent}
# spring.mvc.throw-exception-if-no-handler-found={no_handler_exception}
# spring.web.resources.add-mappings={resources_mappings}
# spring.security.authentication.disable-session-creation={security_authentication_disable}
# server.port={app_port}
# spring.jpa.properties.hibernate.dialect={hibernate_dialect}
# logging.file.path={file_path}
# logging.level.root={logging_level}
# logging.level.com.example.webapplication.*={logging_level}
# publish.metrics={publish_metrics}
# metrics.server.hostname={metrics_server_hostname}
# metrics.server.port={metrics_server_port} 

# EOL
# EOL

# # moving file
# sudo mv /home/admin/webapplication-0.0.1-SNAPSHOT.jar /opt/csye6225/
# sudo mv /home/admin/cloudwatch-config.json /opt/csye6225/
# # moving file
# sudo mv /home/admin/webapplication-0.0.1-SNAPSHOT.jar /opt/csye6225/
# sudo mv /home/admin/cloudwatch-config.json /opt/csye6225/

# # Start CloudWatch agent
# sudo /opt/aws/amazon-cloudwatch-agent/bin/amazon-cloudwatch-agent-ctl \
#     -a fetch-config \
#     -m ec2 \
#     -c file:/opt/csye6225/cloudwatch-config.json \
#     -s
# # Start CloudWatch agent
# sudo /opt/aws/amazon-cloudwatch-agent/bin/amazon-cloudwatch-agent-ctl \
#     -a fetch-config \
#     -m ec2 \
#     -c file:/opt/csye6225/cloudwatch-config.json \
#     -s


# """
# """


EC2_CloudWatchRole = aws.iam.Role(data.get("EC2_CloudWatchRole"),
    assume_role_policy=json.dumps({
        "Version": "2012-10-17",
        "Statement": [{
            "Action": "sts:AssumeRole",
            "Effect": "Allow",
            "Sid": "",
            "Principal": {
                "Service": "ec2.amazonaws.com",
            },
        }],
    }),
    tags={
        "Name": data.get("EC2_CloudWatchRole"),
        "Name": data.get("EC2_CloudWatchRole"),
    })


cloudwatch_policy = aws.iam.RolePolicy(data.get("Webapp-cloudwatch-policy"),
    role=EC2_CloudWatchRole.name,
    policy=json.dumps({

    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "cloudwatch:PutMetricData",
                "ec2:DescribeTags",
                "logs:PutLogEvents",
                "logs:DescribeLogStreams",
                "logs:DescribeLogGroups",
                "logs:CreateLogStream",
                "logs:CreateLogGroup"
            ],
            "Resource": "*"
        },
        {
            "Effect": "Allow",
            "Action": [
                "ssm:GetParameter",
                "ssm:PutParameter"
            ],
            "Resource": "arn:aws:ssm:*:*:parameter/AmazonCloudWatch-*"
        }, ]  
        },   
))


ec2_instance_profile = aws.iam.InstanceProfile(data.get("webapp-ec2-instance-profile"),
    role=EC2_CloudWatchRole.name
)


# ec2_instance = aws.ec2.Instance(f"{vpc_name}-webAppInstance",   
# ec2_instance = aws.ec2.Instance(f"{vpc_name}-webAppInstance",   

#     instance_type=data.get("instance_type"),
#     ami=data.get("ami_id"),
#     subnet_id=public_subnets[0].id,  # Placing in the first public subnet                          
#     vpc_security_group_ids=[app_security_group.id],
#     key_name = data.get("keyname"),  # Using security group name
#     disable_api_termination=data.get("disable_api_termination"),  
#     user_data=user_data,
#     iam_instance_profile= ec2_instance_profile.name,  
#     root_block_device=
#         aws.ec2.InstanceRootBlockDeviceArgs(
#             delete_on_termination=data.get("delete_on_termination"),
#             volume_size=data.get("volume_size"),
#             volume_type=data.get("volume_type")
#         ),
    
#     tags={"Name": f"{vpc_name}-webAppInstance"}
# )


pulumi.export('vpc_id', Virtual_private_cloud.id)
pulumi.export('app_security_group_id', app_security_group.id)
pulumi.export('db_security_group_id', db_security_group.id)
pulumi.export('lb_security_group_id',lb_security_group.id)
pulumi.export('rds_instance_id',rds_instance)
pulumi.export('ec2_instance_profile',ec2_instance_profile.name)
public_subnet_ids = [subnet.id for subnet in public_subnets]
pulumi.export('public_subnet_ids', public_subnet_ids)
pulumi.export('public_subnets', public_subnets)
pulumi.export('azs',azs)
pulumi.export('EC2_CloudWatchRole',EC2_CloudWatchRole.name)


