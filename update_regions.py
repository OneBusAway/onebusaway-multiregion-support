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
import csv
import os
import io
import sys
import urllib.request, urllib.error, urllib.parse
from src.serializers import JSONSerializer, XMLSerializer, serialize

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


# In both reading cases, we need to read all data into memory
# because there's no way of seeking back in a CSV reader.

def get_csv_from_file(path):
    with open(path) as f:
        reader = csv.DictReader(open(path))
        return list(reader)


def get_csv_from_url(url):
    "Returns a list of regions from the specified spreadsheet URL."
    opener = urllib.request.build_opener(
        urllib.request.HTTPCookieProcessor(),
        urllib.request.HTTPRedirectHandler()
    )
    urllib.request.install_opener(opener)
    response = urllib.request.urlopen(url)
    reader = csv.DictReader(io.TextIOWrapper(response, encoding='utf-8'))
    return list(reader)


def output_stdout(_fmt, output, _opts):
    print(output)


def output_file(fmt, output, opts, version):
    if version == 2:
        file_name = 'regions.'
    else:
        file_name = 'regions-v' + str(version) + '.'
    path = os.path.join(opts.output_dir, file_name + fmt)
    print('Writing %s' % path)
    with open(path, 'w+') as f:
        f.write(output)


def output_s3(fmt, output, opts, version):
    try:
        from boto.s3.connection import S3Connection
        from boto.s3.key import Key
    except ImportError:
        print("Unable to publish to S3: Boto not installed.", file=sys.stderr)
        return

    # Verify the S3 configuration
    bucket_name = opts.output_s3
    access_key = opts.aws_access_key or os.environ.get('AWS_ACCESS_KEY_ID')
    secret_key = opts.aws_secret_key or os.environ.get('AWS_SECRET_ACCESS_KEY')

    if not access_key or not secret_key:
        print("We need an AWS access key and AWS secret key", file=sys.stderr)
        return

    conn = S3Connection(access_key, secret_key)
    bucket = conn.get_bucket(bucket_name)
    k = Key(bucket)
    if version == 2:
        file_name = 'regions.'
    else:
        file_name = 'regions-v' + version + '.'

    k.key = file_name + fmt

    # Set a content type
    content_types = {
        'json': 'application/json',
        'xml': 'text/xml'
    }
    if fmt in content_types:
        k.set_metadata('Content-Type', content_types[fmt])

    print('Writing %s/%s' % (bucket_name, k.key))
    k.set_contents_from_string(output)


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
