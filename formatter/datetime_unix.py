"""
Formatting current date and time into string representations.
"""
from datetime import datetime

now = datetime.now() # current date and time

# date_time = now.strftime("%m/%d/%Y, %H:%M:%S")
# print("date and time:",date_time)

datetime = now.strftime("%Y%m%d-%H%M%S")
print(datetime)