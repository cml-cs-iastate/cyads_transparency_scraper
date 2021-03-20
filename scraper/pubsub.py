from time import sleep

import requests
from google.cloud import pubsub_v1

import logging
import os



class GTRSubscriber:
    logger = logging.getLogger(__name__)

    def __init__(self, project_id, subscription):

        self.project_id = project_id
        self.subscription = subscription

    def subscribe(self):
        subscriber = pubsub_v1.SubscriberClient()
        subscription_name = f'projects/{self.project_id}/subscriptions/{self.subscription}'

        try:
            future = subscriber.subscribe(subscription_name, self.callback)
            self.logger.info(f"subscribed to subscription - {subscription_name}")
            # future.result()
        except Exception as e:
            self.logger.error("Not Able to subscribe to the topic ", str(e))
            raise e

    def callback(self, message):
        self.logger.info("GTR - Received the message : ")
        print(message)
        if message.attributes["type"] == "CHECK_GTR_FOR_UPDATE":

            print("scrapping table")
            message.ack()

            # notify django
            response = requests.post("http://127.0.0.1:8000/scraper/update_gtr")
            print(f"update endpoint response: {response} - text: {response.text}")


environ = "development"
if environ == "development":
    gtr_subscriber = GTRSubscriber(project_id=os.getenv("GOOGLE_CLOUD_PROJECT"),
                                   subscription=os.environ["GTR_SUBSCRIPTION"])
    gtr_subscriber.subscribe()
else:
    raise ValueError("environ net set up for production yet")

# keep program alive
keep_running = True
while keep_running:
    sleep(0.5)
