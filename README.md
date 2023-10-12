# iac-pulumi

## AWS Networking Setup¶
Here is what you need to do for networking infrastructure setup:

- Create Virtual Private Cloud (VPC).
- Create subnets in your VPC. You must create 3 public subnets and 3 private subnets, each in a different availability zone in the same region in the same VPC.
- Create an Internet Gateway resource and attach the Internet Gateway to the VPC.
- Create a public route table. Attach all public subnets created to the route table.
- Create a private route table. Attach all private subnets created to the route table.
- Create a public route in the public route table created above with the destination CIDR block 0.0.0.0/0 and the internet gateway created above as the target.

## Infrastructure as Code with Pulumi¶
For this objective, you must complete the following tasks:

- Install and set up the AWS command-line interface.
- Write Pulumi code in a high level language (you cannot use YAML) all the networking resources.
- Values should not be hard coded in your code.

## Useful commands 

pulumi stack init demo
pulumi config set aws:profile demo
pulumi config set aws:region us-east-1
pulumi config set vpcCidr "10.0.0.0/16"
pulumi config set vpcName "demo"

pulumi stack rm demo
