from imswitch.imcommon.model import initLogger
from imswitch.imcontrol.model.interfaces.restapicamera import RestPiCamera

from PIL import Image
import io
import requests
import time
import cv2
import numpy as np
from threading import Thread
import urllib
import json
from io import BytesIO


class BrightEyesMCSCamera:
    def __init__(self, host, port):
        """
        Initializes the BrightEyesMCSCamera object with the given host and port.

        Parameters:
        host (str): The host address of the camera.
        port (int): The port number of the camera.
        """
        super().__init__()
        self.__logger = initLogger(self, tryInheritParent=True)
        self.host = host
        self.port = port

        # Camera parameters and properties
        self.model = "BrightEyesMCSCamera"
        self.shape = (0, 0)
        self.framesize = 100
        self.exposure_time = 0
        self.analog_gain = 0
        self.internal_property = {
            "image_width": 2000,
            "image_height": 2000
        }

        # Initialize camera network interface
        self.camera = BrightEyesMCSNetwork(self.host, self.port, is_debug=True)
        self.frame = np.zeros((self.internal_property["image_height"], self.internal_property["image_width"]))

    def put_frame(self, frame):
        """
        Updates the current frame with the given frame and resizes it to the camera's image dimensions.

        Parameters:
        frame (numpy.ndarray): The frame to update.
        """
        self.frame = frame
        self.frame = cv2.resize(self.frame, (self.internal_property["image_width"], self.internal_property["image_height"]))
        return frame

    def start_live(self):
        """
        Sends a command to start the live preview on the camera.
        """
        self.camera.send_command("preview")

    def stop_live(self):
        """
        Sends a command to stop the live preview on the camera.
        """
        self.camera.send_command("stop")

    def suspend_live(self):
        """
        Sends a command to stop the live preview on the camera (alias for stop_live).
        """
        self.camera.send_command("stop")

    def prepare_live(self):
        """
        Placeholder for preparing the live view (not implemented).
        """
        pass

    def close(self):
        """
        Placeholder for closing the camera connection (not implemented).
        """
        pass

    def set_exposure_time(self, exposure_time):
        """
        Sets the exposure time of the camera.

        Parameters:
        exposure_time (int): The desired exposure time.
        """
        self.exposure_time = exposure_time
        self.camera.setExposureTime(self.exposure_time)

    def set_analog_gain(self, analog_gain):
        """
        Sets the analog gain of the camera.

        Parameters:
        analog_gain (int): The desired analog gain.
        """
        self.analog_gain = analog_gain
        self.camera.setGain(self.analog_gain)

    def set_framesize(self, framesize):
        """
        Sets the frame size of the camera.

        Parameters:
        framesize (int): The desired frame size.
        """
        self.framesize = framesize
        self.camera.setFrameSize(self.framesize)

    def getLast(self):
        """
        Retrieves the last frame from the camera's preview.

        Returns:
        numpy.ndarray: The last frame.
        """
        self.frame = self.camera.download_array("preview")
        return self.frame

    def getLastChunk(self):
        """
        Retrieves the last chunk of data from the camera's preview.

        Returns:
        numpy.ndarray: The last chunk of data.
        """
        return self.camera.download_array("preview")

    def setROI(self, hpos, vpos, hsize, vsize):
        """
        Sets the Region of Interest (ROI) for the camera.

        Parameters:
        hpos (int): The horizontal position of the ROI.
        vpos (int): The vertical position of the ROI.
        hsize (int): The horizontal size of the ROI.
        vsize (int): The vertical size of the ROI.
        """
        hsize = max(hsize, 256)  # minimum ROI size
        vsize = max(vsize, 24)  # minimum ROI size

    def setPropertyValue(self, property_name, property_value):
        """
        Sets the property value for the camera.

        Parameters:
        property_name (str): The name of the property.
        property_value (any): The value of the property.

        Returns:
        any: The set property value.
        """
        self.camera.set_gui_data({property_name: property_value})
        return property_value

    def getPropertyValue(self, property_name):
        """
        Retrieves the property value for the given property name.

        Parameters:
        property_name (str): The name of the property.

        Returns:
        any: The value of the property.
        """
        if property_name in self.internal_property:
            return self.internal_property[property_name]
        else:
            try:
                property_value = self.camera.get_gui_data(property_name)
            except Exception as e:
                print(e)
        return property_value

    def openPropertiesGUI(self):
        """
        Placeholder for opening the properties GUI (not implemented).
        """
        pass


class BrightEyesMCSNetwork(object):

    def __init__(self, host="127.0.0.1", port=8000, is_debug=True):
        """
        Initializes the BrightEyesMCSNetwork object with the given host, port, and debug flag.

        Parameters:
        host (str): The host address of the network.
        port (int): The port number of the network.
        is_debug (bool): Flag indicating if debug mode is enabled.
        """
        self.base_url = f"http://{host}:{port}"
        self.debug = is_debug

    def get_param(self, param):
        """
        Retrieves the parameter from the GUI data.

        Parameters:
        param (str): The parameter to retrieve.
        """
        self.get_gui_data()

    def get_root(self):
        """
        Retrieves the root information from the server.

        Returns:
        dict: The root information.
        """
        response = requests.get(f"{self.base_url}/")
        return response.json()

    def get_gui_data(self, item=None):
        """
        Retrieves the GUI data from the server.

        Parameters:
        item (str, optional): Specific item to retrieve from the GUI data.

        Returns:
        dict: The GUI data.
        """
        url = f"{self.base_url}/gui/"
        if item:
            url += f"{item}"
        response = requests.get(url)
        return json.loads(response.json())

    def send_command(self, command):
        """
        Sends a command to the server.

        Parameters:
        command (str): The command to send.

        Returns:
        str: The response from the server.
        """
        url = f"{self.base_url}/cmd/{command}"
        response = requests.get(url)
        return response.text

    def set_gui_data(self, data):
        """
        Sets the GUI data on the server.

        Parameters:
        data (dict): The data to set.

        Returns:
        str: The response from the server.
        """
        url = f"{self.base_url}/set"
        headers = {"Content-Type": "application/json"}
        d = json.dumps(data)
        print("data=json.dumps(data)", d)
        response = requests.put(url, data=d, headers=headers)
        return response.text

    def upload_array(self, array, shape, dtype="float64"):
        """
        Uploads an array to the server.

        Parameters:
        array (numpy.ndarray): The array to upload.
        shape (tuple): The shape of the array.
        dtype (str, optional): The data type of the array (default is "float64").

        Returns:
        dict: The response from the server.
        """
        url = f"{self.base_url}/array/"
        files = {'file': ('array', array.tobytes(), 'application/octet-stream')}
        data = {'shape': ','.join(map(str, shape)), 'dtype': dtype}
        response = requests.post(url, files=files, data=data)
        return response.json()

    def download_image(self, image_type):
        """
        Downloads an image from the server.

        Parameters:
        image_type (str): The type of image to download ("preview" or "fingerprint").

        Returns:
        bytes: The downloaded image content.

        Raises:
        ValueError: If the image type is invalid.
        """
        if image_type not in ["preview", "fingerprint"]:
            raise ValueError("Invalid image type. Must be 'preview' or 'fingerprint'.")
        url = f"{self.base_url}/{image_type}.png"
        response = requests.get(url)
        if response.status_code == 200:
            return response.content
        else:
            response.raise_for_status()

    def download_array(self, array_type):
        """
        Downloads an array from the server.

        Parameters:
        array_type (str): The type of array to download ("preview" or "fingerprint").

        Returns:
        numpy.ndarray: The downloaded array.

        Raises:
        ValueError: If the array type is invalid.
        """
        if array_type not in ["preview", "fingerprint"]:
            raise ValueError("Invalid array type. Must be 'preview' or 'fingerprint'.")
        url = f"{self.base_url}/{array_type}.np"
        response = requests.get(url, stream=True)
        if response.status_code == 200:
            array_bytes = BytesIO(response.content)
            shape = tuple(map(int, response.headers["X-Shape"].split(',')))
            dtype = response.headers["X-Dtype"]
            np_array = np.frombuffer(array_bytes.getvalue(), dtype=dtype).reshape(shape)
            print(np_array)
            return np_array
        else:
            response.raise_for_status()


# Copyright (C) ImSwitch developers 2021
# This file is part of ImSwitch.
#
# ImSwitch is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# ImSwitch is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.
