Scripts for synchronizing CARLA and XRShark.

# Requirements
These instructions were tested on the following system configuration:
- HP Omen gaming laptop
  - Operating System: Windows 10 Home
  - Processor: i7 @ 2.20 Ghz,
  - Memory: 32 GB RAM,
  - Graphics Card: NVIDIA GeForce GTX 1070 Max-Q

You will need the following programs:
- CARLA: Tested with version 0.9.10
- Unity: Version 2019.4.5f1 required
- Unity project: XRShark ERA Network Viz. Currently you must be added as a team member to the Unity project and download it through Unity collaboration services.
- Python scripts (in this repo):
  - carla_xrshark_sync.py: Python script for synchronizing the camera positions.
  - carla_camera_capture.py: Python script for sending the current CARLA camera image to XRShark

# Python Script Setup
To run the scripts, you will need to make sure 1) that the CARLA Python egg is on your system PATH, 2) that you are using the version of Python that corresponds to the egg version, and 3) you have all dependencies installed.

### Setting up the PATH
These scripts simply `import carla` and do not manually search for the CARLA egg like many of the scripts in CARLA's examples folder. This is so that they can be run from any folder. I added the following to my system PATH so all scripts can find the CARLA Python egg file no matter where they're run from:

```
C:\Users\lab11\CARLA\CARLA_0.9.10\WindowsNoEditor\PythonAPI\carla\dist\carla-0.9.10-py3.7-win-amd64.egg
```

### Using the right version of Python
Because CARLA's egg file is for 3.7 but my system's Python version is 3.9, I downloaded and built a separate Python 3.7 binary. I run that Python 3.7 binary in my xrshark-era-scripts folder with virtualenv:

```
> cd <folder where I'm putting my scripts, e.g. xrshark-era-scripts>
> C:\Users\lab11\Python-3.7.11\PCbuild\amd64\python.exe -m venv .
```

This tells virtualenv to create a new virtual environment in my xrshark-era-scripts folder where the `python` command corresponds to the Python 3.7 binary, and any `pip install` commands will just be to this virtual Python 3.7 environment, and not to the system Python.

The command will also create a Scripts folder and some other folders for virtualenv in that directory. To activate the virtual environment (such as when opening a new command prompt), run:  
```
> Scripts\activate.bat
```
You can check which version of Python is currently in use with the command `where python`. After running activate.bat, you should see the python.exe in your Scripts folder at the top.

## Installing Dependencies
Once you are using the right version of Python, run `python -m pip install paho-mqtt` to install the MQTT libraries.

# Running
- Open the ERA XRShark Unity project. Make sure XRScene is the open scene in the Hierarchy tab.
- Start CARLA. Start the two scripts. (I usually do this in three separate command windows, because you have to ctrl-c the two scripts to exit.)
- Push the play button in the XRShark project.

You should now have CARLA and XRShark synced! If you want XRShark to display network host markers and packet data, refer to the [XRShark Interface](https://docs.google.com/document/d/1FLnxK0fSAxS3ziwpZ2-dLTjNdDfohzlo00dI5aq-SIc/edit?usp=sharing).
