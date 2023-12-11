import numpy as np

class ImageMixer:
    def __init__(self, images_list):
        self.images_list = images_list

    def mix_images(self, mix_ratios):
        # Validate the mix_ratios
        if len(mix_ratios) != len(self.images_list):
            raise ValueError("The number of mix ratios should be equal to the number of images.")

        # Initialize variables for the mixed amplitude and phase
        mixed_amplitudes = np.zeros_like(self.images_list[0].get_magnitude_spectrum())
        mixed_phases = np.zeros_like(self.images_list[0].get_phase_spectrum())

        # Mix the amplitudes and phases based on the mix ratios
        for i, image in enumerate(self.images_list):
            mix_ratio = mix_ratios[i]
            mixed_amplitudes += mix_ratio * image.get_magnitude_spectrum()
            mixed_phases += mix_ratio * image.get_phase_spectrum()

        # Reconstruct the mixed image using the inverse Fourier transform
        mixed_transform = mixed_amplitudes * np.exp(1j * mixed_phases)
        mixed_image_data = np.fft.ifft2(mixed_transform).real

        return mixed_image_data