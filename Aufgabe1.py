import ntplib
import time
import csv
from tqdm import tqdm


def get_ntp_offset(server):
    c = ntplib.NTPClient()
    response = c.request(server, version=3)
    return response.offset


def main():
    ntp_servers = [
        "de.pool.ntp.org",
        "time.google.com",
        "time.windows.com",
    ]  # Add more NTP servers if needed
    duration = 3600*3  # Duration in seconds (1 hour)
    interval = 10  # Interval in seconds for each measurement

    num_measurements = duration // interval
    data = []

    for i in tqdm(range(num_measurements)):
        offsets = []
        local_times = []
        for server in ntp_servers:
            try:
                offset = get_ntp_offset(server)
                local_time = time.time()
                offsets.append(offset)
                local_times.append(local_time)
            except Exception as e:
                continue
        data.append((sum(offsets)/len(offsets), sum(local_times)/len(local_times)))
        time.sleep(interval)

    with open("ntp_accuracy_data.csv", "w", newline="") as csvfile:
        fieldnames = ["Local Time", "Offset"]
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        for datum in data:
            writer.writerow(
                {"Local Time": datum[1], "Offset": datum[0]}
            )

    print("Data saved to ntp_accuracy_data.csv")


if __name__ == "__main__":
    main()
