"""
Requires a boto user config with the following sections:
[long-term]
aws_access_key_id =
aws_secret_access_key =

and

[Credentials]
aws_access_key_id =
aws_secret_access_key =
aws_security_token =


The section [long-term] houses your long-term credentials
that do not change. These are referecned when creating temporary credentials.
This script manages, validates, and updates the default [Credentials] section,
so that you do not have to modify your existing boto scripts!

"""
import os
import sys

import boto
import boto.s3
import boto.exception

from boto.sts import STSConnection

# Get AWS account number. Needed to build MFA serial
aws_account_num = os.environ.get('AWS_ACT_NUM')
if aws_account_num is None:
    sys.exit('Environment variable AWS_ACT_NUM is required!')

# If your MFA device is named something other than your
# shell's username, it can be provided via MFA_USER
mfa_device_name = os.environ.get('MFA_DEVICE_NAME') or os.environ.get('USER')
if mfa_device_name is None:
    sys.exit('Could retrieve your username or MFA_USER!')

mfa_serial = 'arn:aws:iam::%s:mfa/%s' % (aws_account_num, mfa_device_name)


def get_sts(duration=900):
    os.environ['AWS_ACCESS_KEY_ID'] = boto.config.get(
        'long-term', 'aws_access_key_id')
    os.environ['AWS_SECRET_ACCESS_KEY'] = boto.config.get(
        'long-term', 'aws_secret_access_key')
    boto.config.remove_option('Credentials', 'aws_security_token')
    try:
        del os.environ['AWS_SECURITY_TOKEN']
    except:
        pass
    mfa_TOTP = raw_input("Enter AWS MFA code for user %s:" % mfa_device_name)
    try:
        sts_connection = STSConnection()
        tempCredentials = sts_connection.get_session_token(
            duration=duration,
            mfa_serial_number=mfa_serial,
            mfa_token=mfa_TOTP
        )
        boto.config.save_user_option(
            'Credentials', 'aws_access_key_id', tempCredentials.access_key
        )
        boto.config.save_user_option(
            'Credentials', 'aws_secret_access_key', tempCredentials.secret_key
        )
        boto.config.save_user_option(
            'Credentials', 'aws_security_token', tempCredentials.session_token
        )
    except boto.exception.BotoServerError as e:
        message = '%s - Please try again.' % (e.message)
        sys.exit(message)


def test_creds():
    os.environ['AWS_ACCESS_KEY_ID'] = boto.config.get(
        'Credentials', 'aws_access_key_id')
    os.environ['AWS_SECRET_ACCESS_KEY'] = boto.config.get(
        'Credentials', 'aws_secret_access_key')
    os.environ['AWS_SECURITY_TOKEN'] = boto.config.get(
        'Credentials', 'aws_security_token')

    try:
        print 'Validating current temporary cedentials..'
        s3 = boto.connect_s3()
        s3.get_all_buckets()
        print 'Current temporary credentials success!'
        return True
    except:
        print 'Current temporary creds failed.'
        return False


def run(duration):
    # if any of the section named fields are missing, prompt for token
    if (boto.config.get_value('Credentials', 'aws_access_key_id') is None or
        boto.config.get('Credentials', 'aws_secret_access_key') is None or
            boto.config.get('Credentials', 'aws_security_token') is None):
        print 'Temporary credentials are missing ' \
            'grabbing them again'
        get_sts(duration)

    if not test_creds():
        get_sts(duration)
        test_creds()
