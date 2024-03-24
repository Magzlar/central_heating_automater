# Central heating automater/controller

This project is designed to manage central heating system by turning it on when the temp drops below a certain value, also includes class for displaying messages on fourletterphat screen

## Features

- **Message Display**: Display messages on a 4-character digital display
- **MQTT Integration**: Control and receive updates from various home automation devices using MQTT.
- **Sensor Data Processing**: Collect and process data from connected sensors, applying correction factors and transformations as needed
- **Logging and Monitoring**: Track system status and sensor readings, providing insights into the home environment and realtime adjustments

## Requirements

- Raspberry Pi (w/GPIO pins)
- Python >3.6
- Digital Four Letter pHAT display
- GPIO compatible temperature sensor
- MQTT broker 
