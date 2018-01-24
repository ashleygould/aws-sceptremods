import sys
from troposphere import (
    s3,
    Region,
    AccountId,
    FindInMap,
    Join,
    Output,
    Ref,
)
from sceptremods.templates import BaseTemplate


#
# The template class
#
class ALB_LOG_BUCKET(BaseTemplate):

    VARSPEC = {
        "BucketName": {
            "type": str,
            #"default": str(),
            "default": "testing123",
            "description": "Name of the S3 log bucket.",
        },
        "BucketPrefix": {
            "type": str,
            #"default": str(),
            "default": "testing123",
            "description": "Prefix to use for ALB logging to bucket.",
        },
    }

    ELB_ACCOUNT_ID = {
        "us-east-1": {"ELBAccountId": "127311923021"},
        "us-east-2": {"ELBAccountId": "033677994240"},
        "us-west-1": {"ELBAccountId": "027434742980"},
        "us-west-2": {"ELBAccountId": "797873946194"},
    }


    def munge_policy_resourse(self):
        """Assemble a bucket policy statement resource arn per ELB requirements"""
        bucket_arn = Join("", ["arn:aws:s3:::", Ref(self.log_bucket)])
        return Join("/", [
            bucket_arn, self.vars['BucketPrefix'], "AWSLogs", AccountId, "*"
        ]) 


    def create_template(self):
        self.vars = self.validate_user_data()
        t = self.template
        t.add_description(self.vars["BucketName"] + "log bucket")
        t.add_mapping("RegionalELBAccountIds", self.ELB_ACCOUNT_ID)
        
        self.log_bucket = t.add_resource(s3.Bucket(
            "LogBucket",
            BucketName=self.vars["BucketName"],
        ))

        t.add_resource(s3.BucketPolicy(
            "LogBucketPolicy",
            Bucket=Ref(self.log_bucket),
            PolicyDocument={
                "Statement": [{
                    "Action": ["s3:PutObject"],
                    "Principal": {
                        "AWS": [FindInMap(
                            "RegionalELBAccountIds",
                            Region,
                            "ELBAccountId",
                        )]
                    },
                    "Resource": self.munge_policy_resourse(),
                    "Effect": "Allow",
                }]
            },
        ))
        
        t.add_output(Output(
            "LogBucket",
            Description="Cloudfront S3 website log bucket",
            Value=Ref(self.log_bucket),
        ))


#
# The sceptre handler
#
def sceptre_handler(sceptre_user_data):
    alb_log_bucket = ALB_LOG_BUCKET(sceptre_user_data)
    alb_log_bucket.create_template()
    return alb_log_bucket.template.to_json()

def main():
    """
    When called as a script, print out the generated template.
    If any arg is supplied, call the template class help method.
    """
    if len(sys.argv) > 1:
        ALB_LOG_BUCKET().help()
    else:
        print(sceptre_handler(dict()))


if __name__ == "__main__":
    main()
