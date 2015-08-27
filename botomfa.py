import datetime
import logging
import os
import sys

import boto
import boto.s3
import boto.exception

from boto.sts import STSConnection

logger = logging.getLogger('botomfa')
stdout_handler = logging.StreamHandler(stream=sys.stdout)
stdout_handler.setFormatter(
    logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
stdout_handler.setLevel(logging.DEBUG)
logger.addHandler(stdout_handler)
logger.setLevel(logging.DEBUG)

# Get AWS account number. Needed to build MFA serial
aws_account_num = os.environ.get('AWS_ACT_NUM')
if aws_account_num is None:
    logger.error('Environment variable AWS_ACT_NUM is required.')
    sys.exit(1)

# If your MFA device is named something other than your
# shell's username, it can be provided via MFA_USER
mfa_device_name = os.environ.get('MFA_DEVICE_NAME') or os.environ.get('USER')
if mfa_device_name is None:
    logger.error('Could retrieve MFA device name from environment '
                 'variables MFA_DEVICE_NAME or USER.')
    sys.exit(1)

mfa_serial = 'arn:aws:iam::%s:mfa/%s' % (aws_account_num, mfa_device_name)


def get_sts(duration):
    if boto.config.get('long-term', 'aws_access_key_id') is None:
        logger.error('aws_access_key_id is missing from section long-term '
                     'or config file is missing.')
        sys.exit(1)
    else:
        long_term_id = boto.config.get('long-term', 'aws_access_key_id')

    if boto.config.get('long-term', 'aws_secret_access_key') is None:
        logger.error('aws_secret_access_key is missing from section long-term '
                     'or config file is missing.')
        sys.exit(1)
    else:
        long_term_secret = boto.config.get('long-term', 'aws_secret_access_key')

    os.environ['AWS_ACCESS_KEY_ID'] = long_term_id
    os.environ['AWS_SECRET_ACCESS_KEY'] = long_term_secret

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
            mfa_token=mfa_TOTP)
        boto.config.save_user_option(
            'Credentials',
            'aws_access_key_id',
            tempCredentials.access_key)
        boto.config.save_user_option(
            'Credentials',
            'aws_secret_access_key',
            tempCredentials.secret_key)
        boto.config.save_user_option(
            'Credentials',
            'aws_security_token',
            tempCredentials.session_token)
        boto.config.save_user_option(
            'Credentials',
            'expiration',
            tempCredentials.expiration)
    except boto.exception.BotoServerError as e:
        message = '%s - Please try again.' % (e.message)
        logger.error(message)
        sys.exit(1)


def test_creds():
    os.environ['AWS_ACCESS_KEY_ID'] = boto.config.get(
        'Credentials', 'aws_access_key_id')
    os.environ['AWS_SECRET_ACCESS_KEY'] = boto.config.get(
        'Credentials', 'aws_secret_access_key')
    os.environ['AWS_SECURITY_TOKEN'] = boto.config.get(
        'Credentials', 'aws_security_token')

    try:
        logger.info('Validating temporary credentials..')
        s3 = boto.connect_s3()
        s3.get_all_buckets()
        expiration_string = boto.config.get('Credentials', 'expiration')
        exp_dt = datetime.datetime.strptime(
            expiration_string, '%Y-%m-%dT%H:%M:%SZ'
        )
        t_diff = exp_dt - datetime.datetime.utcnow()
        logger.info(
            'Temporary credentials validation successful! '
            'Token expires in %s seconds at %s' %
            (t_diff.seconds, expiration_string)
        )
        return True
    except:
        logger.error('Temporary credentials failed.')
        return False


def run(duration):
    # if any of the section named fields are missing, prompt for token
    if (
        boto.config.get_value('Credentials', 'aws_access_key_id') is None or
        boto.config.get('Credentials', 'aws_secret_access_key') is None or
        boto.config.get('Credentials', 'aws_security_token') is None
    ):
        logger.info(
            'Temporary credentials are missing, obtaining them.')
        get_sts(duration)

    if not test_creds():
        get_sts(duration)
        test_creds()
