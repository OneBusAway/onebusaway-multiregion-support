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
import json
import os
import sys
import urllib2
from xml.dom.minidom import getDOMImplementation


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
    opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(),
                                  urllib2.HTTPRedirectHandler())
    urllib2.install_opener(opener)
    response = urllib2.urlopen(url)
    reader = csv.DictReader(response)
    return list(reader)


class BaseSerializer(object):
    def __init__(self, **kwargs):
        self.pretty = kwargs.get('pretty')

    def _bounds(self, bounds_str):
        def _map_bound(bound):
            lat, lon, latSpan, lonSpan = bound.split(':')
            return {
                'lat': float(lat),
                'lon': float(lon),
                'latSpan': float(latSpan),
                'lonSpan': float(lonSpan)
            }

        if not bounds_str:
            return []

        bounds = bounds_str.split('|')
        return [_map_bound(b) for b in bounds]

    def region_id(self, bundle, value):
        bundle['id'] = int(value)

    def active(self, bundle, value):
        bundle['active'] = self._bool(value)

    def bounds(self, bundle, value):
        bundle['bounds'] = self._bounds(value)

    def supportsSiriRealtimeApis(self, bundle, value):
        bundle['supportsSiriRealtimeApis'] = self._bool(value)

    def supportsObaDiscoveryApis(self, bundle, value):
        bundle['supportsObaDiscoveryApis'] = self._bool(value)

    def supportsObaRealtimeApis(self, bundle, value):
        bundle['supportsObaRealtimeApis'] = self._bool(value)

    def experimental(self, bundle, value):
        bundle['experimental'] = self._bool(value)
	
    def alter_bundle(self, bundle):
        return bundle


class JSONSerializer(BaseSerializer):
    def __init__(self, **kwargs):
        super(JSONSerializer, self).__init__(**kwargs)

    def _bool(self, value):
        if value == 'TRUE':
            return True
        elif value == 'FALSE':
            return False
        else:
            raise ValueError("Invalid value for active")

    # The base URLs want to be serialized as null in JSON,
    # not the empty string.

    def obaBaseUrl(self, bundle, value):
        bundle['obaBaseUrl'] = value or None

    def siriBaseUrl(self, bundle, value):
        bundle['siriBaseUrl'] = value or None

    def alter_list_bundle(self, list_bundle):
        return {
            'version': 2,
            'code': 200,
            'text': 'OK',
            'data': {'list': list_bundle}
        }

    def serialize(self, list_bundle):
        if self.pretty:
            return json.dumps(list_bundle, indent=2)
        else:
            return json.dumps(list_bundle)


class XMLSerializer(BaseSerializer):
    def __init__(self, **kwargs):
        super(XMLSerializer, self).__init__(**kwargs)
        self.dom = getDOMImplementation()
        self.doc = self.dom.createDocument(None, "response", None)

    def _bool(self, value):
        if value in ('TRUE', 'FALSE'):
            return value.lower()
        else:
            raise ValueError("Invalid value for active")

    def _node(self, tag, text):
        elem = self.doc.createElement(tag)
        text_elem = self.doc.createTextNode(str(text))
        elem.appendChild(text_elem)
        return elem

    def bounds(self, bundle, value):
        bounds = self._bounds(value)
        # We need to convert this to a element here
        l = self.doc.createElement('bounds')

        for b in bounds:
            elem = self.doc.createElement('bound')
            for key, value in b.iteritems():
                child = self._node(key, value)
                elem.appendChild(child)
            l.appendChild(elem)

        bundle['bounds'] = l

    def alter_bundle(self, bundle):
        # Each item in the bundle should be converted to a text
        # node, if it isn't already a node (which it would be for bounds)
        elem = self.doc.createElement('region')
        for key, value in bundle.iteritems():
            if key == 'bounds':
                elem.appendChild(value)
            else:
                child = self._node(key, value)
                elem.appendChild(child)

        return elem

    def alter_list_bundle(self, list_bundle):
        top = self.doc.documentElement
        top.appendChild(self._node('version', 2))
        top.appendChild(self._node('code', 200))
        top.appendChild(self._node('text', 'OK'))

        # Create the data and list nodes
        data = self.doc.createElement('data')
        l = self.doc.createElement('list')
        for elem in list_bundle:
            l.appendChild(elem)

        data.appendChild(l)
        top.appendChild(data)
        return list_bundle

    def serialize(self, list_bundle):
        if self.pretty:
            return self.doc.toprettyxml(indent='  ')
        else:
            return self.doc.toxml()


def serialize(regions, serializer):
    """
    This does the following:
    1. Map each spreadsheet name into a suitable python function.
    2. Use the serializer class to bundle up the spreadhsheet values
        into a serializable form (with proper typing, etc)
    3. Allow the serializer to add any other header information, etc.
    4. Convert to the serialized format.
    """
    def _key(name):
        # Remove the '?' and replace _ with a space, convert to title
        name = name.replace('?', '').replace('_', ' ').title()
        # Convert to lower camel
        name = name[0].lower() + name[1:]
        # Remove spaces
        return name.replace(' ', '')

    def _to_bundle(index, region):
        bundle = {}
        serializer.region_id(bundle, index)
        for k, v in region.iteritems():
            key = _key(k)
            f = getattr(serializer, key, None)
            if f:
                f(bundle, v)
            else:
                # Convenience for strings, and things that need no conversion
                bundle[key] = v
        bundle = serializer.alter_bundle(bundle)
        return bundle

    list_bundle = []
    for i, region in enumerate(regions):
        try:
            list_bundle.append(_to_bundle(i, region))
        except ValueError:
            print >> sys.stderr, "*** ERROR: Invalid region specification: " + str(region)
            raise

    list_bundle = serializer.alter_list_bundle(list_bundle)
    serialized = serializer.serialize(list_bundle)
    return serialized


def output_stdout(_fmt, output, _opts):
    print output


def output_file(fmt, output, opts):
    path = os.path.join(opts.output_dir, 'regions.' + fmt)
    print 'Writing %s' % path
    with open(path, 'w+') as f:
        f.write(output)


def output_s3(fmt, output, opts):
    try:
        from boto.s3.connection import S3Connection
        from boto.s3.key import Key
    except ImportError:
        print >> sys.stderr, "Unable to publish to S3: Boto not installed."
        return

    # Verify the S3 configuration
    bucket_name = opts.output_s3
    access_key = opts.aws_access_key or os.environ.get('AWS_ACCESS_KEY_ID')
    secret_key = opts.aws_secret_key or os.environ.get('AWS_SECRET_ACCESS_KEY')

    if not access_key or not secret_key:
        print >> sys.stderr, "We need an AWS access key and AWS secret key"
        return

    conn = S3Connection(access_key, secret_key)
    bucket = conn.get_bucket(bucket_name)
    k = Key(bucket)
    k.key = 'regions.' + fmt

    # Set a content type
    content_types = {
        'json': 'application/json',
        'xml': 'text/xml'
    }
    if fmt in content_types:
        k.set_metadata('Content-Type', content_types[fmt])

    print 'Writing %s/%s' % (bucket_name, k.key)
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
            print s

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
            output = serialize(regions, cls(**serializer_opts))
            if opts.output_dir == '-':
                output_stdout(fmt, output, opts)
            elif opts.output_s3:
                output_s3(fmt, output, opts)
            else:
                output_file(fmt, output, opts)

        else:
            print >> sys.stderr, '*** ERROR: Unknown format: "%s"' % fmt


if __name__ == '__main__':
    main()
