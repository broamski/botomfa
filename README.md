
# botomfa: boto + multi-factor authentication (MFA) enabled accounts


**botomfa** makes it easy to use boto, the AWS SDK for Python, with AWS IAM user accounts that have multi-factor authentication (MFA) enabled.

**botomfa** utilizes your long-term IAM User Access Keys to obtain temporary ``AWS_ACCESS_KEY_ID``, ``AWS_SECRET_ACCESS_KEY``, and ``AWS_SECURITY_TOKEN``  values from [AWS Security Token Service](http://docs.aws.amazon.com/STS/latest/APIReference/Welcome.html) and populates these values in the user's boto config.


#### Installation:

1. Clone this repo
2. `python setup.py install`
 


#### Requirements:

boto profiles were introduced in v2.24.0. This has been tested on versions >=2.35.2.

1. You must provide your AWS account number via the environment variable ``AWS_ACT_NUM``
2. The script assumes the identifying value of your MFA device is the same as your shell's ``USER`` variable. To override this, set the environment variable ``MFA_USER`` with your MFA device id.

**e.g.** ``arn:aws:iam::AWS_ACT_NUM:mfa/MFA_USER``


**botomfa** requires that you have a boto user configuration file with the following sections:

```
[long-term]
aws_access_key_id = YOUR_LONGTERM_KEY_ID
aws_secret_access_key = YOUR_LONGTERM_ACCESS_KEY

[Credentials]
aws_access_key_id = <POPULATED_BY_SCRIPT>
aws_secret_access_key = <POPULATED_BY_SCRIPT>
aws_security_token = <POPULATED_BY_SCRIPT>

```

The section ``[long-term]`` houses your long-term IAM User Access Keys
that do not change. These are referecned when creating temporary credentials.
This script manages, validates, and updates temporary credentials which are stored in the ``[Credentials]`` section. This section may look familar to you as the **defaut/fallback** section that boto references when authenticating to AWS services. This is intentional so that you are not requred to update any of your existing boto scripts!


It's probably a good idea to put ``AWS_ACT_NUM`` in your shell startup/source scripts.

### Usage Example


After installing and before utilizing boto, run ``botomfa [--duration n]`` to verify/update your temporary AWS credentials. 

``duration`` specifies, in seconds, the length of time in which your temporary credentials remain valid. The default value is 900 seconds, a dictated minimum by AWS.

**botomfa** is ran *before* running any of your scripts that use the boto library.

Below you will see that the temporary credentails in the ``[Credentials]`` section have expired and are no longer valid. So, you are prompted for your current MFA code in order to update these values:

```
person@host> botomfa
Validating current temporary credentials..
Current temporary creds failed.
Enter AWS MFA code for user person:123456
Validating current temporary credentials..
Current temporary credentials success!
```

Running **botomfa** again shows that your credentials are valid. You are now free to use boto uninterupted for the duration of your temporary credentials.

```
person@host> botomfa
Validating Current Temporary Credentials
Current temporary credentials success!
```

If you require temporary credentials longer than 900 seconds, try a larger duration value: ``botomfa --duration 3600``
