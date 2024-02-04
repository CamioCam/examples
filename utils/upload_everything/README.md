# upload_everything.py

## Overview

When you use the `event_auto_upload_query_filter` option to upload only the video Events that have 
interesting motion, you may sometimes  need to retrieve all video Events (even when there was no motion at all).

This utility sends API requests using `all tag:box` in the query to force the upload of everything recorded.

## Instructions

Excecute with:
```
python upload_everything.py --cameras_filename your_cameras_filename.csv --time_range_filename your_time_range_filename.csv --token your_access_token
```

See help with:
```
python upload_everything.py --help
```

`cameras_filename` is a csv with a header row and three required columns like this,
where the rows without `is_requested` value `TRUE` are skipped:

```csv
user_email,camera,is_requested
hqcams@acme.com,Front Entrance,TRUE
hqcams@acme.com,Back Exit,TRUE
```

`time_range_filename` is a csv with a header row and two required columns like this,
where each time range should span less than 800 Events (for reference, the max number
of Events/hour/camera is typically 180):

```
start_time,end_time
7pm PT January 31,7:30pm PT January 31st
7:30pm PT January 31,8:00pm PT January 31st
```

You can obtain `your_access_token` from:
[https://camio.com/settings/integrations/#api](https://camio.com/settings/integrations/#api)

The stdout is a CSV with four columns like this example, where the `search_url` can be used to view the results the requested
uploads are completed:

```
python upload_everything.py --cameras_filename cameras.csv --time_range_filename time-ranges.csv --token YOURTOKEN | tee output.csv

api_request_url,status,upload_commands_count,uploading_devices,search_url
https://camio.com/api/search?text=sanmateo%40camiolog.com+Front+East+7pm+PT+January+31st+to+8pm+PT+January+31st+all+tag%3Abox,200,2,gd:00vx12273wf6fvd:000C29EF1F22 gd:00vx12273wf6fvd:B0416F040AF6,https://camio.com/app/#search;q=sanmateo%40camiolog.com+Front+East+7pm+PT+January+31st+to+8pm+PT+January+31st+all
https://camio.com/api/search?text=sanmateo%40camiolog.com+Front+East+8pm+PT+January+31st+to+9pm+PT+January+31st+all+tag%3Abox,200,2,gd:00vx12273wf6fvd:000C29EF1F22 gd:00vx12273wf6fvd:B0416F040AF6,https://camio.com/app/#search;q=sanmateo%40camiolog.com+Front+East+8pm+PT+January+31st+to+9pm+PT+January+31st+all
https://camio.com/api/search?text=sanmateo%40camiolog.com+Front+West+7pm+PT+January+31st+to+8pm+PT+January+31st+all+tag%3Abox,200,2,gd:00vx12273wf6fvd:000C29EF1F22 gd:00vx12273wf6fvd:B0416F040AF6,https://camio.com/app/#search;q=sanmateo%40camiolog.com+Front+West+7pm+PT+January+31st+to+8pm+PT+January+31st+all
https://camio.com/api/search?text=sanmateo%40camiolog.com+Front+West+8pm+PT+January+31st+to+9pm+PT+January+31st+all+tag%3Abox,200,2,gd:00vx12273wf6fvd:000C29EF1F22 gd:00vx12273wf6fvd:B0416F040AF6,https://camio.com/app/#search;q=sanmateo%40camiolog.com+Front+West+8pm+PT+January+31st+to+9pm+PT+January+31st+all
```

Only the tag:box upload request query text is shown when using the `--dry_run` argument like this:

```
python upload_everything.py --cameras_filename cameras.csv --time_range_filename time-ranges.csv --token YOURTOKEN --dry_run
api_request_url,status,upload_commands_count,uploading_devices,search_url
sanmateo@camiolog.com Front East 7pm PT January 31st to 8pm PT January 31st all tag:box,N/A,0,N/A
sanmateo@camiolog.com Front East 8pm PT January 31st to 9pm PT January 31st all tag:box,N/A,0,N/A
sanmateo@camiolog.com Front West 7pm PT January 31st to 8pm PT January 31st all tag:box,N/A,0,N/A
sanmateo@camiolog.com Front West 8pm PT January 31st to 9pm PT January 31st all tag:box,N/A,0,N/A
```
