#!/usr/bin/env python

"""
Copyright (C) 2013 Paul Watts (paulcwatts@gmail.com)

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

      http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
 distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
"""

import argparse
import sys
from src.csv_readers import get_csv_from_file, get_csv_from_url
from src.serializers import JSONSerializer, XMLSerializer, serialize
from src.writers import output_file, output_s3, output_stdout

DESCRIPTION = """Generate and update OneBusAway regions list.

This script will translate the spreadsheet that specifies the
OneBusAway regions into JSON and XML files that can be served by
the regions server. It provides options to store the output
files locally, or in an AWS S3 bucket.
"""
parser = argparse.ArgumentParser(description=DESCRIPTION)
parser.add_argument('--input-url',
                    default="https://docs.google.com/spreadsheet/ccc?key=0AsoU647elPShdHlYc0RJbkEtZnVvTW11WE5NbHNiMXc&pli=1&gid=0&output=csv",
                    help='The source URL to process as input.')
parser.add_argument('--input-file',
                    help='The local CSV file to process as input.')
parser.add_argument('--output-dir',
                    default='.',
                    help="The directory to write the output files. Defaults to the current directory. You can use '-' for stdout.")
parser.add_argument('--output-formats',
                    default='json,xml',
                    help='The file types to write, separated by commas. Defaults to "json,xml".')
parser.add_argument('--output-s3',
                    metavar='S3_BUCKET',
                    help='Outputs to S3. Requires --aws-access-key --aws-secret-key options, or the AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY environment variables.')
parser.add_argument('--aws-access-key',
                    help='AWS Access key for publishing to S3.')
parser.add_argument('--aws-secret-key',
                    help='AWS Secret key for publishing to S3.')
parser.add_argument('--pretty',
                    action='store_true',
                    default=False,
                    help='Make the output files pretty and readable with indentation.')


def main():
    class Options(object):
        pass

    opts = Options()
    parser.parse_args(namespace=opts)

    # Maybe we should import print function from Python 3
    if opts.output_dir == '-':
        # Don't use stdout for log messages
        def log(s):
            pass
    else:
        def log(s):
            print(s)

    if opts.input_file:
        log('Reading %s' % opts.input_file)
        regions = get_csv_from_file(opts.input_file)
    else:
        log('Reading %s' % opts.input_url)
        regions = get_csv_from_url(opts.input_url)

    serializer_opts = {
        'pretty': opts.pretty
    }

    serializers = {
        'json': JSONSerializer,
        'xml': XMLSerializer
    }

    for fmt in opts.output_formats.split(','):
        cls = serializers.get(fmt)
        if cls:
            # Write v2 (initial) version of API first, without experimental regions
            version = 2
            output = serialize(regions, cls(**serializer_opts), version)
            if opts.output_dir == '-':
                output_stdout(fmt, output, opts)
            elif opts.output_s3:
                output_s3(fmt, output, opts, version)
            else:
                output_file(fmt, output, opts, version)

            # Write v3 version of API next (includes experimental regions)
            version = 3
            output = serialize(regions, cls(**serializer_opts), version)
            if opts.output_dir == '-':
                output_stdout(fmt, output, opts)
            elif opts.output_s3:
                output_s3(fmt, output, opts, version)
            else:
                output_file(fmt, output, opts, version)

        else:
            print('*** ERROR: Unknown format: "%s"' % fmt, file=sys.stderr)


if __name__ == '__main__':
    main()
