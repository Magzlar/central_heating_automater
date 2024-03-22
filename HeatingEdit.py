import time
from datetime import datetime
import fourletterphat as flp # only availble on raspberry pi 
import paho.mqtt.client as mqtt # only availble on raspberry pi 
import math
import RPi.GPIO as GPIO # only availble on raspberry pi 
from smbus2 import ADCPI # only availble on raspberry pi 
import csv 


class DigitalDisplay:
    '''Handles displaying sentences on the LCD display with 4 character slots'''
    def __init__(self, sentence: str):
        self.sentence = sentence.upper().replace(" ","")
        
    def display_message(self):
        for position, char in enumerate(self.sentence):
            print(f"Goes here {position % 4} and display this character {char}")  
            if (position + 1) % 4 == 0:
                time.sleep(1)  

class MyMQTTClass(mqtt.Client):
    
    mqtt_connected = False

    def on_connect(self, mqttc, obj, flags, rc):
        if rc == 0: 
            print(f"Connection succesful - RC: {rc}")
            return rc 
        else:
            print(f"Connection error - RC: {rc}")

    def on_connect_fail(self, mqttc, obj):
        print("Connection failed")

    def on_message(self, mqttc, obj, msg):
        print(msg.topic+" "+str(msg.qos)+" "+str(msg.payload))
        topic = msg.topic 
        message_decode = str(msg.payload.decode("utf-8", "ignore"))

    def on_publish(self, mqttc, obj, mid):
        print("mid: "+str(mid))

    def on_subscribe(self, mqttc, obj, mid, granted_qos):
        print("Subscribed: "+str(mid)+" "+str(granted_qos))

    def on_log(self, mqttc, obj, level, string):
        print(string)

    def run(self):
        self.connect("mqtt.eclipseprojects.io", 1883, 60)
        self.subscribe("$SYS/#", 0)

        rc = 0
        while rc == 0:
            rc = self.loop()
        return rc

class CalculatingValues:
    
    correction_factor = 0.06 # Can optimise this by measuring at the pump and adjusting value 
    
    def __init__(self,raw_values:dict,correction_factor):
        self.raw_values = raw_values
        self.correction_factor = correction_factor 
        
    def transform(self):  # equation for correction factor
        for i in self.raw_values:
            self.raw_values[i] = self.raw_values[i] * self.correction_factor
        for i in self.raw_values:
            if 7500 < self.raw_values[i] < 30500:
                answer = (3950 / (math.log((54400 / self.raw_values[i]) - 1.68) + 13.248)) - 273.15
                self.raw_values[i] = answer
            else:
                answer = 10
                self.raw_values[i] = answer 
                print(f"{i} is out of range")

class FileManager:
    ''' Handles storing the data in a CSV and retriving the last value to know wether to turn heating on'''
    def __init__(self, file_location):
        self.file_location = file_location
        
    def retrive_last_value(self):
        with open(self.file_location,"r",errors="ignore") as file:
            final_line = file.readlines()[-1]
            return final_line 
    
    def assign_new_value(self):
        now = datetime.now()
 
        print("now =", now)
        room_stat_temp = 17
        # dd/mm/YY H:M:S
        dt_string = now.strftime("%d/%m/%Y;%H:%M:%S")
        dt_string = dt_string.split(";")
        dt_string = [dt_string[0],dt_string[1],room_stat_temp]
        
        file_location = "C:/Users/ryan/OneDrive/Documents/test_file.csv"

        with open(file_location,"a",newline="") as new_file:
            writer = csv.writer(new_file)
            writer.writerow(dt_string)
            
#Setup GPIO pins for the tripple relay board
class GPIO_start:

    @classmethod
    def start_up(self):
        pass
        GPIO.setmode(GPIO.BCM)
        GPIO.setwarnings(False)
        GPIO.setup(26, GPIO.OUT, initial=GPIO.HIGH)  # Channel 1 Central Heating
        GPIO.setup(20, GPIO.OUT, initial=GPIO.HIGH)  # Channel 2 Hot Water
        GPIO.setup(21, GPIO.OUT, initial=GPIO.HIGH)  # Channel 3 Pump, includes pump overrun timer


################ MAIN PROGRAM ######################
if __name__ == "__main__":
    first_loop = True
    file_location = "C:/Users/ryan/OneDrive/Documents/test_file.csv"
    startup_sentence = "Vers 2021 Ryan edit"
    message1 = DigitalDisplay(startup_sentence).start_up()
    previous_room_stat_setting = 0.1
    #GPIO_start.start_up()
    adc = ADCPi(0x68, 0x69, 16).set_pga(1).set_conversion_mode(1)
    adc.set_pga(1)
    adc.set_conversion_mode(1)

    while True:
        
        if first_loop:
            room_stat_setting = FileManager(file_location).retrive_last_value()
            print(room_stat_setting)
        elif room_stat_setting < previous_room_stat_setting:
            room_stat_setting = previous_room_stat_setting + 0.5
        newchannel8 = 29000
        correction_factor = 1

        devices = {("RoomTemp","NewChannel1"):10000, # adc.read_raw(1)
                ("CylTopTemp","NewChannel2"):20000, # adc.read_raw(2)
                ("CylBtmTemp","NewChannel3"):24500, # adc.read_raw(3)
                ("BoilerFlowTemp","NewChannel4"):2000, # adc.read_raw(4)
                ("HWReturntemp", "NewChannel5"):2000, # adc.read_raw(5)
                ("CHReturnTemp","NewChannel6"):21000, # adc.read_raw(6)
                "ReferenceChannel":23000}

        if newchannel8 in range(28000,30001):
            transformed_values = CalculatingValues(devices,correction_factor).transform()
            print(devices)
        else:
            transformed_values = CalculatingValues(devices,correction_factor=1).transform()
            print(devices)

        client = mqtt.Client("Ryan_Test")
        client.on_connect = MyMQTTClass.on_connect
        if client.on_connect == 0:
            MyMQTTClass.mqtt_connected = True 
            client.subscribe("CentralHeating/MQTTHW")  # look for the HW on/off request from MQTT
            client.subscribe("CentralHeating/MQTTCH")  # look for the CH on/off request from MQTT
            client.subscribe("CentralHeating/MQTTRoomStatAdj")  # look for the adjust the room stat setting value from MQTT
            client.subscribe("EarlyStart/MQTTES")  # look for the ES on/off request from MQTT *EMILY EarlyStart*
        else: 
            MyMQTTClass.mqtt_connected = False 
            print(f"MQTT failed to connect = {MyMQTTClass.mqtt_connected}")
            





