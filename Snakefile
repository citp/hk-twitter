import datetime

def datetime_range(start=None, end=None):
  start = datetime.date(start[0], start[1], start[2])
  end = datetime.date(end[0], end[1], end[2])
  span = end - start
  for i in range(span.days + 1):
    date = start + datetime.timedelta(days=i)
    yield "%04d_%02d_%02d" % (date.year, date.month, date.day)

DATETIME_RANGE = list(datetime_range((2019,1,1), (2020,1,1)))

rule all:
  input:
    expand("results/users/{date}_hk.json", date=DATETIME_RANGE)

rule fetch_and_process_archive:
  output:
    "results/users/{date}_hk.json"
  wildcard_constraints:
    date="\d+_\d+_\d+"
  shell:
    "python3 twitter/main.py {wildcards.date} --subdir results/users"
