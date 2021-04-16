# DarkShield Files API Benchmarks: S3 Buckets

This benchmark tests the speed of processing files from  demonstrates the use of the 
*darkshield-files* API to search and mask files located on an S3 bucket. To run, 
the *plankton* web services API must be hosted on *http://localhost:8080* and must have 
the *darkshield* and *darkshield-files* plugins installed.

This benchmark uses asyncio dependencies, so a separate virtual environment is required to
avoid dependency clashes. To install the dependencies, execute 
*pip install -r requirements.txt* (make sure your virtual environment is activated, 
or your dependencies will be installed globally).

The program will take in a bucket name or an s3 url (starting with 's3://') and 
iterate over all objects found there, sending each file to the API. The s3 url can 
contain a prefix, which means only files under a certain prefix will be searched 
and masked. A single file can also be specified using its s3 url.

The original and masked files are never loaded fully into memory or stored in
temporary files on the client. Instead, they are streamed in chunks directly
between the S3 bucket and the API.

The masked files will be placed under the *darkshield-masked* key in the root of 
the bucket.

The *results.json* for each masked file will be placed inside of the 
*darkshield-results* key in the root of the bucket. The name of each file will 
be *{filename}-results.json*. Use the *--no-results* flag to disable results.json
generation.

To execute, run *python main.py bucket_name_or_url*. The script will use the *default*
profile in your AWS credentials file in order to access the bucket unless the
*--profile* flag is included. See the [boto3 quickstart guide](https://boto3.amazonaws.com/v1/documentation/api/latest/guide/quickstart.html#configuration)
for more information on how to configure this file.
