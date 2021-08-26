# Uses TCP

import carla
from time import time, sleep
#import binascii
import base64
import _thread

import socket
import struct
import queue

TCP_IP = "127.0.0.1"
TCP_PORT = 8892

CARLA_IP = "127.0.0.1"
CARLA_PORT = 2000

CONNECTION = None
SOCK = None

MSG_SIZE_BYTES = 6 * 4 # six floats, four bytes each

def init_carla_spectator():
    # Set up CARLA client
    carla_client = carla.Client(CARLA_IP, CARLA_PORT)
    carla_client.set_timeout(2.0)
    spectator = carla_client.get_world().get_spectator()
    return spectator

def init_connection():
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM) # TCP
    sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
    sock.bind((TCP_IP, TCP_PORT))
    print("socket bound")
    sock.listen(1) #one client at a time
    sock.settimeout(0.5)
    print("socket listening")
    return sock


# expects six floats
# xrshark_x, xrshark_y, xrshark_z, xrshark_roll, xrshark_pitch, xrshark_yaw
def tcp_recv(spectator):
    #st = time()
    # chunks = []
    # if CONNECTION != None:
    #     bytes_recd = 0
    #     while bytes_recd < MSG_SIZE_BYTES:
    #         chunk = CONNECTION.recv(min(MSG_SIZE_BYTES - bytes_recd, 2048))
    #         if chunk == b'':
    #             raise RuntimeError("socket connection broken")
    #         chunks.append(chunk)
    #         bytes_recd = bytes_recd + len(chunk)
    # binary_data = b''.join(chunks)

    binary_data = CONNECTION.recv(MSG_SIZE_BYTES)
    #print("Received data in {} seconds".format(time()-st))


    # unpack data
    #st = time()
    xrshark_x, xrshark_y, xrshark_z, xrshark_roll, xrshark_pitch, xrshark_yaw = struct.unpack('ffffff', binary_data)
    #print(nums)
    #print("Unpacked data in {} seconds".format(time()-st))

    # set carla camera pos
    # location = carla.Location(xrshark_z,
    #                           xrshark_x,
    #                           xrshark_y)
    # rotation = carla.Rotation(360-xrshark_roll,
    #                           xrshark_pitch,
    #                           xrshark_yaw)
    #st = time()
    new_transform = carla.Transform(carla.Location(xrshark_z,
                                                    xrshark_x,
                                                    xrshark_y),
                                    carla.Rotation(360-xrshark_roll,
                                                    xrshark_pitch,
                                                    xrshark_yaw))
    spectator.set_transform(new_transform)
    #print("Set camera in {} seconds".format(time()-st))

def main():
    """Sends CARLA camera images to specified destination socket over UDP"""
    global CONNECTION
    global SOCK
    global IMAGE_QUEUE
    try:
        spectator = init_carla_spectator()
        SOCK = init_connection()
        print(SOCK)
        while True:
            try:
                if CONNECTION == None:
                    CONNECTION, addr = SOCK.accept()
                    print("Connected!")
                else:
                    #if time()-enqueue_time < 0.00001:
                    tcp_recv(spectator)
                    #print(data)
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
        print("Done.")

if __name__ == "__main__":
    main()
