# iac-pulumi

## AWS Networking Setup¶
Here is what you need to do for networking infrastructure setup:

- Create Virtual Private Cloud (VPC).
- Create subnets in your VPC. You must create 3 public subnets and 3 private subnets, each in a different availability zone in the same region in the same VPC.
- Create an Internet Gateway resource and attach the Internet Gateway to the VPC.
- Create a public route table. Attach all public subnets created to the route table.
- Create a private route table. Attach all private subnets created to the route table.
- Create a public route in the public route table created above with the destination CIDR block 0.0.0.0/0 and the internet gateway created above as the target.
- Application Security Group
- Create an EC2 security group for your EC2 instances that will host web applications.

## Infrastructure as Code with Pulumi¶
For this objective, you must complete the following tasks:

- Install and set up the AWS command-line interface.
- Write Pulumi code in a high level language (you cannot use YAML) all the networking resources.
- Values should not be hard coded in your code.

## Auto Scaling stack Setup:
- Web Application Access: Restricted direct access via EC2 IP; accessible only through load balancer.
- Launch Template: Custom AMI, t2.micro instances, specific key and security settings.
- Auto Scaling Group: Min 1, Max 3 instances, cooldown period 60 seconds.
- Scaling Policies: Scale up on >5% CPU usage, scale down on <3% CPU usage.
  
# Application Load Balancer:
- Integrated with EC2 instances in the auto-scaling group.
- Configuration for HTTP traffic on port 80.
- Attached specific security group to the load balancer.

# Amazon SNS Configuration: 
- Implemented using Pulumi for topic creation, facilitating notifications related to web application updates.
- Google Cloud Setup: Involves creating projects and enabling services, alongside local gcloud CLI setup.
- Infrastructure as Code with Pulumi: Establishes Google Cloud Storage, Service Accounts, Lambda Functions, and DynamoDB instances, including IAM roles and policies.

# SSL Certificate Acquisition: 
- Configured load balancer to utilize the imported SSL certificate for secure connections and allowed port 443 for HTTPS.

## Useful commands 

- pulumi stack init demo
- pulumi config set aws:profile demo
- pulumi config set aws:region us-east-1
- pulumi config set vpcCidr "10.0.0.0/16"
- pulumi config set vpcName "demo"
- pulumi stack rm demo


sudo apt install postgresql postgresql-contrib -y
sudo apt-get install postgresql-client
PGPASSWORD=csye6225 psql -h db_host -U csye6225 -d csye6225



*** GET Healthz

seq 1 500 | xargs -n1 -P20  curl "http://demo.supriyavallarapu.me/healthz"

*** POST request

seq 1 500 | xargs -n1 -P20 -I{} curl -X POST -H "Content-Type: application/json" -u "john.doe@example.com:abc123" -d '{
    "name": "Assignment 08",
    "points": 9,
    "num_of_attempts": 2,
    "deadline": "2016-08-29T09:12:33.001Z"
}' "http://demo.supriyavallarapu.me/v1/assignments"


*** PUT request

seq 1 500 | xargs -n1 -P20 -I{} curl -X PUT -H "Content-Type: application/json" -u "john.doe@example.com:abc123" -d '{
    "name": "Assignment 08 updated",
    "points": 9,
    "num_of_attempts": 2,
    "deadline": "2016-08-29T09:12:33.001Z"
}' "http://demo.supriyavallarapu.me/v1/assignments/ffe99570-2052-4ebb-bb81-51dfda279ac4"


*** GET by ID

seq 1 500 | xargs -n1 -P20 -I{} curl -X GET -H "Content-Type: application/json" -u "john.doe@example.com:abc123" "http://demo.supriyavallarapu.me/v1/assignments/ffe99570-2052-4ebb-bb81-51dfda279ac4"


*** GET ALL

seq 1 500 | xargs -n1 -P20 -I{} curl -X GET -H "Content-Type: application/json" -u "john.doe@example.com:abc123" "http://demo.supriyavallarapu.me/v1/assignments"

*** DELETE by ID

seq 1 500 | xargs -n1 -P20 -I{} curl -X DELETE -H "Content-Type: application/json" -u "john.doe@example.com:abc123" "http://demo.supriyavallarapu.me/v1/assignments/ffe99570-2052-4ebb-bb81-51dfda279ac4"
