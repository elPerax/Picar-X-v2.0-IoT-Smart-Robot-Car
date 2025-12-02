# 🚗 Picar-X v2.0 IoT Smart Robot Car – Milestone 3  
**Course:** Internet of Things 2 (IoT 2) – Fall 2025  
**Student:** Samuel Reyes Cifuentes  
**Institution:** Champlain College Saint-Lambert  

---

## 🌍 Project Overview
This project demonstrates an **IoT-enabled smart robot car** built using the **SunFounder Picar-X v2.0** kit and a **Raspberry Pi 4**.  
The system integrates multiple sensors and actuators, publishes live data to **Adafruit IO** using MQTT, stores logs locally in **CSV and SQLite**, syncs structured sensor data to a **Neon PostgreSQL cloud database**, and automatically uploads local logs to **Google Drive** every night.  

A dedicated **Flask dashboard** was also developed to visualize the Neon + SQLite data:  
🔗 Dashboard Repo: https://github.com/elPerax/picarx-flask-app

The project demonstrates a complete IoT pipeline:  
> **Sense → Process → Log → Store → Sync → Upload → Visualize → Control**

---

## 🧠 Features Implemented
✅ **Sensors (3 +):** 
- **Ultrasonic Module** – Detects obstacles and controls automatic avoidance.  
- **Grayscale Module** – Detects and follows a black line track.
- **Speaker / TTS Module** – Provides audible feedback and speaks text thas is received.
- **DHT11** – Measures ambient temperature & humidity.  
- **Pi Camera** – Captures photos/videos.

✅ **Actuators (3):**
- **TT Motors** – Drive the wheels.  
- **Servo Motor for camera** – Controls camera direction.  
- **Robot-Hat** - Controls steering direction

✅ **Cloud Connectivity (MQTT + Adafruit IO):**  
- Publishes:  
  - `ultrasonic_distance`  
  - `grayscale_left`, `grayscale_mid`, `grayscale_right`  
  - `line_state`  
  - `tts`  
- Subscribes:  
  - `picarx-command`  
  - `steering-command`  
  - `camera-command`  
  - `tts`   
### 🔁 New in Milestone 3
- Fully implemented **cloud-to-robot control**  
- Added **SQLite local database**  
- Added **Neon PostgreSQL cloud sync** (Python script pushes new rows -> Neon)  
- Added **Flask dashboard** for Neon/SQLite visualization  
- Improved **subscriber.py** (unified controller)  
- Added **systemd auto-start service**  
- Made file/DB sync fault-tolerant  

---
✅ **Local Data Logging:**
- Each sensor logs to a CSV file automatically named with the date, e.g:
  - /home/pi/picar-x/logs/2025-11-01_dht11.csv
- Each entry contains an ISO timestamp and value(s).

 ## Neon PostgreSQL Cloud Sync
 A sync script pushes new SQLite rows → Neon PostgreSQL:
```
Script:
/home/pi/picar-x/iot/neon_sync.py
Cron(every minute):
* * * * * /usr/bin/python3 /home/pi/picar-x/iot/neon_sync.py >> /home/pi/picar-x/logs/sync_to_neon.log 2>&1

```
This ensures:

  - Cloud DB stays updated
    
  - Remote visualization dashboards work
    
  - Data remains backed up


 ## ✅ Cloud Storage Automation (Google Drive)

- The script [`/home/pi/picar-x/tools/upload_yesterday.sh`](tools/upload_yesterday.sh) automatically uploads **the previous day’s log files** to Google Drive using **rclone**.  
- A **cron job** runs daily at **00:05 AM**, ensuring that uploads happen **unattended** once new logs are generated.  
- Uploaded files are neatly organized in Google Drive following this structure:
```
  My Drive /
└── RobotCar_M2 /
  └── logs /
    └── YYYY-MM-DD /
      ├── 2025-11-01_grayscale.csv
      ├── 2025-11-01_ultrasonic.csv
      └── ...
```
- If there are **no logs for a given day** (e.g., the robot wasn’t running), the script **skips the upload** and **does not create an empty folder** on Drive.  
This behavior keeps the cloud storage **clean and organized**, showing only dates when real data was collected.
- Upload evidence and logs are stored locally under: /home/pi/picar-x/logs/upload_YYYY-MM-DD.log

## 🌐 Flask Dashboard (Local + Neon)

A full web dashboard was developed to display:

  - Live Neon data
  
  - SQLite fallback data
  
  - Charts for each sensor
  
  - Line state history
  
  - TTS history

Repo: https://github.com/elPerax/picarx-flask-app

## ⚙️ System Architecture
Sensors (DHT11, Ultrasonic, Grayscale)
        ↓
  Raspberry Pi 4 + Robot HAT
        ↓
   MQTT (Paho) → Adafruit IO Cloud Dashboard
        ↓
   CSV Logs + SQLite DB
        ↓
 Local CSV Logs → rclone → Google Drive
        ↓
 Neon PostgreSQL Cloud Database
        ↓
 Flask Web Dashboard
        ↓
Cloud Commands → subscriber.py → Motors/Servo/TTS

## 🧩 Directory Structure
```text
picar-x/
├── example/
│   ├── 14.avoiding_obstacles_mqtt.py
│   ├── 15.dht11_mqtt.py
│   ├── 16.line_follow_mqtt.py
│   ├── 18.tts_mqtt.py
│   └── ...
├── iot/
│   ├── mqtt_helper.py
│   ├── logger.py
├── tools/
│   ├── upload_yesterday.sh
├── logs/
│   ├── 2025-11-01_grayscale.csv
│   ├── 2025-11-01_ultrasonic.csv
│   └── ...
└── .env
```

## 🔧 Configuration
- .env file: AIO_USERNAME=your_adafruit_username
             AIO_KEY=your_adafruit_key
             PG_DSN=postgresql://...
- Cron job: 5 0 * * * bash /home/pi/picar-x/tools/upload_yesterday.sh >> /home/pi/picar-x/logs/cron_upload.log 2>&1

## 🚀 How to Run
- SSH into the Pi

    -ssh pi@<raspberry-pi-ip>
    -cd ~/picar-x


- Activate virtual environment (if used)

    -source .venv/bin/activate


- Run each module individually

    -sudo python3 example/14.avoiding_obstacles_mqtt.py
    -sudo python3 example/15.dht11_mqtt.py
    -sudo python3 example/16.line_follow_mqtt.py
    -sudo python3 example/18.tts_mqtt.py


- Check Adafruit Dashboard
    -Observe live graphs and values updating in real time.

- Verify logs

    -ls /home/pi/picar-x/logs


- Automatic upload
    -Wait until 00:05 AM → check Google Drive folder for new daily logs.

## 📊 Example Data (log file sample)
timestamp,temp,humidity
2025-11-01T22:53:21,23.4,47
2025-11-01T22:58:23,23.5,48

## 🌐 Cloud Links
-**Adafruit dashboard:** https://io.adafruit.com/elperax8000/dashboards/picarx-iot-dashboard

-**Feeds Adafruit:**

    -grayscale left: https://io.adafruit.com/elperax8000/feeds/grayscale-left
    
    -grayscale mid: https://io.adafruit.com/elperax8000/feeds/grayscale-mid
    
    -grayscale right: https://io.adafruit.com/elperax8000/feeds/grayscale-right
    
    -line state: https://io.adafruit.com/elperax8000/feeds/line-state
    
    -tts: https://io.adafruit.com/elperax8000/feeds/tts
    
    -ultrasonic distance: https://io.adafruit.com/elperax8000/feeds/ultrasonic-distance

-**Google Drive logs folder:** https://drive.google.com/drive/folders/1A4Ai35VOQ5_w5rglKn54Gdh239tzeBDm?usp=sharing

## 🧰 Tools & Libraries
- **Python 3.9 / Raspberry Pi OS**
- **Libraries:**
  - `adafruit-circuitpython-dht` – reads temperature/humidity
  - `robot-hat` – motor, servo, and sensor control
  - `paho-mqtt` – publishes data to Adafruit IO
  - `python-dotenv` – loads `.env` credentials
- **Command-line Tools:**
  - `rclone` – syncs daily log files to Google Drive
- **Cloud Services:**
  - Adafruit IO (MQTT Broker)
  - Google Drive (via rclone backend)

## Video Link
https://www.youtube.com/shorts/56ofl5jYCgs

---

## ⚙️ Bill of Materials (BOM)

Below is the complete list of components used to build the IoT Smart Robot Car (PiCar-X v2.0).  
Each part is linked or described with its model and primary function.

| **Component** | **Model / Link** | **Function** |
|----------------|------------------|---------------|
| **Raspberry Pi 4 (4 GB)** | [SunFounder PiCar-X v2.0 Kit](https://www.sunfounder.com/products/picar-x-ai-robot-car-kit) | Main controller & computing unit |
| **Robot HAT Plus** | – | Motor, servo, and sensor interface board |
| **TT Motors × 2** | Included in kit | Drive rear wheels (differential motion) |
| **SG90 Servo Motor** | Included in kit | Steering control for front wheels |
| **DHT11 Sensor** | [Adafruit DHT11 Module](https://www.adafruit.com/product/386) | Measures ambient temperature & humidity |
| **HC-SR04 Ultrasonic Module** | [HC-SR04 Datasheet](https://cdn.sparkfun.com/datasheets/Sensors/Proximity/HCSR04.pdf) | Measures obstacle distance |
| **Grayscale Module × 3** | SunFounder Line Tracking Sensors | Detects and follows black line track |
| **Pi Camera v2** | [Raspberry Pi Camera Module v2](https://www.raspberrypi.com/products/camera-module-v2/) | Captures photos and video |
| **Speaker (Built-in)** | On Robot HAT | Provides audio & text-to-speech feedback |

---

## 🧩 Wiring / Schematic Diagram and Photos

The following images illustrate the wiring connections between the Raspberry Pi, Robot HAT, sensors, and actuators.

**-Diagram of wiring:**

<img width="443" height="286" alt="image" src="https://github.com/user-attachments/assets/4d0e6f69-93aa-4c43-81ad-b4c54cb9b859" />

**-Images of wiring(Motors and Robot-Hat wiring):**
<img width="979" height="740" alt="image" src="https://github.com/user-attachments/assets/0e4060ec-b297-4c38-a935-a576e3498a23" />
<img width="557" height="741" alt="image" src="https://github.com/user-attachments/assets/4e627139-d528-444d-91d3-d5f99795e3d2" />

**-Full photo of Robot:**
<img width="1374" height="790" alt="image" src="https://github.com/user-attachments/assets/396348a2-1b22-4a51-9a5f-ad265c23db0c" />




> **Note:** Ensure power separation between logic (5 V) and motors (external battery pack).  
> All grounds (GND) must be connected together for proper reference.

## ⚙️ System Architecture (Till Milestone 2)

**System architecture:**
<img width="2266" height="1226" alt="image" src="https://github.com/user-attachments/assets/a34d4127-b76b-4731-8476-9fb36610ade6" />


---
## 🧰 Setup Instructions

```bash
# 1️⃣  Install Raspberry Pi OS (64-bit)
# Use Raspberry Pi Imager → Raspberry Pi OS (64-bit)
# Username: pi   Password: raspberry
# Enable SSH and Wi-Fi before flashing (Advanced Options).

# 2️⃣  First-boot update
sudo apt update && sudo apt upgrade -y

# 3️⃣  Enable interfaces
sudo raspi-config
# → Interface Options → I2C → Enable
# → Interface Options → Camera → Enable
sudo reboot

# 4️⃣  Install I2C tools and Python build deps
sudo apt install -y i2c-tools python3-smbus python3-pip python3-venv git

# 5️⃣  Clone and install SunFounder libraries
cd ~
git clone https://github.com/sunfounder/robot-hat.git && cd robot-hat
sudo python3 setup.py install
cd ~
git clone https://github.com/sunfounder/picar-x.git && cd picar-x
sudo python3 setup.py install
sudo reboot

# 6️⃣  (Optional) Create Python venv and dependencies
cd ~/picar-x
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```


---

## 🔁 Reliability & Auto-Start Configuration

To ensure continuous and fault-tolerant operation, the system includes both **automatic service management** and **exception handling**.

### 🧩 Systemd Service File
Create a file at `/etc/systemd/system/picarx.service`:

```ini
[Unit]
Description=PiCar-X IoT Service
After=network-online.target

[Service]
ExecStart=/usr/bin/python3 /home/pi/picar-x/example/main_mqtt.py
WorkingDirectory=/home/pi/picar-x
Restart=on-failure
User=pi
EnvironmentFile=/home/pi/picar-x/.env

[Install]
WantedBy=multi-user.target

Enable and start it:
sudo systemctl daemon-reload
sudo systemctl enable picarx.service
sudo systemctl start picarx.service
```
## ⚙️ Exception Handling Example
All MQTT publishing scripts include retry logic and error catching:
```
try:
    client.publish(feed, value)
except Exception as e:
    print(f"[ERROR] MQTT publish failed: {e}")
    time.sleep(2)
    client.reconnect()
```
**Purpose:**
Ensures the service auto-restarts if a crash occurs and reconnects to Adafruit IO after transient network failures.

## 📦 Python Requirements

All Python dependencies used in this project are listed in the `requirements.txt` file located at the root of the repository.

To install them quickly, run:
```bash
pip install -r requirements.txt
```

### 🧾 Data Schema

Each script logs sensor data using the shared `iot/logger.py` module, which automatically names each file as:


Each CSV file starts with a header row generated from the dictionary keys passed to `log(sensor, data)` inside each script.

| **Log File** | **Generated by Script** | **Columns (in order)** | **Description / Units** |
|---------------|--------------------------|--------------------------|--------------------------|
| `YYYY-MM-DD_grayscale.csv` | `16.line_follow_mqtt.py` | `timestamp, left, mid, right` | Raw grayscale sensor values (0–4095) from the left, middle, and right channels. |
| `YYYY-MM-DD_grayscale_state.csv` | `16.line_follow_mqtt.py` | `timestamp, state` | Line-following decision: one of `forward`, `left`, `right`, or `stop`. |
| `YYYY-MM-DD_dht11.csv` | `15.dht11_mqtt.py` | `timestamp, temp, humidity` | Ambient temperature in °C and humidity in %RH from DHT11. |
| `YYYY-MM-DD_ultrasonic.csv` | `14.avoiding_obstacles_mqtt.py` | `timestamp, distance` | Distance to nearest object measured in centimeters (cm). |
| `YYYY-MM-DD_tts.csv` | `18.tts_mqtt.py` | `timestamp, text` | Text message spoken by the robot and published to Adafruit IO. |

> Each row contains a precise timestamp in ISO 8601 format (e.g., `2025-11-01T22:53:21`) followed by one or more sensor or actuator values.  
> These structured CSV logs are automatically synchronized to Google Drive nightly for visualization and backup.

## 🧾 Data Schema

All sensor data is logged through the shared `iot/logger.py` module.  
Each CSV file is automatically named using the format:
YYYY-MM-DD_<sensor>.csv
```
Each CSV begins with a header row generated from the dictionary keys passed into the logger.

| **Log File** | **Generated by Script** | **Columns (in order)** | **Description / Units** |
|---------------|--------------------------|--------------------------|--------------------------|
| `YYYY-MM-DD_grayscale.csv` | `16.line_follow_mqtt.py` | `timestamp, left, mid, right` | Raw grayscale sensor values (0–4095) |
| `YYYY-MM-DD_grayscale_state.csv` | `16.line_follow_mqtt.py` | `timestamp, state` | Line-following logic result: `forward`, `left`, `right`, or `stop` |
| `YYYY-MM-DD_dht11.csv` | `15.dht11_mqtt.py` | `timestamp, temp, humidity` | Temperature in °C and humidity in %RH |
| `YYYY-MM-DD_ultrasonic.csv` | `14.avoiding_obstacles_mqtt.py` | `timestamp, distance` | Distance to the nearest obstacle (cm) |
| `YYYY-MM-DD_tts.csv` | `18.tts_mqtt.py` | `timestamp, text` | Text spoken by the robot via TTS |

These logs are used for:
- **CSV file storage**,  
- **SQLite database tables**,  
- **Neon PostgreSQL cloud synchronization**,  
- **Flask dashboard visualization**.  

This ensures that all data is available both locally and remotely, forming a complete IoT data pipeline.
```
---
## 🧠 Reflection
The hardest part of this milestone was fixing the servo calibration.  
At first, the steering angles were inconsistent, and the car struggled during sharp left and right turns. Adjusting the PWM boundaries, wheel alignment, and servo offsets took a lot of trial and error, but seeing the car drive correctly afterward made the effort worth it.

Connecting all sensors to MQTT and managing the timing so the car didn’t exceed Adafruit IO’s free publish limits was another challenge. Getting the ultrasonic sensor, grayscale sensors, and TTS feed to all send data reliably required tuning delays, adding retry logic, and building a more solid MQTT helper.

Milestone 3 also introduced a completely new layer of complexity with **SQLite**, **Neon PostgreSQL**, and the **Flask dashboard**. Writing the sync script, testing data transfers, validating table schemas, and seeing the data appear instantly in Neon made the project feel like a real, production-level IoT ecosystem. The dashboard helped visualize the pipeline clearly and made the whole system feel more complete.

Overall, this project taught me how IoT devices collect data, store it locally, sync it to the cloud, and interact with remote dashboards. It was challenging, but extremely rewarding to see the robot move, avoid obstacles, follow lines, speak through TTS, and sync all of its data automatically. The hands-on experience of combining hardware, software, networking, and cloud systems gave me a much deeper understanding of IoT.
