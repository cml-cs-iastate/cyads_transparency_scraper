import datetime

from typing import Union

from google.cloud import bigquery
from google.cloud.bigquery import Dataset, TableReference
from google.cloud.bigquery import Table
client = bigquery.Client()

creative_table_id = "bigquery-public-data.google_political_ads.creative_stats"


def enriched_transparency_is_up_to_date(last_modified_creative_table_local: Union[datetime.datetime, None] = None) -> bool:
    if last_modified_creative_table_local is None:
        return False
    creative_table_public: Table = client.get_table(creative_table_id)
    print(f"creative table has {creative_table_public.num_rows} rows")
    print(f"creative table was last modified: {creative_table_public.modified}")
    return last_modified_creative_table_local >= creative_table_public.modified


def enrich_transparency_report():
    print("Checking if local copy of transparency report is out of date...")
    if enriched_transparency_is_up_to_date():
        return
    print("brand new report")
    print("grab latest report next.")

    creative_table_public: Table = client.get_table(creative_table_id)

    print(f"table schema: {creative_table_public.schema}")

    # Grab the latest report


def get_unseen_creatives(latest_first_seen_timestamp_in_db: datetime.datetime):
    # To limit results to only creatives that were added since the last scrape, this query only returns ads
    # that have a first served timestamp >= the previous updates latest first_served_timestamp
    #
    # first_served_timestamp - The timestamp of the earliest impression for this ad.

    # As an example, the last modification time of the public table was at: 2021-02-25 02:10:36.848000+00:00 There is
    # a difference of about ~3 days between when the data is published, and when the last datapoint is collected in
    # the public dataset first_served_timestamp = 2021-02-22 06:45:00 UTC Our stored first_served_timestamp would be
    # somewhere around 2021-02-18 00:00:00 UTC

    # Next, we will still check if we already have the creative downloaded, the above query restriction cuts down on
    # the amount of creatives needing to be checked.

    query = """
    SELECT ad_id, ad_url, advertiser_id, first_served_timestamp
     FROM `bigquery-public-data.google_political_ads.creative_stats`
     WHERE ad_type='video'
     AND first_served_timestamp >= @previous_scrape_latest_first_served_timestamp
     ORDER BY first_served_timestamp DESC
     LIMIT 100;
    """

    job_config = bigquery.QueryJobConfig(
        query_parameters=[
            bigquery.ScalarQueryParameter("previous_scrape_latest_first_served_timestamp", "INT64", latest_first_seen_timestamp_in_db),
        ]
    )

    query_job = client.query(query, job_config=job_config)  # Make an API request.
    for row in query_job:
        print("{}: \t{}".format(row.ad_id, row.ad_url))
        break

    # Store the last modified table timestamp after completion of all
    # Store the first_served_timestamp after completion of all
    pass
