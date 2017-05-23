Camio Examples
==============

This repo contains example code and documentation explaining how to use the Camio APIs and services.

The [batch_import](batch_import) folder explains the bulk import of pre-existing video files that need to be
segmented into smaller video events and labeled for search.

The [hooks](hooks) folder explains how to add custom post-processing services, such as image labelers or notifications, 
to video events as they arrive.

### Overview of video importing

![Import Video Overview](https://storage.googleapis.com/camio_general/import-video-overview-camio.png)

0. Run `import_video.py` from any laptop/computer.
1. Specify the input directory of H.264 video files.
2. [Camio Box](https://camio.com/box) analyzes the video files, segments into events, and submits for labeling.
3. [camio.com](https://camio.com) ranks interest, queues labeling services, and indexes results.
4. Labeling services analyze images from video events and post additional labels.
5. Run `download_labels.py` to export the desired labels.
6. Exported labels are organized by timestamp and camera for easy import as bookmarks.
7. Observers jump to bookmarked video events for faster review.

