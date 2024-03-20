import os

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