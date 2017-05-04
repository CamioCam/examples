#!/usr/bin/env bash


usage="bash $0 auth_token callback_url query"

if [ "$#" -lt 3 ]; then
  echo "Usage: $usage"
  exit 1
fi

auth_token="$1"
callback_url="$2"
query="$3"

curl -v \
    -H "Content-Type: application/json" \
    -H "Authorization: token $auth_token" \
    -d '{"callback_url": "'"$callback_url"'", "type": "query_match", "parsed_query": "'"$query"'"}' \
    -X POST https://camio.com/api/users/me/hooks
