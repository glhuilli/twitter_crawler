import argparse
import base64
import csv
import datetime
import json
import logging
import time
from typing import Iterable, List

import requests

_WAIT_TIME = 60  # seconds (we can make 15 API requests every 15 minutes -- so 1 per minute)
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


def get_screen_names(screen_names_path: str) -> List[str]:
    with open(screen_names_path, 'r') as file:
        return json.load(file).get('screen_names')


def get_authorization_token(client_key: str, client_secret: str) -> str:
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


def get_ids(screen_name: str,
            access_token: str,
            ids_type: str,
            logger: logging.Logger,
            batch_size: int = 5000) -> Iterable[int]:
    cursor = -1
    search_url = '{}1.1/{}/ids.json'.format(_BASE_URL, ids_type)
    search_headers = {'Authorization': 'Bearer {}'.format(access_token)}
    while cursor:
        if cursor != -1:
            logger.info('waiting 60s -- cursor {}'.format(cursor))
            time.sleep(_WAIT_TIME)
        search_params = {
            'screen_name': screen_name,
            'count': batch_size,
        }
        if cursor != -1:
            search_params['cursor'] = cursor

        res = requests.get(search_url,
                           headers=search_headers,
                           params=search_params)  # type: ignore
        data = res.json()
        cursor = data.get('next_cursor')
        yield from data.get('ids', [])


def download_data(screen_names: List[str],
                  access_token: str,
                  ids_type: str,
                  logger: logging.Logger,
                  already_processed_path: str = None) -> None:
    already_processed_screen_names = set()
    if already_processed_path:
        with open(already_processed_path, 'r') as file:
            for row in csv.reader(file):
                already_processed_screen_names.add(row[0])
    now = datetime.datetime.now().date().isoformat()
    with open('{}_{}.jsons'.format(ids_type, now), 'w') as output:
        for idx, screen_name in enumerate(screen_names):
            if already_processed_screen_names and screen_name in already_processed_screen_names:
                logger.info('already processed: {}'.format(screen_name))
                continue
            if idx != 0:
                logger.info('waiting 60s -- next screen_name')
                time.sleep(_WAIT_TIME)
            logger.info('processing {}'.format(screen_name))
            ids = list(get_ids(screen_name, access_token, ids_type, logger))
            output.write('{}\n'.format(json.dumps({screen_name: ids})))


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
    parser.add_argument('--ids_type',
                        help='Type of ids to download (friends or followers)',
                        required=True)
    parser.add_argument(
        '--screen_names_path',
        help='path to file with the screen_names to download (json format)',
        required=True)
    parser.add_argument('--already_processed',
                        help='List of screen_names already processed',
                        required=False)
    parser.add_argument('--log', default='./crawler_log.txt', help='Log file')
    return parser.parse_args()


def main(args):
    logger = get_logger(args.log)

    access_token = get_authorization_token(args.client_key, args.client_secret)
    screen_names = get_screen_names(args.screen_names_path)
    already_processed = args.already_processed
    logger.info(
        f'Crawling Friends and Followers from {args.screen_names_path}')
    if already_processed:
        download_data(screen_names,
                      access_token,
                      args.ids_type,
                      logger,
                      already_processed_path=already_processed)
    else:
        download_data(screen_names, access_token, args.ids_type, logger)


if __name__ == "__main__":
    main(parse_args())
