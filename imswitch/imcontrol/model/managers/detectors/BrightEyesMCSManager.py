from typing import List, Tuple, Optional, Dict

import numpy as np

from imswitch.imcommon.model import initLogger
#from imswitch.imcontrol.model.interfaces.BrightEyesMCScamera import BrightEyesMCSCamera
from .DetectorManager import (DetectorManager, DetectorAction, DetectorNumberParameter,
                              DetectorParameter, DetectorBooleanParameter, DetectorListParameter)


# class BrightEyesMCSManager(DetectorManager):
#
#     def __init__(self, detectorInfo, name, **_lowLevelManagers):
#         self.__logger = initLogger(self, instanceName=name)
#         self._camera = self._getBrightEyesMCSobj(host, port)
#         pass
#
#     @property
#     def pixelSizeUm(self) -> List[int]:
#         pass
#
#     def crop(self, hpos: int, vpos: int, hsize: int, vsize: int) -> None:
#         pass
#
#     def getLatestFrame(self) -> np.ndarray:
#         pass
#
#     def getChunk(self) -> np.ndarray:
#         pass
#
#     def flushBuffers(self) -> None:
#         pass
#
#     def startAcquisition(self) -> None:
#         pass
#
#     def stopAcquisition(self) -> None:
#         pass


class BrightEyesMCSManager(DetectorManager):
    """ DetectorManager that deals with TheImagingSource cameras and the
    parameters for frame extraction from them.

    Manager properties:

    - ``cameraListIndex`` -- the camera's index in the Allied Vision camera list (list
      indexing starts at 0); set this string to an invalid value, e.g. the
      string "mock" to load a mocker
    - ``picamera`` -- dictionary of Allied Vision camera properties
    """

    def __init__(self, detectorInfo, name, **_lowLevelManagers):
        self.__logger = initLogger(self, instanceName=name)

        host = detectorInfo.managerProperties['cameraHost']
        port = detectorInfo.managerProperties['cameraPort']

        from imswitch.imcontrol.model.interfaces.BrightEyesMCScamera import BrightEyesMCSCamera
        self.__logger.debug(f'Trying to initialize BrightEyesMCSCamera {host}')
        camera = BrightEyesMCSCamera(host, port)
        self.__logger.info(f'Initialized camera, model: {camera.model}')
        self._camera = camera

        model = self._camera.model
        self._running = False
        self._adjustingParameters = False

        fullShape = (self._camera.getPropertyValue('image_width'),
                     self._camera.getPropertyValue('image_height'))



        self.crop(hpos=0, vpos=0, hsize=fullShape[0], vsize=fullShape[1])

        # Prepare parameters
        parameters = {
            'fcs': DetectorBooleanParameter(group='Misc', value=False, editable=True),
            'circular_active': DetectorBooleanParameter(group='Misc', value=False, editable=True),
            'offset_x_um': DetectorNumberParameter(group='Position', value=0.0, valueUnits='um', editable=True),
            'offset_y_um': DetectorNumberParameter(group='Position', value=0.0, valueUnits='um', editable=True),
            'offset_z_um': DetectorNumberParameter(group='Position', value=0.0, valueUnits='um', editable=True),
            'range_x': DetectorNumberParameter(group='Position', value=200.0, valueUnits='um', editable=True),
            'range_y': DetectorNumberParameter(group='Position', value=200.0, valueUnits='um', editable=True),
            'range_z': DetectorNumberParameter(group='Position', value=0.0, valueUnits='um', editable=True),
            'time_resolution': DetectorNumberParameter(group='Timing', value=1.0, valueUnits='us', editable=True),
            'timebin_per_pixel': DetectorNumberParameter(group='Timing', value=10, valueUnits='', editable=True),
            'nx': DetectorNumberParameter(group='Dimensions', value=300, valueUnits='', editable=True),
            'ny': DetectorNumberParameter(group='Dimensions', value=300, valueUnits='', editable=True),
            'nframe': DetectorNumberParameter(group='Dimensions', value=1, valueUnits='', editable=True),
            'nrep': DetectorNumberParameter(group='Dimensions', value=1, valueUnits='', editable=True),
            'calib_x': DetectorNumberParameter(group='Misc', value=8.89999, valueUnits='um/V', editable=True),
            'calib_y': DetectorNumberParameter(group='Misc', value=8.89999, valueUnits='um/V', editable=True),
            'calib_z': DetectorNumberParameter(group='Misc', value=10, valueUnits='um/V', editable=True),

            'preview_autoscale': DetectorBooleanParameter(group='Misc', value=True, editable=True),

            'projection': DetectorListParameter(group='Misc', value="xy", options=["xy","yx","zx"], editable=True),
            'preview_channel': DetectorListParameter(group='Misc', value="Sum", options=["Sum", "1", "12", "24"], editable=True),

            'fingerprint_visualization': DetectorListParameter(group='Misc', value="Cumulative", options=["Cumulative"], editable=True),

            'fingerprint_autoscale': DetectorBooleanParameter(group='Misc', value=True, editable=True),
            'ratio_xy_locked': DetectorBooleanParameter(group='Misc', value=True, editable=True),
            'waitOnlyFirstTime': DetectorBooleanParameter(group='Misc', value=False, editable=True),

            'waitAfterFrame': DetectorNumberParameter(group='Misc', value=0.0, valueUnits='um', editable=True),

            'laserOffAfterMeas': DetectorBooleanParameter(group='Misc', value=False, editable=True),

            'ch_preview': DetectorListParameter(group='Misc', value="Sum", options=["Sum", "1", "12", "24"], editable=True),



            # "\"defaultFolder\": \"C:/Users/Developer/Documents/Data\", "
            # "\"spad_number_of_channels\": \"25\","
            # " \"comment\":"
            # " \"\", \"bitFile\": \"bitfiles/SingleBoard-USB7856R.lvbitx\""

            }

        # Prepare actions
        actions = {
            'More properties': DetectorAction(group='Misc',
                                              func=self._camera.openPropertiesGUI)
        }

        super().__init__(detectorInfo, name, fullShape=fullShape, supportedBinnings=[1],
                         model=model, parameters=parameters, actions=actions, croppable=True)

    def getLatestFrame(self, is_save=False):
        if is_save:
            return self._camera.getLastChunk()
        else:
            return self._camera.getLast()

    def setParameter(self, name, value):
        """Sets a parameter value and returns the value.
        If the parameter doesn't exist, i.e. the parameters field doesn't
        contain a key with the specified parameter name, an error will be
        raised."""

        super().setParameter(name, value)

        if name not in self._DetectorManager__parameters:
            raise AttributeError(f'Non-existent parameter "{name}" specified')

        value = self._camera.setPropertyValue(name, value)
        return value

    def getParameter(self, name):
        """Gets a parameter value and returns the value.
        If the parameter doesn't exist, i.e. the parameters field doesn't
        contain a key with the specified parameter name, an error will be
        raised."""

        if name not in self._parameters:
            raise AttributeError(f'Non-existent parameter "{name}" specified')

        value = self._camera.getPropertyValue(name)
        return value

    def setBinning(self, binning):
        super().setBinning(binning) 
        

    def getChunk(self):
        return self._camera.getLastChunk()

    def flushBuffers(self):
        pass

    def startAcquisition(self):
        if not self._running:
            self._camera.start_live()
            self._running = True
            self.__logger.debug('startlive')

    def stopAcquisition(self):
        if self._running:
            self._running = False
            self._camera.suspend_live()
            self.__logger.debug('suspendlive')

    def stopAcquisitionForROIChange(self):
        self._running = False
        self._camera.stop_live()
        self.__logger.debug('stoplive')

    def finalize(self) -> None:
        super().finalize()
        self.__logger.debug('Safely disconnecting the camera...')
        self._camera.close()

    @property
    def pixelSizeUm(self):
        return [1, 1, 1]

    def crop(self, hpos, vpos, hsize, vsize):
        if(0):
            def cropAction():
                # self.__logger.debug(
                #     f'{self._camera.model}: crop frame to {hsize}x{vsize} at {hpos},{vpos}.'
                # )
                self._camera.setROI(hpos, vpos, hsize, vsize)

            self._performSafeCameraAction(cropAction)
            # TODO: unsure if frameStart is needed? Try without.
            # This should be the only place where self.frameStart is changed
            self._frameStart = (hpos, vpos)
            # Only place self.shapes is changed
            self._shape = (hsize, vsize)
        # TODO: Reimplement

    def _performSafeCameraAction(self, function):
        """ This method is used to change those camera properties that need
        the camera to be idle to be able to be adjusted.
        """
        self._adjustingParameters = True
        wasrunning = self._running
        self.stopAcquisitionForROIChange()
        function()
        if wasrunning:
            self.startAcquisition()
        self._adjustingParameters = False

    def openPropertiesDialog(self):
        self._camera.openPropertiesGUI()

    def closeEvent(self):
        self._camera.close()

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
