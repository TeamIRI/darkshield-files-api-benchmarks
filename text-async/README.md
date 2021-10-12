# DarkShield Files API Benchmarks: Asynchronous Programming Approach

This benchmark utilizes aynchronous programming through Python modules *asyncio* and *aiohttp* to maximize the speed in processing files.
The DarkShield API can handle multiple requests at once, meaning that utilizing a synchronous programming approach will result in reduced overall speed when processing the same 
number of files with the exact same data. This is because, with a synchronous approach, the program must wait for a response from the DarkShield API before doing anything else.
Since the DarkShield API can handle multiple requests at once (the sweet spot is typically between 4-8 requests at a time depending on hardware specs before performance improvements level off),
a synchronous approach is missing out on the maximum performance potential a program could achieve when interacting with the DarkShield API.

This benchmark takes the following arguments:

lines - the number of lines that should be in each text file. Each line is 1 KB in size.
number of files (-n) - the number of files that should be generated and asynchronously sent to the DarkShield API. The default is 10.
buffer limit (-b) Buffer limit configuration parameter sent to the DarkShield API to utilize when processing the text files. This limits memory use by the DarkShield API.
workers (-w) The number of workers to use to process the files. The default is 4.

The start time and end time of the operation will be recorded.
To calculate the difference between the synchronous text benchmarks and this asynchronous text benchmark:
1. Find the difference between the end time and the start time recorded in the async benchmark. This will be
the total time taken for how many files were specified (the default is 10).
2. Divide this time by the number of files specified.
3. Calculate the percent difference between this time and the *mean time* recorded in the synchronous benchmark.

Based on 100000 lines and 4 workers, the asynchronous approach benchmark is roughly 50 percent faster than the synchronous benchmark.
Exact differences may vary depending on machine specs and other factors not being controlled.
