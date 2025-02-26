from torch import Tensor
from lightly.transforms.multi_crop_transform import MultiCropTranform
from lightly.transforms.utils import IMAGENET_NORMALIZE
from lightly.transforms.rotation import random_rotation_transform
from lightly.transforms.gaussian_blur import GaussianBlur
from typing import Optional, Tuple, Union
from PIL.Image import Image
import torchvision.transforms as T


class SwaVTransform(MultiCropTranform):
    """Implements the multi-crop transformations for SwaV.

    Attributes:
        crop_sizes:
            Size of the input image in pixels for each crop category.
        crop_counts:
            Number of crops for each crop category.
        crop_min_scales:
            Min scales for each crop category.
        crop_max_scales:
            Max_scales for each crop category.
        hf_prob:
            Probability that horizontal flip is applied.
        vf_prob:
            Probability that vertical flip is applied.
        rr_prob:
            Probability that random rotation is applied.
        rr_degrees:
            Range of degrees to select from for random rotation. If rr_degrees is None,
            images are rotated by 90 degrees. If rr_degrees is a (min, max) tuple,
            images are rotated by a random angle in [min, max]. If rr_degrees is a
            single number, images are rotated by a random angle in
            [-rr_degrees, +rr_degrees]. All rotations are counter-clockwise.
        cj_prob:
            Probability that color jitter is applied.
        cj_strength:
            Strength of the color jitter.
        random_gray_scale:
            Probability of conversion to grayscale.
        gaussian_blur:
            Probability of Gaussian blur.
        kernel_size:
            Will be deprecated in favor of `sigmas` argument. If set, the old behavior applies and `sigmas` is ignored.
            Used to calculate sigma of gaussian blur with kernel_size * input_size.
        sigmas:
            Tuple of min and max value from which the std of the gaussian kernel is sampled.
            Is ignored if `kernel_size` is set.
        normalize:
            Dictionary with 'mean' and 'std' for torchvision.transforms.Normalize.

    """

    def __init__(
        self,
        crop_sizes: Tuple[int] = (224, 96),
        crop_counts: Tuple[int] = (2, 6),
        crop_min_scales: Tuple[float] = (0.14, 0.05),
        crop_max_scales: Tuple[float] = (1.0, 0.14),
        hf_prob: float = 0.5,
        vf_prob: float = 0.0,
        rr_prob: float = 0.0,
        rr_degrees: Union[None, float, Tuple[float, float]] = None,
        cj_prob: float = 0.8,
        cj_strength: float = 0.8,
        random_gray_scale: float = 0.2,
        gaussian_blur: float = 0.5,
        kernel_size: Optional[float] = None,
        sigmas: Tuple[float, float] = (0.2, 2),
        normalize: Union[None, dict] = IMAGENET_NORMALIZE,
    ):

        transforms = SwaVViewTransform(
            hf_prob=hf_prob,
            vf_prob=vf_prob,
            rr_prob=rr_prob,
            rr_degrees=rr_degrees,
            cj_prob=cj_prob,
            cj_strength=cj_strength,
            random_gray_scale=random_gray_scale,
            gaussian_blur=gaussian_blur,
            kernel_size=kernel_size,
            sigmas=sigmas,
            normalize=normalize,
        )

        super().__init__(
            crop_sizes=crop_sizes,
            crop_counts=crop_counts,
            crop_min_scales=crop_min_scales,
            crop_max_scales=crop_max_scales,
            transforms=transforms,
        )


class SwaVViewTransform:
    def __init__(
        self,
        hf_prob: float = 0.5,
        vf_prob: float = 0.0,
        rr_prob: float = 0.0,
        rr_degrees: Union[None, float, Tuple[float, float]] = None,
        cj_prob: float = 0.8,
        cj_strength: float = 0.8,
        random_gray_scale: float = 0.2,
        gaussian_blur: float = 0.5,
        kernel_size: Optional[float] = None,
        sigmas: Tuple[float, float] = (0.2, 2),
        normalize: Union[None, dict] = IMAGENET_NORMALIZE,
    ):
        color_jitter = T.ColorJitter(
            cj_strength,
            cj_strength,
            cj_strength,
            cj_strength / 4.0,
        )

        transforms = [
            T.RandomHorizontalFlip(p=hf_prob),
            T.RandomVerticalFlip(p=vf_prob),
            random_rotation_transform(rr_prob=rr_prob, rr_degrees=rr_degrees),
            T.ColorJitter(),
            T.RandomApply([color_jitter], p=cj_prob),
            T.RandomGrayscale(p=random_gray_scale),
            GaussianBlur(kernel_size=kernel_size, sigmas=sigmas, prob=gaussian_blur),
            T.ToTensor(),
            T.Normalize(mean=normalize["mean"], std=normalize["std"]),
        ]
        if normalize:
            transforms += [T.Normalize(mean=normalize["mean"], std=normalize["std"])]

        self.transform = T.Compose(transforms)

    def __call__(self, image: Union[Tensor, Image]) -> Tensor:
        """
        Applies the transforms to the input image.

        Args:
            image: 
                The input image to apply the transforms to.

        Returns:
            The transformed image.

        """
        return self.transform(image)
