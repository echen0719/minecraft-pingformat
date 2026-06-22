# masscan 0.0.0.0-255.255.255.255 -p 25565 --rate 25000000 --exclude 255.255.255.255 -oJ output.json

import json

with open("output.json", "r") as infile, open("cleaned.json", "w") as outfile:
    data = json.load(infile)

    for entry in data:
        ip = entry.get("ip")
        timestamp = entry.get("timestamp")

        for portInfo in entry.get("ports", []):
            port = portInfo.get("port")

            item = {"ip": ip, "port": port, "timestamp": timestamp}
            outfile.write(json.dumps(item) + "\n")

print("Done!")