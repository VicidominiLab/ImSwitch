from typing import List, Tuple, Optional, Dict
import numpy as np
from imswitch.imcommon.model import initLogger
from .DetectorManager import (
    DetectorManager, DetectorAction, DetectorNumberParameter,
    DetectorParameter, DetectorBooleanParameter, DetectorListParameter
)

class BrightEyesMCSManager(DetectorManager):
    """
    Manages the BrightEyesMCS camera system.
    """

    def __init__(self, detectorInfo, name, **_lowLevelManagers):
        """
        Initializes the BrightEyesMCSManager object.

        Parameters:
        detectorInfo: Information about the detector.
        name (str): The name of the manager.
        _lowLevelManagers: Additional low-level managers.
        """
        self.__logger = initLogger(self, instanceName=name)

        # Extract host and port information from detector properties
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
        }

        # Prepare actions
        actions = {
            'More properties': DetectorAction(group='Misc', func=self._camera.openPropertiesGUI),
            'Force STOP': DetectorAction(group='Misc', func=self._camera.stop_live)
        }

        super().__init__(detectorInfo, name, fullShape=fullShape, supportedBinnings=[1],
                         model=model, parameters=parameters, actions=actions, croppable=True)

    @property
    def pixelSizeUm(self) -> List[int]:
        """
        Returns the pixel size in micrometers.

        Returns:
        List[int]: A list of pixel sizes in micrometers.
        """
        return [1, 1, 1]

    def crop(self, hpos: int, vpos: int, hsize: int, vsize: int) -> None:
        """
        Crops the camera frame.

        Parameters:
        hpos (int): Horizontal position of the crop.
        vpos (int): Vertical position of the crop.
        hsize (int): Horizontal size of the crop.
        vsize (int): Vertical size of the crop.
        """
        pass

    def getLatestFrame(self) -> np.ndarray:
        """
        Retrieves the latest frame from the camera.

        Returns:
        numpy.ndarray: The latest frame.
        """
        return self._camera.getLast()

    def getChunk(self):
        """
        Retrieves the latest chunk of data from the camera.

        Returns:
        numpy.ndarray: The latest chunk of data.
        """
        return self._camera.getLastChunk()

    def flushBuffers(self) -> None:
        """
        Flushes the camera buffers.
        """
        pass

    def startAcquisition(self) -> None:
        """
        Starts data acquisition from the camera.
        """
        if not self._running:
            self._camera.start_live()
            self._running = True
            self.__logger.debug('startlive')

    def stopAcquisition(self) -> None:
        """
        Stops data acquisition from the camera.
        """
        if self._running:
            self._running = False
            self._camera.suspend_live()
            self.__logger.debug('suspendlive')

    def setParameter(self, name, value):
        """
        Sets a parameter value and returns the value.

        Parameters:
        name (str): The name of the parameter.
        value (any): The value to set.

        Returns:
        any: The set parameter value.

        Raises:
        AttributeError: If the parameter does not exist.
        """
        super().setParameter(name, value)

        if name not in self._DetectorManager__parameters:
            raise AttributeError(f'Non-existent parameter "{name}" specified')

        value = self._camera.setPropertyValue(name, value)
        return value

    def getParameter(self, name):
        """
        Gets a parameter value and returns the value.

        Parameters:
        name (str): The name of the parameter.

        Returns:
        any: The parameter value.

        Raises:
        AttributeError: If the parameter does not exist.
        """
        if name not in self._parameters:
            raise AttributeError(f'Non-existent parameter "{name}" specified')

    def stopAcquisitionForROIChange(self):
        """
        Stops data acquisition to change the region of interest (ROI).
        """
        self._running = False
        self._camera.stop_live()
        self.__logger.debug('stoplive')

    def finalize(self) -> None:
        """
        Finalizes and safely disconnects the camera.
        """
        super().finalize()
        self.__logger.debug('Safely disconnecting the camera...')
        self._camera.close()

    def openPropertiesDialog(self):
        """
        Opens the properties dialog for the camera.
        """
        self._camera.openPropertiesGUI()

    def closeEvent(self):
        """
        Closes the camera connection.
        """
        self._camera.close()
