
# botomfa: boto + multi-factor authentication (MFA) enabled accounts


**botomfa** makes it easy to use boto, the AWS SDK for Python, with AWS IAM user accounts that have multi-factor authentication (MFA) enabled.

The concept behind **botomfa** is that there are 2 types of credentials:

* `long-term` - Your typcial AWS access keys, consisting of an ID and a SECRET

* `temporary` - A temporary set of credentials that are generated from a combination for your long-term credentials and your MFA token using the [AWS Security Token Service](http://docs.aws.amazon.com/STS/latest/APIReference/Welcome.html).

**botomfa** utilizes your `long-term` IAM User Access Keys to obtain temporary ``AWS_ACCESS_KEY_ID``, ``AWS_SECRET_ACCESS_KEY``, and ``AWS_SECURITY_TOKEN``  values from [AWS Security Token Service](http://docs.aws.amazon.com/STS/latest/APIReference/Welcome.html) and populates these values in the user's boto config.

*Note*: The credentials test is performed by making a basic connection to s3 a la ``get_all_buckets()``.


#### Installation:

1. Clone this repo
2. `python setup.py install`
 


#### Requirements:

boto profiles were introduced in v2.24.0. This has been tested on versions >=2.35.2.


**botomfa** requires that you have a .boto [boto user configuration file](http://boto.readthedocs.org/en/latest/boto_config_tut.html) in your home directory with the following sections:

```
[long-term]
aws_access_key_id = YOUR_LONGTERM_KEY_ID
aws_secret_access_key = YOUR_LONGTERM_ACCESS_KEY

```

The section ``[long-term]`` houses your long-term IAM User Access Keys
that do not change. These are referecned when creating temporary credentials.
This script manages, validates, and updates temporary credentials which are stored in the ``[Credentials]`` section. This section may look familar to you as the **defaut/fallback** section that boto references when authenticating to AWS services. This is intentional so that you are not requred to update any of your existing boto scripts!

After running `botomfa`, you will notice that the `[Credentials]` section has been populated:

```
[long-term]
aws_access_key_id = YOUR_LONGTERM_KEY_ID
aws_secret_access_key = YOUR_LONGTERM_ACCESS_KEY

[Credentials]
aws_access_key_id = <POPULATED_BY_SCRIPT>
aws_secret_access_key = <POPULATED_BY_SCRIPT>
aws_security_token = <POPULATED_BY_SCRIPT>
```

##### Aruguments / Inputs

Argument precedence: Command line arguments take precedence over environment variables. 

* **Required:** Environment variable `AWS_ACT_NUM` or command argument `--aws-act-num` - Your AWS account number. 
* Enviroment variable `MFA_DEVICE_NAME` or command argument `--mfa-device-name` -  The script assumes the identifying value of your MFA device is the same as your shell's ``USER`` variable. This option overrides that value.
* Environment varialbe `STS_DURATION` or command argument `--duration` - The default is 900 seconds, a dictated minimum by AWS.


###### Profiles
In the event that you utilize multiple AWS keypairs via profiles, we've got you covered. Just specify `--profile <profile_name>` when running `botomfa`.

### Usage Example

Run **botomfa** *before* running any of your scripts that use the boto library and need valid AWS credentials. 

##### First Run
```
$> botomfa
2015-08-27 13:45:57,334 - botomfa - DEBUG - Your AWS account number is: 123456789012
2015-08-27 13:45:57,334 - botomfa - DEBUG - Your MFA device name is: brian
2015-08-27 13:45:57,334 - botomfa - INFO - Temporary credentials are missing, obtaining them.
Enter AWS MFA code for user brian (renewing for 900 seconds):666666
2015-08-27 13:46:06,172 - botomfa - INFO - Validating temporary credentials..
2015-08-27 13:46:06,835 - botomfa - INFO - Temporary credentials validation successful! Token expires in 899 seconds at 2015-08-27T18:01:06Z
```

Running **botomfa** again shows that your credentials are valid. You are now free to use boto uninterupted for the duration of your temporary credentials.

```
$> botomfa
2015-08-27 13:48:03,294 - botomfa - DEBUG - Your AWS account number is: 123456789012
2015-08-27 13:48:03,295 - botomfa - DEBUG - Your MFA device name is: brian
2015-08-27 13:48:03,295 - botomfa - INFO - Validating temporary credentials..
2015-08-27 13:48:03,750 - botomfa - INFO - Temporary credentials validation successful! Token expires in 782 seconds at 2015-08-27T18:01:06Z
```

