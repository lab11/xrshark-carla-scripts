# Uses TCP

import carla
from time import time, sleep
#import binascii
import base64
import _thread

import socket

import queue

TCP_IP = "127.0.0.1"
TCP_PORT = 8891

CARLA_IP = "127.0.0.1"
CARLA_PORT = 2000

CONNECTION = None
SOCK = None

FPS = 40
LAST_FRAME_TIME = time()

IMAGE_QUEUE = queue.Queue()

def init_carla_camera():
    # Set up CARLA client
    carla_client = carla.Client(CARLA_IP, CARLA_PORT)
    carla_client.set_timeout(2.0)
    world = carla_client.get_world()
    camera_blueprint = world.get_blueprint_library().find("sensor.camera.rgb")
    # camera_blueprint.set_attribute('image_size_x', '1920')
    # camera_blueprint.set_attribute('image_size_y', '1080')
    camera_blueprint.set_attribute('image_size_x', '640')
    camera_blueprint.set_attribute('image_size_y', '480')
    # camera_blueprint.set_attribute('image_size_x', '800')
    # camera_blueprint.set_attribute('image_size_y', '600')
    camera_offset = carla.Transform(carla.Location(), carla.Rotation())
    camera = world.spawn_actor(camera_blueprint, camera_offset, attach_to=world.get_spectator())
    camera.listen((lambda image: enqueue_image(image)))
    return camera

def init_connection():
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM) # TCP
    sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
    sock.bind((TCP_IP, TCP_PORT))
    print("socket bound")
    sock.listen(1) #one client at a time
    sock.settimeout(0.5)
    print("socket listening")
    return sock

# Get CARLA spectator camera image and send over connection
def enqueue_image(image):
    global IMAGE_QUEUE
    global LAST_FRAME_TIME
    if CONNECTION != None:
        if (time() - LAST_FRAME_TIME) > 1.0/FPS:
            IMAGE_QUEUE.put(image)
            LAST_FRAME_TIME = time()

def tcp_send(image):
    global CONNECTION
    message = image.raw_data
    start_ptr = 0
    chunk_size_bytes = 65000
    # send metadata
    START_MSG_TYPE = 0
    CHUNK_MSG_TYPE = 1
    END_MSG_TYPE = 2
    CONNECTION.sendall(START_MSG_TYPE.to_bytes(4, 'little') + image.height.to_bytes(4, 'little') + image.width.to_bytes(4, 'little') + len(message).to_bytes(4, 'little'))
    while start_ptr < len(message):
        end_ptr = min(len(message), start_ptr + chunk_size_bytes)
        message_chunk = message[start_ptr:end_ptr]
        message_chunk = CHUNK_MSG_TYPE.to_bytes(4, 'little') + len(message_chunk).to_bytes(4, 'little') + message_chunk
        # msg chunks
        CONNECTION.sendall(message_chunk)
        start_ptr = end_ptr
    # end msg
    CONNECTION.sendall(END_MSG_TYPE.to_bytes(4, 'little'))

def main():
    """Sends CARLA camera images to specified destination socket over UDP"""
    global CONNECTION
    global SOCK
    global IMAGE_QUEUE
    try:
        camera = init_carla_camera()
        SOCK = init_connection()
        print(SOCK)
        while True:
            try:
                if CONNECTION == None:
                    CONNECTION, addr = SOCK.accept()
                    print("Connected!")
                else:
                    if not IMAGE_QUEUE.empty():
                        #if time()-enqueue_time < 0.00001:
                        tcp_send(IMAGE_QUEUE.get())
                        #print("Client connected!")
                        #print("Send takes: " + str(time()-st))
            except socket.timeout:
                pass
            except Exception as e:
                print(e)
                if CONNECTION != None:
                    CONNECTION.close()
                CONNECTION = None
    except KeyboardInterrupt as e:
        print("Exiting...")
    finally:
        if CONNECTION != None:
            CONNECTION.close()
        if SOCK != None:
            SOCK.close()
        if camera != None:
            camera.destroy()
        print("Done.")

if __name__ == "__main__":
    main()
