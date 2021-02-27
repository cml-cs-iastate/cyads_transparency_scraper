import csv
import datetime
import logging

from typing import Union

from google.cloud import bigquery
from google.cloud.bigquery import Dataset, TableReference, QueryJob
from google.cloud.bigquery import Table

from scraper.tasks import scrape_new_urls

client = bigquery.Client()
creative_table_id = "bigquery-public-data.google_political_ads.creative_stats"

from huey.contrib.djhuey import task

logger = logging.getLogger(__name__)


def enriched_transparency_is_up_to_date(
        last_modified_creative_table_local: Union[datetime.datetime, None] = None) -> bool:
    if last_modified_creative_table_local is None:
        return False
    creative_table_public: Table = client.get_table(creative_table_id)
    logger.info(f"creative table has {creative_table_public.num_rows} rows")
    logger.info(f"creative table was last modified: {creative_table_public.modified}")
    return last_modified_creative_table_local >= creative_table_public.modified


@task()
def enrich_transparency_report():
    logger.info("Checking if local copy of transparency report is out of date...")
    update_status = enriched_transparency_is_up_to_date()
    logger.info(f"status: {update_status}")
    if update_status:
        return
    logger.info("brand new report")
    logger.info("grabbing latest report...")

    # creative_table_public: Table = client.get_table(creative_table_id)


    # Grab the latest report
    get_unseen_creatives()
    scrape_new_urls()


def get_unseen_creatives(latest_first_seen_timestamp_in_db: datetime.datetime = datetime.datetime.min,
                         use_csv: bool = True):
    import csv
    from .models import CreativeInfo
    if use_csv:
        with open("./creatives.csv") as creative_csv:
            reader = csv.DictReader(creative_csv)
            count =0
            creatives_to_insert = []
            for row in reader:
                if count % 1000 == 0:
                    print(f"built {count} rows")
                creative = CreativeInfo()
                creative.ad_id = row["ad_id"]
                creative.advertiser_id = row["advertiser_id"]
                creative.transparency_url = row["ad_url"]
                creative.first_served_timestamp = row["first_served_timestamp"]
                creatives_to_insert.append(creative)
                count += 1
            print(f"Finished building {count} rows")
            CreativeInfo.objects.bulk_create(creatives_to_insert, ignore_conflicts=True)
    print("finished saving")
    return
    print("passed the return")
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
     WHERE ad_type='Video'
     AND first_served_timestamp >= @previous_scrape_latest_first_served_timestamp
     ORDER BY first_served_timestamp DESC;
    """

    job_config = bigquery.QueryJobConfig(
        query_parameters=[
            bigquery.ScalarQueryParameter("previous_scrape_latest_first_served_timestamp", "TIMESTAMP",
                                          latest_first_seen_timestamp_in_db),
        ]
    )
    import csv
    fields = ["ad_id", "transparency_url", "advertiser_id", "first_served_timestamp"]

    query_job: QueryJob = client.query(query, job_config=job_config)  # Make an API request.
    logger.info("running query")
    with open("creatives.csv", mode="w", encoding="utf8") as csvfile:
        csvwriter = csv.writer(csvfile)
        csvwriter.writerow(fields)

        for index, row in enumerate(query_job):
            csvwriter.writerow([row.ad_id, row.ad_url, row.advertiser_id, row.first_served_timestamp])
            if index % 100 == 0:
                print(f"saved {index} rows")

    # Store the last modified table timestamp after completion of all
    # Store the first_served_timestamp after completion of all
    pass
