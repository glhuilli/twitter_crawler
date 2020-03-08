# twitter_crawler

Get all Friends and Followers from a list of Twitter screen names.

To use this script you should first setup a Virtual Environment, and run

```bash
pip install -r requirements.txt
```

Then you can run the code below to start crawling all input screen name followers using the following, 

```bash
python src/get_twitter_ffs.py --client_key=$TWITTER_CLIENT_KEY --client_secret=$TWITTER_CLIENT_SECRET --ids_type=followers --screen_names_path=./data/screen_names_test.json --log=./crawler_followers_log.txt
```


and then all the input screen names friends using the following,


```bash
python src/get_twitter_ffs.py --client_key=$TWITTER_CLIENT_KEY --client_secret=$TWITTER_CLIENT_SECRET --ids_type=friends --screen_names_path=./data/screen_names_test.json --log=./crawler_friends_log.txt
```


And the execution logs will be stored in `crawler_log.txt` (default) unless a different file is defined.


Any entry on the `jsons` file will look like the following, where given an input screen name, all the friends (or followers) Twitter ID will be listed. 

```
{
    "glhuilli": [
        1057652599439147009, 
        71596667, 
        14066472, 
        374670487,
        ...
    ]
}
```

Once you get the User Ids, you can fetch the actual user information by using the `get_twitter_users.py` script using the following,   


```bash
python src/get_twitter_users.py --client_key=$TWITTER_CLIENT_KEY --client_secret=$TWITTER_CLIENT_SECRET --ids_files=followers_2020-03-07.jsons,friends_2020-03-07.jsons --log=./crawler_users_log.txt
```

That will store the `user_id` to the user object defined by Twitter API (more info [here](https://developer.twitter.com/en/docs/accounts-and-users/follow-search-get-users/api-reference/get-users-show)). 


Both scripts were formatted using `mypy`, `yapf`, `isort`, and `pylint`.

Note that there are strict constraints on the amount of API calls that can be made to the Twitter API, please review your specific Tokens constraints and modify the script accordingly.  
