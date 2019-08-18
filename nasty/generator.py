"""This module generates jobs.

Change config.json to define what keywords and time-range or language to use."""
import json
from calendar import monthrange
from typing import Dict


def generate_jobs(config: Dict) -> None:
    """
    Generates a jobs.jsonl file, that worker can use to download tweets.
    """
    keywords = config["keywords"]
    start = config["since"].split("-")
    end = config["until"].split("-")
    start_year = int(start[0])
    start_month = int(start[1])
    start_day = int(start[2])
    end_year = int(end[0])
    end_month = int(end[1])
    end_day = int(end[2])
    try:
        lang = config["lang"]
    except KeyError:
        lang = "en"
    # If the end day is before the start day, no new file will be created,
    # atm also no error message. If a date is missing, we will get an error.
    # Create or overwrite a Jobs file. Each Line is a job, saved as valid
    # JSON.
    with open("jobs.jsonl", "w") as jobs:
        for keyword in keywords:
            for year in range(start_year, end_year + 1):
                # If the year right now is not the start_year,
                # the month we should start searching is January (1)
                if year != start_year:
                    start_month_range = 1
                # Else (the year is the start_year)
                # we have to start from the specified month, not earlier
                # To not overwrite the start_month for the next
                # year/keyword -> new variable
                else:
                    start_month_range = start_month
                # If the year is not the end_year,
                # we want to search for the full year -> until December
                if year != end_year:
                    end_month_range = 12
                # Else (we are in the last year to search trough)
                # we only want to got until the specified end_month
                # Also new variable to not overwrite
                else:
                    end_month_range = end_month
                for month in range(start_month_range, end_month_range + 1):
                    # If we are in the last year to search and in the last
                    # month, we end at the specified end day
                    if year == end_year and month == end_month:
                        day_range = end_day
                    # Else we want to search for as long as the month has
                    # days
                    else:
                        day_range = monthrange(year, month)[1] + 1
                    # If we are not in the start_month,
                    # we shall begin at the first day of the month
                    if month != start_month:
                        start_day_range = 1
                    # If we are in the start_month,
                    # we want to start from the specified start_day
                    else:
                        start_day_range = start_day
                    for day in range(start_day_range, day_range):
                        # If the day is the last day of the month,
                        # we need "until" to jump to the first of the next
                        if day == monthrange(year, month)[1]:
                            # If its also December we need to jump to the
                            # next year
                            if day == monthrange(year, month)[1] \
                                    and month == 12:
                                # for 0x use month:02
                                since = f"{year}-{month}-{day}"
                                until = f"{year + 1}-01-01"
                            # Else -> jump to the first of the next month
                            else:
                                since = f"{year}-{month}-{day}"
                                until = f"{year}-{month + 1}-01"
                        # Else (if its not the last day of a month),
                        # just jump a day ahead for until
                        else:
                            since = f"{year}-{month}-{day}"
                            until = f"{year}-{month}-{day + 1}"
                        # Save the keyword and dates to a dict, for easy
                        # json dumping
                        data_dict = dict()
                        data_dict["keyword"] = keyword
                        data_dict["start_date"] = since
                        data_dict["end_date"] = until
                        data_dict["lang"] = lang
                        jobs.write(json.dumps(data_dict))
                        jobs.write("\n")


if __name__ == '__main__':
    generate_jobs()
