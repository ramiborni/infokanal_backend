import requests
from django_cron import CronJobBase, Schedule


class FetchAiFeed:
    def do(self):
        try:
            response = requests.get("https://services.infokanal.com/feed/")
            response.raise_for_status()  # Raises an HTTPError if the status is 4xx, 5xx
            data = response.json()
            # Process the data as needed
            print("Data fetched successfully:", data)
        except requests.exceptions.RequestException as e:
            print(f"Error fetching data: {e}")


class RunEveryTenMinutesCronJob(CronJobBase, FetchAiFeed):
    RUN_EVERY_MINS = 10
    schedule = Schedule(run_every_mins=RUN_EVERY_MINS)
    code = "cron.RunEveryTenMinutesCronJob"