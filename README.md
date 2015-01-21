# botomfa


``import botomfa`` in any of your scripts that utilize the boto SDK.

#### Requirements:

1. You must provide your AWS account number via the environment variable ``AWS_ACT_NUM``
2. The script assumes the identifying value of your MFA device is the same as your shell's ``USER`` variable. To override this, provide the environment variable ``MFA_USER`` with your MFA id.
3. The MFA token is also provided via an the environment variable ``MFA_CODE``


**e.g.** ``arn:aws:iam::AWS_ACT_NUM:mfa/MFA_USER``


### Example


It's probably a good idea to put ``AWS_ACT_NUM`` in your shell startup/source scripts.


##### Example #1
**list_instances.py**

```
MFA_CODE=123456 python list_intances.py
```


##### Example #2
```
>>> import os
>>> os.environ['AWS_ACT_NUM'] = '000000000000'
>>> os.environ['MFA_USER'] = 'karl'
>>> os.environ['MFA_CODE'] = 123456
>>> import boto.ec2
>>> import botomfa
>>> conn = boto.ec2.connect_to_region('us-west-2')
>>> conn.get_only_instances()
[Instance:i-0z0z0z0z, Instance:i-2f2f2f2f]
```
