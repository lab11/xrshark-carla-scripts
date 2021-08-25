# Author: Meghan Clark

import carla
from time import sleep
import paho.mqtt.client as mqtt
import json

CARLA_LOCATION_OUT_TOPIC = "xrshark/camera/set" # for sending spectator coords
CARLA_LOCATION_IN_TOPIC = "xrshark/camera/get" # for receiving spectator coords
MQTT_QOS = 0

class CARLAViewSynchronizer:
    """Sends and receives CARLA spectator locations via MQTT"""

    def __init__(self, carla_ip='127.0.0.1', carla_port=2000, mqtt_ip='127.0.0.1', mqtt_port=1883):

        # Set up CARLA client
        self.carla_client = carla.Client(carla_ip, carla_port)
        self.carla_client.set_timeout(2.0)
        self.spectator = self.carla_client.get_world().get_spectator()

        # Set up MQTT client
        self.mqtt_client = mqtt.Client()
        self.mqtt_client.on_connect = self.on_mqtt_connect
        self.mqtt_client.on_message = self.on_mqtt_message
        self.mqtt_client.on_subscribe = self.on_mqtt_subscribe
        self.mqtt_client.on_disconnect = self.on_mqtt_disconnect
        self.mqtt_client.connect(mqtt_ip, mqtt_port)

    # Get CARLA spectator location/rotation (z-up lefthanded)
    # Transform to Unity coordinate system (y-up lefthanded)
    # Send over MQTT
    def send_coords(self):
        while True:
            # get CARLA spectator location and rotation
            t = self.spectator.get_transform()

            # convert coordinates from CARLA (Unreal) to XRShark (Unity).
            # z-up lefthanded to y-up lefthanded
            # Unity forward = z, right = x, up = y.
            # Unreal forward = x, right = y, up = z
            msg_dict = {
                "location": {"x": round(t.location.y, 10),
                            "y": round(t.location.z, 10),
                            "z": round(t.location.x, 10)},
                "rotation": {"pitch":  round(t.rotation.yaw, 10),
                            "roll": 360-round(t.rotation.pitch, 10),
                            "yaw":  round(t.rotation.roll, 10)}
                        }

            # convert Python dict to JSON
            msg_dict_json = json.dumps(msg_dict)
            #print(msg_dict_json)

            # send to MQTT
            self.mqtt_client.publish(CARLA_LOCATION_OUT_TOPIC, msg_dict_json, MQTT_QOS)
            self.mqtt_client.loop()
            sleep(0.02)

    # Process MQTT message with XRShark location/rotation (y-up lefthanded)
    # Transform to CARLA coordinate system (z-up lefthanded)
    # Set CARLA spectator location/rotation
    def receive_coords(self, msg):
        # Convert coordinates from XRShark (Unity) to CARLA (Unreal)
        # y-up lefthanded to z-up lefthanded
        #print(msg)
        msg_location = msg["location"]
        msg_rotation = msg["rotation"]
        location = carla.Location(msg_location["z"],
                                  msg_location["x"],
                                  msg_location["y"])
        rotation = carla.Rotation(360-msg_rotation["roll"],
                                  msg_rotation["pitch"],
                                  msg_rotation["yaw"])
        new_transform = carla.Transform(location, rotation)
        self.spectator.set_transform(new_transform)


    # Clean up before exiting
    def disconnect(self):
        self.mqtt_client.disconnect()

    ############################################################################
    # MQTT CALLBACKS
    ############################################################################

    def on_mqtt_connect(self, client, userdata, flags, rc):
        if rc == 0:
            print("Connected to MQTT broker")
            self.mqtt_client.subscribe(CARLA_LOCATION_IN_TOPIC, MQTT_QOS)
        else:
            print("Failed to connect (return code {})".format(rc))

    def on_mqtt_subscribe(self, client, userdata, mid, granted_qos):
        print("Subscribed")

    def on_mqtt_message(self, client, userdata, msg):
        self.receive_coords(json.loads(msg.payload.decode('utf-8')))

    def on_mqtt_disconnect(self, client, userdata, rc):
        print("Disconnected from MQTT broker")


################################################################################
# MAIN
################################################################################

def main():
    synchronizer = CARLAViewSynchronizer()
    try:
        #synchronizer.send_coords()
        synchronizer.mqtt_client.loop_forever()
    except KeyboardInterrupt as e:
        synchronizer.disconnect()

if __name__ == "__main__":
    main()
