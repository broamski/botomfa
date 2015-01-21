"""
This assumes that you have already sourced your IAM
creds before running this script. If MFA is successful,
new, temporary credentials are populated in the environment
varialbes:
AWS_ACCESS_KEY_ID
AWS_SECRET_ACCESS_KEY
AWS_SECURITY_TOKEN
"""
import os
import sys

from boto.sts import STSConnection


# Gather AWS account number
aws_account_num = os.environ.get('AWS_ACT_NUM')
if aws_account_num is None:
    sys.exit('Environment variable AWS_ACT_NUM is required!')

# Gather username. If your MFA token is named other than your
# shell's username, it can be provided via MFA_USER
mfa_user = os.environ.get('MFA_USER') or os.environ.get('USER')
if mfa_user is None:
    sys.exit('Could not find MFA_USER or your username!')

# Prompt for MFA time-based one-time password (TOTP)
mfa_TOTP = raw_input("Enter your AWS MFA code: ")

sts_connection = STSConnection()

mfa_serial = 'arn:aws:iam::%s:mfa/%s' % (aws_account_num, mfa_user)

tempCredentials = sts_connection.get_session_token(
    duration=900,
    mfa_serial_number=mfa_serial,
    mfa_token=mfa_TOTP
)

os.environ['AWS_ACCESS_KEY_ID'] = tempCredentials.access_key
os.environ['AWS_SECRET_ACCESS_KEY'] = tempCredentials.secret_key
os.environ['AWS_SECURITY_TOKEN'] = tempCredentials.session_token
