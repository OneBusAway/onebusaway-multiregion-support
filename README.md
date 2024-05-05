# Multi-Region support files for OneBusAway

This project generates files that serve as the [OneBusAway Regions API](https://github.com/OneBusAway/onebusaway/wiki/Multi-Region#regions-rest-api), which helps the OneBusAway clients find servers across multiple regions within the same app.

The `update_regions.py` script retrieves the contents of the [OneBusAway Server Directory](https://docs.google.com/spreadsheets/d/11WpYOQn__NDjtvWgW0tjyqeLFoqxnZmmjklF9yP9ioU/edit#gid=0) (a Google Spreadsheet) as CSV, and then re-formats and exports this content as local JSON and XML files.  These files are then transferred to the `regions.onebusaway.org` server, and accessed as the [Regions API](https://github.com/OneBusAway/onebusaway/wiki/Multi-Region#regions-rest-api) by the mobile apps at the following URLs:

* http://regions.onebusaway.org/regions-v3.json
* http://regions.onebusaway.org/regions-v3.xml

More about this Regions API update process is found [here](https://github.com/OneBusAway/onebusaway/wiki/Multi-Region#multi-region-administration---updating-the-regions-rest-api-response).

#### tl;dr

Assuming that you have access to the `onebusaway-regions` bucket, have installed the awscli tools, and have set up your appropriate AWS credentials under the profile `obaregions`, you can update the regions files with the following commmands:

```
python update_regions.py --pretty
aws s3 mv regions.json s3://onebusaway-regions/regions.json --profile obaregions
aws s3 mv regions-v3.json s3://onebusaway-regions/regions-v3.json --profile obaregions
aws s3 mv regions-v3.xml s3://onebusaway-regions/regions-v3.xml --profile obaregions
aws s3 mv regions.xml s3://onebusaway-regions/regions.xml --profile obaregions
```

#### Prerequisites

You'll need to download and install [Python](https://www.python.org/).  This project has been tested with Python 2.7.x.

#### Usage

To generate new local JSON and XML files from the [OneBusAway Server Directory](https://docs.google.com/spreadsheets/d/11WpYOQn__NDjtvWgW0tjyqeLFoqxnZmmjklF9yP9ioU/edit#gid=0):

`python update_regions.py --pretty`

If you'd prefer to use a local CSV file as input for testing instead of the OBA Server Directory Google Spreadsheet, you can use the following command:
`python update_regions.py --input-file regions-test.csv --pretty`

You can remove the `--pretty` parameter if you'd prefer JSON and XML files without whitespace.

#### Output

The `update_regions.py` script will generate 4 files in your local directory:

* **regions-v3.json** - current JSON version of the Regions API that includes experimental servers (`experimental = true`)
* **regions-v3.xml** - current XML version of the Regions API that includes experimental servers (`experimental = true`)
* **regions.json** - a legacy version of the Regions API that does not include experimental servers
* **regions.xml** - a legacy version of the Regions API that does not include experimental servers

*When using the `regions-v3` API, apps should screen out regions with `experimental` set to true by default, and provide the user a setting to "opt-in" to using experimental regions.*

When new output files are generated, we add the four new files to the `/staging` directory in this repository.  The apps can then test with the staging files to ensure no problems exist.  The URL to access the staging files has the format:

`https://raw.githubusercontent.com/OneBusAway/onebusaway-multiregion-support/master/staging/regions-v3.json`

For example, in [OBA Android](https://github.com/OneBusAway/onebusaway-android), you can change string `regions_api_url` in the file `donottranslate.xml` to the above URL to make OBA Android use the staging Regions API file instead of the production Regions API.

After sufficient testing, these files can be moved to the `regions.onebusaway.org` server to replace the production Regions API files.

## Resources

Multi-Region documentation for the OneBusAway project is here:

https://github.com/OneBusAway/onebusaway/wiki/Multi-Region

Are you a developer interested in contributing to OneBusAway? Read up on the entire Application Suite here:

https://github.com/OneBusAway/onebusaway-application-modules/wiki

You can also learn more about the project at the main OneBusAway site:

http://onebusaway.org/

