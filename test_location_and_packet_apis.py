# Author: Meghan Clark
# Tests the XRShark location API by spawning some agents and sending their
# locations into MQTT for XRShark

import carla
import random
from time import sleep
import json
import paho.mqtt.client as mqtt

MSGS_PER_SECOND = 25
NUM_VEHICLES = 10

CAR_LOCATION_OUT_TOPIC = "xrshark/host/location" # for sending car coords
PACKET_OUT_TOPIC = "xrshark/packet" # for sending network traffic
MQTT_QOS = 1

class LocationTester:
    """Create agents and stream their locations into MQTT (and thus XRShark)"""

    def __init__(self, carla_ip='127.0.0.1', carla_port=2000, mqtt_ip='127.0.0.1', mqtt_port=1883):

        # Set up CARLA client
        self.carla_client = carla.Client(carla_ip, carla_port)
        self.carla_client.set_timeout(2.0)
        self.world = self.carla_client.get_world()
        self.blueprint_library = self.world.get_blueprint_library()

        # Set up MQTT client
        self.mqtt_client = mqtt.Client()
        self.mqtt_client.on_connect = self.on_mqtt_connect
        self.mqtt_client.on_disconnect = self.on_mqtt_disconnect
        self.mqtt_client.connect(mqtt_ip, mqtt_port)

        # Bookkeeping
        self.ids_to_vehicles = {}
        self.used_spawn_points = {}

    def create_vehicles(self, num_actors=2):
        bp = self.blueprint_library.filter('model3')[0]
        print(bp)

        for i in range(num_actors):
            if len(self.used_spawn_points) < len(self.world.get_map().get_spawn_points()):
                spawn_point = None
                while spawn_point == None:
                    candidate_spawn_point = random.choice(self.world.get_map().get_spawn_points())
                    if candidate_spawn_point not in self.used_spawn_points:
                        spawn_point = candidate_spawn_point
                        self.used_spawn_points[candidate_spawn_point] = True
                vehicle = self.world.spawn_actor(bp, spawn_point)
                vehicle.apply_control(carla.VehicleControl(throttle=1.0, steer=0.0))
                object_id = "Vehicle " + str(vehicle.id)
                self.ids_to_vehicles[object_id] = vehicle

    def send_location_msgs(self):
        for object_id in self.ids_to_vehicles:
            loc_msg_json = self.get_location_msg(object_id)
            #print(loc_msg_json)
            self.mqtt_client.publish(CAR_LOCATION_OUT_TOPIC, loc_msg_json, MQTT_QOS)
            self.mqtt_client.loop()

    def get_location_msg(self, object_id):
        t = self.ids_to_vehicles[object_id].get_transform()
        msg_dict = {"object_id": object_id,
                    "location": {
                        "x_right_meters": t.location.y,   # y is right in CARLA
                        "y_up_meters": t.location.z,      # z is up in CARLA
                        "z_forward_meters": t.location.x} # x is forward in CARLA
                    }
        # convert Python dict to JSON
        msg_dict_json = json.dumps(msg_dict)
        return msg_dict_json


    # sends totally made up random network traffic
    def send_random_packet_msg(self):
        # pick random pair, send packet
        vehicle_ids = self.ids_to_vehicles.keys()
        if len(vehicle_ids) > 1:
            pair = random.sample(vehicle_ids, 2)
            msg_dict = {"src_object_id": pair[0],
                        "dst_object_id": pair[1],
                        "src_ip": "192.168.1.120",
                        "dst_ip": "52.237.246.196",
                        "src_port": "50576",
                        "dst_port": "1410",
                        "src_mac": "3c:15:c2:bc:c1:68",
                        "dst_mac": "3c:37:86:24:46:fd",
                        "protocol": "udp",
                        "payload":""}
            # convert Python dict to JSON
            msg_dict_json = json.dumps(msg_dict)
            #print(msg_dict_json)
            self.mqtt_client.publish(PACKET_OUT_TOPIC, msg_dict_json, MQTT_QOS)
            self.mqtt_client.loop()


    def cleanup(self):
        for object_id in self.ids_to_vehicles:
            self.ids_to_vehicles[object_id].destroy()
        self.used_spawn_points = {}

    ############################################################################
    # MQTT CALLBACKS
    ############################################################################

    def on_mqtt_connect(self, client, userdata, flags, rc):
        if rc == 0:
            print("Connected to MQTT broker")
        else:
            print("Failed to connect (return code {})".format(rc))

    def on_mqtt_disconnect(self, client, userdata, rc):
        print("Disconnected from MQTT broker")

if __name__=="__main__":
    lt = LocationTester()
    try:
        lt.create_vehicles(NUM_VEHICLES)
        while True:
            lt.send_location_msgs()
            lt.send_random_packet_msg()
            sleep(1.0/MSGS_PER_SECOND)
    except KeyboardInterrupt:
        "Exiting..."
    finally:
        print("Cleaning up...")
        lt.cleanup()
        print("Done")
