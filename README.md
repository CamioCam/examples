Camio Examples Repository
===================

This respository contains example code and documentation on how to interact with the various Camio APIs.

The batch_import folder contains examples of code and documentation to upload pre-existing video files into the Camio pipeline. These files will be segmented in smaller videos, and labeled for search. The labels and sample images extracted from the segmented files will be uploaded into the Camio cloud in the form of events.

The hooks folder contains examples of code and documentation to register a user provided service for post processing of events, for example a custom labaler for images.