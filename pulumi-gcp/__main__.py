import pulumi
import pulumi_gcp as gcp

config = pulumi.Config()
data = config.require_object("data")

demoaccount= data.get("demoaccount")

gcp_bucket = gcp.storage.Bucket(data.get("gcp_bucket"),
    location=data.get("location"),
    uniform_bucket_level_access=data.get("uniform_bucket_level_access"),
    force_destroy=data.get("force_destroy"))


service_account = gcp.serviceaccount.Account(data.get("service_account"),
    account_id=data.get("service-account-id"),
    display_name=data.get("display_name"))


mykey = gcp.serviceaccount.Key(data.get("mykey"),
    service_account_id=service_account.name,
    public_key_type=data.get("keytype"))

object_creator = gcp.storage.BucketIAMMember(data.get("object_creator"),
    bucket=gcp_bucket,
    role=data.get("object_creator_role"),
    member=pulumi.Output.concat("serviceAccount:", service_account.email))

object_viewer = gcp.storage.BucketIAMMember(data.get("bucket-object-viewer"),
    bucket=gcp_bucket,
    role=data.get("object_viewer_role"),
    member=pulumi.Output.concat("serviceAccount:", service_account.email))


object_user = gcp.storage.BucketIAMMember(data.get("bucket-object_user"),
    bucket=gcp_bucket,
    role=data.get("object_viewer_user"),
    member=pulumi.Output.concat("serviceAccount:", service_account.email))

pulumi.export("gcp_bucket",gcp_bucket.name)
pulumi.export("mykey",mykey.private_key)

