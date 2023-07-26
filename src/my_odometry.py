from typing import ClassVar, Optional, Dict, Sequence, Any, Mapping, Tuple

from typing_extensions import Self

from viam.components.camera import Camera
from viam.components.movement_sensor.movement_sensor import MovementSensor
from viam.resource.base import ResourceBase
from viam.proto.app.robot import ComponentConfig

from viam.gen.common.v1.common_pb2 import Orientation, Vector3, GeoPoint
from viam.proto.common import ResourceName
from viam.resource.base import ResourceBase
from viam.module.types import Reconfigurable
from viam.resource.types import Model, ModelFamily

from .visual_odometry import ORBVisualOdometry
from .utils import get_camera_matrix, get_distort_param
from threading import Thread

class MyOdometry(MovementSensor, Reconfigurable):
    MODEL: ClassVar[Model] = Model(ModelFamily("viam", "opencv"), "visual_odometry_orb")
    # cam: Camera
    visual_odometry: ORBVisualOdometry

    @classmethod
    def new(cls, config: ComponentConfig, dependencies: Mapping[ResourceName, ResourceBase]) -> Self:
        movement_sensor = cls(config.name)
        movement_sensor.reconfigure(config, dependencies)
        return movement_sensor

    # Validate JSON Configuration

    @classmethod
    def validate_config(cls, config: ComponentConfig) -> Sequence[str]:
        '''
        Returns the dependency
        '''
        camera_name = config.attributes.fields["camera_name"].string_value
        if camera_name == "":
            raise Exception("A 'camera_name' attribute is required for a visual odometry movement sensor")
        #TODO: check that camera has a matrix
        return [camera_name]

    def reconfigure(self, config: ComponentConfig, dependencies: Mapping[ResourceName, ResourceBase]):

        camera_name = config.attributes.fields["camera_name"].string_value
        camera = dependencies[Camera.get_resource_name(camera_name)]
        # TODO:call get properties here to get the intrinsics and throw an error
        # props = await camera.get_properties()
        camera_matrix = self.get_camera_matrix()
        # distortion_parameters = self.get_distortion_parameters_from_properties(props)
        distortion_parameters = self.get_distortion_parameters()
        
        def get_attribute_from_config(attribute_name:str,  default):
            if attribute_name not in config.attributes.fields:
                return default
            
            type_default = type(default)
            
            if type_default == int:
                return int(config.attributes.fields[attribute_name].number_value)
            elif type_default == float:
                return config.attributes.fields[attribute_name].number_value
            elif type_default == str:
                return config.attributes.fields[attribute_name].string_value

        time_between_frames_s = get_attribute_from_config("time_between_frames_s", .1)
        orb_n_features = get_attribute_from_config("orb_n_features", 10000)
        orb_edge_threshold = get_attribute_from_config("orb_edge_threshold", 31)
        orb_patch_size = get_attribute_from_config("orb_patch_size", 31)
        orb_n_levels = get_attribute_from_config("orb_n_levels", 8)
        orb_first_level = get_attribute_from_config("orb_first_level", 0)
        orb_fast_threshold = get_attribute_from_config("orb_fast_threshold", 20)
        orb_scale_factor = get_attribute_from_config("orb_scale_factor", 1.2)
        orb_WTA_K = get_attribute_from_config("orb_WTA_K", 2)
        matcher = get_attribute_from_config("matcher", "flann")
        lowe_ratio_threshold = get_attribute_from_config("lowe_ratio_threshold", .8)
        ransac_prob = get_attribute_from_config("ransac_prob", .99)
        ransac_threshold_px = get_attribute_from_config("ransac_threshold_px", .5)
        
        self.visual_odometry = ORBVisualOdometry(cam= camera,
                                                camera_matrix = camera_matrix,
                                                time_between_frames = time_between_frames_s,
                                                distortion_param = distortion_parameters,
                                                n_features = orb_n_features,
                                                edge_threshold = orb_edge_threshold,
                                                patch_size=orb_patch_size,
                                                n_levels = orb_n_levels, 
                                                first_level=orb_first_level, 
                                                fast_threshold=orb_fast_threshold,
                                                scale_factor=orb_scale_factor,
                                                WTA_K=orb_WTA_K,
                                                matcher= matcher,
                                                lowe_ratio_threshold = lowe_ratio_threshold,
                                                ransac_prob = ransac_prob,
                                                ransac_threshold = ransac_threshold_px)
        
        
    async def get_position(self, extra: Optional[Dict[str, Any]] = None, timeout: Optional[float] = None,
                           **kwargs) -> Tuple[GeoPoint, float]:
        pass

    async def get_linear_velocity(self, extra: Optional[Dict[str, Any]] = None, timeout: Optional[float] = None,
                                  **kwargs) -> Vector3:
        v_x, v_y, v_z = await self.visual_odometry.get_linear_velocity()
        return Vector3(x=v_x, y=v_y, z=v_z)

    async def get_angular_velocity(self, *, extra: Optional[Dict[str, Any]] = None, timeout: Optional[float] = None,
                                   **kwargs) -> Vector3:

        w_x, w_y, w_z = await self.visual_odometry.get_angular_velocity()
        return Vector3(x=w_x,y=w_y, z=w_z)

    async def get_linear_acceleration(self, *, extra: Optional[Dict[str, Any]] = None, timeout: Optional[float] = None,
                                      **kwargs) -> Vector3:
        pass

    async def get_compass_heading(self, extra: Optional[Dict[str, Any]] = None, timeout: Optional[float] = None,
                                  **kwargs) -> float:
        pass

    async def get_orientation(self, extra: Optional[Dict[str, Any]] = None, timeout: Optional[float] = None,
                              **kwargs) -> Orientation:
        pass

    async def get_properties(self, extra: Optional[Dict[str, Any]] = None, timeout: Optional[float] = None,
                             **kwargs) -> MovementSensor.Properties:
        return MovementSensor.Properties(linear_velocity_supported=True,
                                         angular_velocity_supported=True,
                                         orientation_supported=False,
                                         position_supported=False,
                                         compass_heading_supported=False,
                                         linear_acceleration_supported=False)

    async def get_accuracy(self, extra: Optional[Dict[str, Any]] = None, timeout: Optional[float] = None,
                           **kwargs) -> Mapping[str, float]:
        pass

    # @staticmethod
    # def get_camera_matrix_from_properties(props: Camera.Properties):
    #     fx = props.intrinsic_parameters.focal_x_px
    #     fy = props.intrinsic_parameters.focal_y_px
    #     ppx = props.intrinsic_parameters.center_x_px
    #     ppy = props.intrinsic_parameters.center_y_px
    #     return get_camera_matrix(fx, fy, ppx, ppy)
    #
    # # @staticmethod
    # def get_distortion_parameters_from_properties(props: Camera.Properties):
    #     # rk1 = props.distortion_parameters.
    #     rk1 = -0.16210
    #     rk2 = 0.13632
    #     rk3 = -0.03443
    #     tp1 = 0.01364798
    #     tp2 = -0.0107569
    #     return utils.get_distort_param(rk1, rk2, rk3, tp1, tp2)

    @staticmethod
    def get_distortion_parameters():
        rk1 = -0.16210
        rk2 = 0.13632
        rk3 = -0.03443
        tp1 = 0.01364798
        tp2 = -0.0107569
        return get_distort_param(rk1, rk2, rk3, tp1, tp2)

    @staticmethod
    def get_camera_matrix():
        fx = 1407.16*(720/960)
        fy = 1359.84*(1280/1440)
        ppx = 595.26*(720/960)
        ppy = 658.18*(1280/1440)
        return get_camera_matrix(fx, fy, ppx, ppy)
