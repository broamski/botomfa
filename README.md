# botomfa


``import botomfa`` in any of your scripts that utilize the boto SDK.

#### Requirements:

1. You must provide your AWS account number via the environment variable ``AWS_ACT_NUM``
2. The script assumes the identifying value of your MFA device is the same as your shell's ``USER`` variable. To override this, provide the environment variable ``MFA_USER`` with your MFA id.


**e.g.** ``arn:aws:iam::AWS_ACT_NUM:mfa/MFA_USER``


### Example

```
>>> import os
>>> os.environ['AWS_ACT_NUM'] = '000000000000'
>>> os.environ['MFA_USER'] = 'karl'
>>> import boto.ec2
>>> import botomfa
Enter your AWS MFA code: 123456
>>> conn = boto.ec2.connect_to_region('us-west-2')
>>> conn.get_only_instances()
[Instance:i-0z0z0z0z, Instance:i-2f2f2f2f]
```