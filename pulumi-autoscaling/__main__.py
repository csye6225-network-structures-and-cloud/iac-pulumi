import pulumi
from pulumi import Config
import pulumi_aws as aws
import base64


# Taking reference from another stack

stack_ref = pulumi.StackReference("vallaras23/pulumi-python/demo")
vpc_id = stack_ref.get_output('vpc_id')
app_security_group_id = stack_ref.get_output('app_security_group_id')
db_security_group_id = stack_ref.get_output('db_security_group_id')
lb_security_group_id = stack_ref.get_output('lb_security_group_id')
rds_instance = stack_ref.get_output('rds_instance_id')
ec2_instance_profile=stack_ref.get_output('ec2_instance_profile')
public_subnet_ids = stack_ref.get_output('public_subnet_ids')

azs=stack_ref.get_output('azs')

# Creating a Config object to access the configurations
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


#USER DATA
db_host_output = rds_instance.apply(lambda instance: instance['address'])
def format_user_data(db_host_value):
    user_data_decoded =  user_data_template.format(
        db_host=db_host_value,
        db_name=db_name,
        username=username,
        password=password,
        hibernate_update=hibernate_update,
        hibernate_dialect=hibernate_dialect,
        app_environment=app_environment,
        security_authentication_disable=security_authentication_disable,
        servlet_session_persistent=servlet_session_persistent,
        no_handler_exception=no_handler_exception,
        resources_mappings=resources_mappings,
        app_port=app_port,
        file_path=file_path,
        logging_level=logging_level,
        publish_metrics=publish_metrics,
        metrics_server_hostname=metrics_server_hostname,
        metrics_server_port=metrics_server_port
    )
    user_data_encoded = base64.b64encode(user_data_decoded.encode('utf-8')).decode('utf-8')
    return user_data_encoded

user_data = db_host_output.apply(format_user_data)

user_data_template = """#!/bin/bash
# Writing the application.properties file
cat <<EOL | sudo tee /opt/csye6225/application.properties

app.environment={app_environment}
spring.datasource.url=jdbc:postgresql://{db_host}:5432/{db_name}
spring.datasource.username={username}
spring.datasource.password={password}
spring.jpa.hibernate.ddl-auto={hibernate_update}
server.servlet.session.persistent={servlet_session_persistent}
spring.mvc.throw-exception-if-no-handler-found={no_handler_exception}
spring.web.resources.add-mappings={resources_mappings}
spring.security.authentication.disable-session-creation={security_authentication_disable}
server.port={app_port}
spring.jpa.properties.hibernate.dialect={hibernate_dialect}
logging.file.path={file_path}
logging.level.root={logging_level}
logging.level.com.example.webapplication.*={logging_level}
publish.metrics={publish_metrics}
metrics.server.hostname={metrics_server_hostname}
metrics.server.port={metrics_server_port} 

EOL

# moving file
sudo mv /home/admin/webapplication-0.0.1-SNAPSHOT.jar /opt/csye6225/
sudo mv /home/admin/cloudwatch-config.json /opt/csye6225/

sudo iptables -t nat -A PREROUTING -p tcp --dport 80 -j REDIRECT --to-ports 8080


# Start CloudWatch agent
sudo /opt/aws/amazon-cloudwatch-agent/bin/amazon-cloudwatch-agent-ctl \
    -a fetch-config \
    -m ec2 \
    -c file:/opt/csye6225/cloudwatch-config.json \
    -s
"""

LaunchTemplate = aws.ec2.LaunchTemplate(data.get("launchtemplatename"),
    
    image_id=data.get("ami_id"),
    instance_type=data.get("instance_type"),
    key_name=data.get("keyname"),
    network_interfaces=[aws.ec2.LaunchTemplateNetworkInterfaceArgs(
        associate_public_ip_address=data.get("associate_public_ip_address"), 
        security_groups=[app_security_group_id],  
    )],
    iam_instance_profile={
        "name": ec2_instance_profile,  
    },
    user_data=user_data,
    tag_specifications=[aws.ec2.LaunchTemplateTagSpecificationArgs(
        resource_type=data.get("resource_type"),
        tags={
            "Name": data.get("launchtemplatename")
        }
    )],
    block_device_mappings=[aws.ec2.LaunchTemplateBlockDeviceMappingArgs(
        device_name=data.get("device_name"),
        ebs=aws.ec2.LaunchTemplateBlockDeviceMappingEbsArgs(
        delete_on_termination=data.get("delete_on_termination"),
        volume_size=data.get("volume_size"),
        volume_type=data.get("volume_type"),
        ),
    )],
    # User data script to configure the instance

)

# Target Group for ALB
target_group = aws.lb.TargetGroup(data.get("targetgroupname"),
    port=app_port,
    protocol=data.get("http_protocol"),
    vpc_id=vpc_id,
    health_check=aws.lb.TargetGroupHealthCheckArgs(
        healthy_threshold=data.get("unhealthy_healthy_threshold"),
        unhealthy_threshold=data.get("unhealthy_healthy_threshold"),
        timeout=data.get("healthchecktimeout"),
        path=data.get("healthcheckpath"),
        interval=data.get("healthcheckinterval"),
    ),
    target_type=data.get("target_type"))


autoscaling_group = aws.autoscaling.Group(data.get("asg_name"),                      
    desired_capacity=data.get("asg_desired_capacity"),
    max_size=data.get("asg_max_size"),
    min_size=data.get("asg_min_size"),
    target_group_arns=[target_group.arn],
    vpc_zone_identifiers=public_subnet_ids,
    launch_template={
        "id": LaunchTemplate.id,  # Reference to the ID of the launch template
        "version": "$Latest",  
    },
    tags=[{
        "key": data.get("asg_tags_key"),
        "value": data.get("asg_tags_value"),
        "propagate_at_launch": data.get("propagate_at_launch"),  
    }],
)



# Scale Up Policy
scale_up_policy = aws.autoscaling.Policy(data.get("scaleuppolicy"),
    scaling_adjustment=data.get("scaling_up_adjustment"),
    adjustment_type=data.get("adjustment_type"),
    cooldown=data.get("cooldown"),
    autoscaling_group_name=autoscaling_group.name,
    policy_type=data.get("policy_type"),
)

# CPU Utilization Alarm for Scale Up
scale_up_alarm = aws.cloudwatch.MetricAlarm(data.get("scaleupalarm"),
    comparison_operator=data.get("comparison_operator_up"),
    evaluation_periods=data.get("evaluation_periods"),
    metric_name=data.get("metric_name"),
    namespace=data.get("namespace"),
    period=data.get("period"),
    statistic=data.get("statistic"),
    threshold=data.get("threshold_up"),
    alarm_actions=[scale_up_policy.arn],
    dimensions={"AutoScalingGroupName": autoscaling_group.name},
)

# Scale Down Policy
scale_down_policy = aws.autoscaling.Policy(data.get("scaledownpolicy"),
    scaling_adjustment=data.get("scaling_down_adjustment"),
    adjustment_type=data.get("adjustment_type"),
    cooldown=data.get("cooldown"),
    autoscaling_group_name=autoscaling_group.name,
    policy_type=data.get("policy_type"),
    
)

# CPU Utilization Alarm for Scale Down
scale_down_alarm = aws.cloudwatch.MetricAlarm(data.get("scaledownalarm"),
    comparison_operator=data.get("comparison_operator_down"),
    evaluation_periods=data.get("evaluation_periods"),
    metric_name=data.get("metric_name"),
    namespace=data.get("namespace"),
    period=data.get("period"),
    statistic=data.get("statistic"),
    threshold=data.get("threshold_down"),
    alarm_actions=[scale_down_policy.arn],
    dimensions={"AutoScalingGroupName": autoscaling_group.name},
)


# Application Load Balancer
alb = aws.lb.LoadBalancer(data.get("webappAppLoadBalancer"),
    internal=data.get("internal"),
    load_balancer_type=data.get("load_balancer_type"),
    security_groups=[lb_security_group_id],  # Security Group for the ALB
    subnets=public_subnet_ids,  # List of public subnet IDs
    enable_http2=data.get("enable_http2"))



# Listener for ALB
listener = aws.lb.Listener(data.get("listener"),
    load_balancer_arn=alb.arn,
    port=http_port, #listener port 80
    default_actions=[
        aws.lb.ListenerDefaultActionArgs(
            type=data.get("Listener_type"),
            target_group_arn=target_group.arn,
        )
    ])

# A record

hosted_zone_id = data.get("hosted_zone_id")
a_record = aws.route53.Record(f"{vpc_name}-a-record",
    zone_id=hosted_zone_id,
    name=data.get("hosted_zone_name"),
    type=data.get("type"),
    aliases=[
        aws.route53.RecordAliasArgs(
            name=alb.dns_name,
            zone_id=alb.zone_id,
            evaluate_target_health=data.get("evaluate_target_health"),
        )
    ],
)


