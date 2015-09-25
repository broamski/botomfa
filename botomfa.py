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


def get_sts(duration, mfa_serial, mfa_device_name,
            long_term, short_term, assume_role_arn=None):
    if boto.config.get(long_term, 'aws_access_key_id') is None:
        logger.error('aws_access_key_id is missing from section %s'
                     'or config file is missing.' % (long_term,))
        sys.exit(1)
    else:
        long_term_id = boto.config.get(long_term, 'aws_access_key_id')

    if boto.config.get(long_term, 'aws_secret_access_key') is None:
        logger.error('aws_secret_access_key is missing from section '
                     'or config file is missing.' % (long_term,))
        sys.exit(1)
    else:
        long_term_secret = boto.config.get(long_term, 'aws_secret_access_key')

    if boto.config.has_section(short_term):
        boto.config.remove_option(short_term, 'aws_security_token')

    mfa_TOTP = raw_input('Enter AWS MFA code for user %s '
                         '(renewing for %s seconds):' %
                         (mfa_device_name, duration))
    try:
        sts_connection = STSConnection(aws_access_key_id=long_term_id,
                                       aws_secret_access_key=long_term_secret)
        if assume_role_arn is None:
            tempCredentials = sts_connection.get_session_token(
                duration=duration,
                mfa_serial_number=mfa_serial,
                mfa_token=mfa_TOTP)
        else:
            role_session_name = assume_role_arn.split('/')[-1]
            assumedRole = sts_connection.assume_role(
                assume_role_arn, role_session_name,
                duration_seconds=duration,
                mfa_serial_number=mfa_serial,
                mfa_token=mfa_TOTP)
            tempCredentials = assumedRole.credentials

        boto.config.save_user_option(
            short_term,
            'aws_access_key_id',
            tempCredentials.access_key)
        boto.config.save_user_option(
            short_term,
            'aws_secret_access_key',
            tempCredentials.secret_key)
        boto.config.save_user_option(
            short_term,
            'aws_security_token',
            tempCredentials.session_token)
        boto.config.save_user_option(
            short_term,
            'expiration',
            tempCredentials.expiration)
        if assume_role_arn:
            boto.config.save_user_option(
                short_term,
                'assumed_arn',
                assume_role_arn)

    except boto.exception.BotoServerError as e:
        message = '%s - Please try again.' % (e.message)
        logger.error(message)
        sys.exit(1)


def test_creds(profile_name):
    try:
        logger.info('Validating temporary credentials..')
        expiration_string = boto.config.get(profile_name, 'expiration')
        if expiration_string is None:
            logger.error('Expiration timestamp missing from temporary '
                         'credentials.')
            return False
        exp_dt = datetime.datetime.strptime(
            expiration_string, '%Y-%m-%dT%H:%M:%SZ'
        )
        t_diff = exp_dt - datetime.datetime.utcnow()
        if t_diff.total_seconds() <= 0:
            logger.warn('Your temporary credentials have expired. '
                        'Attempting to renew...')
            return False

        # Validate against a real service. This may not be the best solution
        # for everyone, as the person attempting to fetch an STS token may
        # now have access to S3. This might need to be more flexible or we
        # could potentially ditch this altogether?
        s3 = boto.connect_s3()
        s3.get_all_buckets()

        logger.info(
            'Temporary credentials validation successful! '
            'Token expires in %s seconds at %s' %
            (t_diff.seconds, expiration_string)
        )
        return True
    except:
        logger.error('Temporary credentials failed.')
        return False


def run(duration, aws_account_num, mfa_device_name, profile,
        assume_role_arn=None):
    # If no profile specified, use default
    if profile is None:
        logger.debug('Using default profile.')
        long_term_profile = 'long-term'
        short_term_profile = 'Credentials'
    else:
        logger.debug('Using profile: %s' % profile)
        long_term_profile = '%s-%s' % (profile, 'long-term')
        short_term_profile = profile

    # Get AWS account number. Needed to build MFA serial
    if aws_account_num is None:
        logger.error('AWS Account number must be set either via '
                     'AWS_ACT_NUM environment variable '
                     'or --aws-acct-num.')
        sys.exit(1)

    # If your MFA device is named something other than your
    # shell's username, it can be provided via MFA_USER
    mfa_device_name = (mfa_device_name or
                       os.environ.get('USER'))
    if mfa_device_name is None:
        logger.error('Could retrieve MFA device name from environment '
                     'variables MFA_DEVICE_NAME or USER.')
        sys.exit(1)

    mfa_serial = 'arn:aws:iam::%s:mfa/%s' % (aws_account_num, mfa_device_name)

    logger.debug('Your AWS account number is: %s' % aws_account_num)
    logger.debug('Your MFA device name is: %s' % mfa_device_name)
    if assume_role_arn:
        logger.debug('You are assuming the role: %s' % assume_role_arn)

    # if any of the section named fields are missing, prompt for token
    if (
        boto.config.get(short_term_profile, 'aws_access_key_id') is None or
        boto.config.get(short_term_profile, 'aws_secret_access_key') is None or
        boto.config.get(short_term_profile, 'aws_security_token') is None
    ):
        logger.info(
            'Temporary credentials are missing, obtaining them.')
        get_sts(duration, mfa_serial,
                mfa_device_name, long_term_profile,
                short_term_profile, assume_role_arn)

    if not test_creds(short_term_profile):
        get_sts(duration, mfa_serial,
                mfa_device_name, long_term_profile,
                short_term_profile, assume_role_arn)
        test_creds(short_term_profile)


def reset_credentials(profile=None):
    short_term_profile = 'Credentials'
    if profile is not None:
        short_term_profile = profile

    if boto.config.has_section(short_term_profile):
        options = ['aws_access_key_id', 'aws_secret_access_key',
                   'aws_security_token', 'expiration', 'assumed_role']
        for option in options:
            boto.config.save_user_option(short_term_profile, option, '')
