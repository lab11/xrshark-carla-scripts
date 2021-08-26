# Author: Meghan Clark

import carla
from time import time, sleep
import paho.mqtt.client as mqtt
import json
#import binascii
import base64

CARLA_IMAGES_OUT_TOPIC = "xrshark/background/image" # for sending images
MQTT_QOS = 0

MAX_FRAMES_PER_SECOND = 8

# Captures
class CameraCaptor:
    """Sends CARLA camera images to MQTT"""
    # class variables for tracking frame rate
    seconds_between_frames = 1.0/MAX_FRAMES_PER_SECOND
    last_time = time()

    # MQTT client is static, aka one instance for the entire class shared
    # between all CameraCaptor objects, because the send_image function is a
    # lamba function with no access to instance variables, only class variables.
    # This works because we assume there will only be one instance of
    # CameraCaptor per process.
    classwide_mqtt_client = mqtt.Client()


    def __init__(self, carla_ip='127.0.0.1', carla_port=2000, mqtt_ip='127.0.0.1', mqtt_port=1883):

        # Set up CARLA client
        self.carla_client = carla.Client(carla_ip, carla_port)
        self.carla_client.set_timeout(2.0)
        self.world = self.carla_client.get_world()
        self.spectator_camera = self.get_spectator_camera()

        # Set up static (so send_image() can access it) MQTT client
        CameraCaptor.classwide_mqtt_client.on_connect = self.on_mqtt_connect
        CameraCaptor.classwide_mqtt_client.on_disconnect = self.on_mqtt_disconnect
        CameraCaptor.classwide_mqtt_client.connect(mqtt_ip, mqtt_port)

    def get_spectator_camera(self):
        camera_blueprint = self.world.get_blueprint_library().find("sensor.camera.rgb")
        camera_offset = carla.Transform(carla.Location(), carla.Rotation())
        camera = self.world.spawn_actor(camera_blueprint, camera_offset, attach_to=self.world.get_spectator())
        camera.listen((lambda image: CameraCaptor.send_image(image)))
        return camera

    # Get CARLA spectator camera image and send over MQTT at desired FPS
    def send_image(image):
        # check to make sure within specified frames per second (FPS)
        if (time()-CameraCaptor.last_time) > CameraCaptor.seconds_between_frames:
            # update when last frame sent
            CameraCaptor.last_time = time()

            # create image message
            msg_dict = {"fov_deg": image.fov,
                        "height_pix": image.height,
                        "width_pix": image.width,
                        "raw_data_bytes": base64.b64encode(bytes(image.raw_data)).decode('ascii')}

            # convert Python dict to JSON
            msg_dict_json = json.dumps(msg_dict)

            # send to MQTT
            CameraCaptor.classwide_mqtt_client.publish(CARLA_IMAGES_OUT_TOPIC, msg_dict_json, MQTT_QOS)



    # Clean up before exiting
    def disconnect(self):
        # stop listening and remove spectator camera, else it persists in CARLA
        self.spectator_camera.stop()
        self.spectator_camera.destroy()
        # disconnect MQTT client
        CameraCaptor.classwide_mqtt_client.disconnect()

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


################################################################################
# MAIN
################################################################################

def main():
    camera_captor = CameraCaptor()
    try:
        CameraCaptor.classwide_mqtt_client.loop_forever()
    except KeyboardInterrupt as e:
        camera_captor.disconnect()

if __name__ == "__main__":
    main()
