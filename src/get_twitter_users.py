import argparse
import base64
import datetime
import json
import logging
import time
from typing import Any, Dict, List, Set

import requests

# The rate limit is 1 user profile per second, so adding a wait time
# to make sure we don't exceed this.
# https://developer.twitter.com/en/docs/accounts-and-users/follow-search-get-users/api-reference/get-users-show
_WAIT_TIME = 1  # seconds
_BASE_URL = 'https://api.twitter.com/'


def get_logger(log_file: str) -> logging.Logger:
    """
    This logger prints both in screen and into a log file at the same time
    """
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)

    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')

    file_handler = logging.FileHandler(log_file)
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.DEBUG)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    return logger


def get_authorization_token(client_key, client_secret) -> str:
    key_secret = '{}:{}'.format(client_key, client_secret).encode('ascii')
    b64_encoded_key = base64.b64encode(key_secret)
    b64_encoded_key = b64_encoded_key.decode('ascii')  # type: ignore

    auth_url = '{}oauth2/token'.format(_BASE_URL)
    auth_headers = {
        'Authorization': 'Basic {}'.format(b64_encoded_key),  # type: ignore
        'Content-Type': 'application/x-www-form-urlencoded;charset=UTF-8'
    }
    auth_data = {'grant_type': 'client_credentials'}
    auth_resp = requests.post(auth_url, headers=auth_headers, data=auth_data)

    return auth_resp.json()['access_token']


def get_twitter_data(access_token: str, twitter_id: str) -> Dict[Any, Any]:
    search_url = '{}1.1/{}/show.json'.format(_BASE_URL, 'users')
    search_headers = {'Authorization': 'Bearer {}'.format(access_token)}
    search_params = {'user_id': twitter_id}
    res = requests.get(search_url,
                       headers=search_headers,
                       params=search_params)
    return res.json()


def get_user_ids(ids_file_paths: List[str]) -> Set[str]:
    user_ids = set()
    for ids_file_path in ids_file_paths:
        with open(ids_file_path, 'r') as file:
            for line in file.readlines():
                screen_name_user_ids = json.loads(line)
                for _, ids in screen_name_user_ids.items():
                    user_ids.update(set(ids))
    return user_ids


def download_data(user_ids: Set[str], access_token: str,
                  logger: logging.Logger) -> None:
    now = datetime.datetime.now().date().isoformat()
    with open('{}_{}.jsons'.format('twitter_users', now), 'w') as output:
        for twitter_user_id in user_ids:
            logger.info(f'fetching data for {twitter_user_id}')
            time.sleep(_WAIT_TIME)
            user_data = get_twitter_data(access_token, twitter_user_id)
            output.write('{}\n'.format(json.dumps({twitter_user_id:
                                                   user_data})))


def parse_args():
    parser = argparse.ArgumentParser(
        description="Get friends and followers for set of Twitter screen_names"
    )
    parser.add_argument('--client_key',
                        help='Twitter client key',
                        required=True)
    parser.add_argument('--client_secret',
                        help='Twitter client secret',
                        required=True)
    parser.add_argument(
        '--ids_files',
        help=
        'Files with Twitter Ids to fetch users information (separated by comma)',
        required=True)
    parser.add_argument('--log', default='./crawler_log.txt', help='Log file')
    return parser.parse_args()


def main(args):
    logger = get_logger(args.log)
    access_token = get_authorization_token(args.client_key, args.client_secret)
    user_ids = get_user_ids(args.ids_files.split(','))
    logger.info(
        f'Crawling {len(user_ids)} User profiles from {args.ids_files}')
    download_data(user_ids, access_token, logger)


if __name__ == "__main__":
    main(parse_args())
