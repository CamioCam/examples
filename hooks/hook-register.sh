#!/usr/bin/env bash


usage="bash $0 callback_url parsed_query"

if [ "$#" -lt 2 ]; then
  echo "Usage: $usage"
  exit 1
fi

auth_token="$CAMIO_OAUTH_TOKEN"
callback_url="$1"
query="$2"

curl -H "Content-Type: application/json" \
    -H "Authorization: token $auth_token" \
    -d '{"callback_url": "'"$callback_url"'", "type": "query_match", "parsed_query": "'"$query"'"}' \
    https://camio.com/api/users/me/hooks
