from bb_api import *
import numpy as np
import scipy.fftpack
from scipy import signal
from scipy.fft import fft, fftshift
import matplotlib.pyplot as plt

'''
data
|-> acquisition 1
    |-> capture_1
    |-> capture_2
    |-> ...
    |-> capture_num_captures
|-> acquisition 2
    |-> capture_1
    |-> capture_2
    |-> ...
    |-> capture_num_captures
|-> ...

avg_data
|-> acquisition 1 (average of all captures)
|-> acquisition 2 (average of all captures)
|-> ...
'''


class BB60C_INTERFACE:
    ## Attributes
    samples_per_capture = 4096 
    decimation = 1
    bandwidth = 20.0e6 / decimation

    ## Constructor
    def __init__(self, ref_level=-60.0, center_freq=1.0e9, num_captures=10):
        self.data = []
        self.avg_data = []
        self.fft_data = []
        self.freqs = fftshift(np.fft.fftfreq(self.samples_per_capture, 1/self.bandwidth))
        self.window = signal.windows.flattop(self.samples_per_capture)
        self.num_captures = num_captures
        self.handle = None
        self.ref_level = ref_level
        self.center_freq = center_freq

    ## Methods
    def initialize_device(self):
        self.handle = bb_open_device()["handle"]
        bb_configure_ref_level(self.handle, self.ref_level)
        bb_configure_gain_atten(self.handle, BB_AUTO_GAIN, BB_AUTO_ATTEN)
        bb_configure_IQ_center(self.handle, self.center_freq)
        bb_configure_IQ(self.handle, self.decimation, self.bandwidth)
        bb_initiate(self.handle, BB_STREAMING, BB_STREAM_IQ)
    
    def close_device(self):
        bb_close_device(self.handle)
    
    def capture_data(self):
        print("Capturing...")
        acquisition = []
        for _ in range(self.num_captures):
            iq = bb_get_IQ_unpacked(self.handle, self.samples_per_capture, BB_FALSE)["iq"]
            acquisition.append(iq)
        self.data.append(acquisition)
        print('Calculating DFT...')
        self.calc_fft()
        return

    def calc_fft(self):
        fft_acquisition = []
        ## last acquisition (i.e. 10 capture)
        acquisition = self.data[-1]
        for capture in acquisition:
            ## DFT of the capture
            dft = fftshift(fft(capture * self.window))
            dft_pwr = 20*np.log10(np.abs(dft)/self.samples_per_capture)
            fft_acquisition.append(dft_pwr) 
        ## save only the average of the DFTs of the captures
        self.fft_data.append(np.mean(fft_acquisition, axis=0))

    def plot_fft(self):
        plt.plot(self.freqs, self.fft_data[-1])
        plt.title('FFT Average in Frequency')
        plt.show()

    def calculate_avg_time(self):
         acquisition = self.data[-1]
         avg_data = np.mean(acquisition, axis=0)
         dft = fftshift(fft(avg_data * self.window))
         plt.plot(self.freqs, 20*np.log10(np.abs(dft)/self.samples_per_capture))
         plt.title('Average in Time')
         plt.show()
