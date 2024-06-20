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
import requests
import json
import numpy as np
from io import BytesIO


class BrightEyesMCSCamera:
    def __init__(self, host, port):
        super().__init__()
        self.__logger = initLogger(self, tryInheritParent=True)
        # URL for the remote camera
        self.host = host
        self.port = port

        # many to be purged
        self.model = "BrightEyesMCSCamera"
        self.shape = (0, 0)

        # camera parameters
        self.framesize = 100
        self.exposure_time = 0
        self.analog_gain = 0

        self.internal_property = {
             "image_width" : 2000,
             "image_height" : 2000
        }
        #%% starting the camera thread

        self.camera = BrightEyesMCSNetwork(self.host, self.port, is_debug=True)

        self.frame = np.zeros((self.internal_property["image_height"], self.internal_property["image_width"]))

    def put_frame(self, frame):
        self.frame = frame
        self.frame = cv2.resize(self.frame, (self.internal_property["image_width"], self.internal_property["image_height"]))
        return frame

    def start_live(self):
        # most likely the camera already runs
        self.camera.send_command("preview")

    def stop_live(self):
        self.camera.send_command("stop")

    def suspend_live(self):
        self.camera.send_command("stop")

    def prepare_live(self):
        pass

    def close(self):
        pass  #TODO: self.camera.close()

    def set_exposure_time(self, exposure_time):
        self.exposure_time = exposure_time
        self.camera.setExposureTime(self.exposure_time)

    def set_analog_gain(self, analog_gain):
        self.analog_gain = analog_gain
        self.camera.setGain(self.analog_gain)

    def set_framesize(self, framesize):
        self.framesize = framesize
        self.camera.setFrameSize(self.framesize)

    def set_ledIntensity(self, ledIntensity):
        self.ledIntensity = ledIntensity
        self.camera.setLed(self.ledIntensity)

    def set_pixel_format(self, format):
        pass

    def getLast(self):
        # get frame and save
        self.frame =  self.camera.download_array("preview")
        return self.frame

    def getLastChunk(self):
        return  self.camera.download_array("preview")

    def setROI(self, hpos, vpos, hsize, vsize):
        hsize = max(hsize, 256)  # minimum ROI size
        vsize = max(vsize, 24)  # minimum ROI size
        pass
        # self.__logger.debug(
        #     f'{self.model}: setROI started with {hsize}x{vsize} at {hpos},{vpos}.'
        # )
        #self.camera.setROI(vpos, hpos, vsize, hsize)

    def setPropertyValue(self, property_name, property_value):
        self.camera.set_gui_data({property_name: property_value})
        # self.__logger.warning(f'Property {property_name} does not exist')
        # return False
        return property_value

    def getPropertyValue(self, property_name):
        if property_name in self.internal_property:
            return self.internal_property[property_name]
        else:
            try:
                property_value = self.camera.get_gui_data(property_name)
            except e as Exception:
                print(e)
        # Check if the property exists.
        # if property_name == "gain":
        #     property_value = self.camera.gain
        # elif property_name == "exposure":
        #     property_value = self.camera.exposuretime
        # elif property_name == "led":
        #     property_value = self.camera.exposuretime
        # elif property_name == "framesize":
        #     property_value = self.camera.framesize
        # elif property_name == "image_width":
        #     property_value = self.camera.SensorWidth
        # elif property_name == "image_height":
        #     property_value = self.camera.SensorHeight
        # else:
        #     self.__logger.warning(f'Property {property_name} does not exist')
        #     return False
        return property_value

    def openPropertiesGUI(self):
        pass


class BrightEyesMCSNetwork(object):

    def __init__(self, host="127.0.0.1", port=8000, is_debug=True):
        self.base_url = f"http://{host}:{port}"
        self.debug = is_debug

    def get_param(self, param):
        self.get_gui_data()

    def get_root(self):
        response = requests.get(f"{self.base_url}/")
        return response.json()

    def get_gui_data(self, item=None):
        url = f"{self.base_url}/gui/"
        if item:
            url += f"{item}"
        response = requests.get(url)
        return json.loads(response.json())

    def send_command(self, command):
        url = f"{self.base_url}/cmd/{command}"
        response = requests.get(url)
        return response.text

    def set_gui_data(self, data):
        url = f"{self.base_url}/set"
        headers = {"Content-Type": "application/json"}
        d=json.dumps(data)
        print("data=json.dumps(data)", d)
        response = requests.put(url, data=d, headers=headers)
        return response.text

    def upload_array(self, array, shape, dtype="float64"):
        url = f"{self.base_url}/array/"
        files = {'file': ('array', array.tobytes(), 'application/octet-stream')}
        data = {'shape': ','.join(map(str, shape)), 'dtype': dtype}
        response = requests.post(url, files=files, data=data)
        return response.json()

    def download_image(self, image_type):
        if image_type not in ["preview", "fingerprint"]:
            raise ValueError("Invalid image type. Must be 'preview' or 'fingerprint'.")
        url = f"{self.base_url}/{image_type}.png"
        response = requests.get(url)
        if response.status_code == 200:
            return response.content
        else:
            response.raise_for_status()

    def download_array(self, array_type):
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

# Example usage:
# client = FastAPIClient()
# print(client.get_root())
# print(client.get_gui_data('all'))
# client.send_command('preview')
# client.set_gui_data({"key": "value"})
# array = np.array([[1, 2], [3, 4]], dtype="float64")
# client.upload_array(array, array.shape, dtype=array.dtype.name)
# image_data = client.download_image('preview')
# with open("preview.png", "wb") as f:
#     f.write(image_data)
# array_data = client.download_array('preview')
# print(array_data)


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
