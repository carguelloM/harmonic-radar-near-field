from classes.bb_api import *
import numpy as np
from scipy import signal
from scipy.fft import fft, fftshift
import matplotlib.pyplot as plt
import logging
import pickle
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

    ## Constructor
    def __init__(self, ref_level=-60.0, center_freq=1.0e9, num_captures=10, decimation=1):
        ## Logging
        self.logger = logging.getLogger("BB60C")

        ## Data
        self.data = []
        self.fft_data = []
        self.peaks = []
        self.num_captures = num_captures
        
        ## Device Related

        ## Keys are the decimation and values are the max filter bandwidths as per the API
        max_filter_bw = {1: 27e6, 2:17.8e6, 4:8e6, 8:3.75e6, 16:2e6, 32:1e6} 
        self.handle = None
        self.ref_level = ref_level
        self.center_freq = center_freq
        self.samples_per_capture = 4096
        self.decimation = decimation
        self.bandwidth = 40.0e6 / self.decimation
        self.filter_bw = max_filter_bw[self.decimation]

         ## DFT Related
        self.freqs = fftshift(np.fft.fftfreq(self.samples_per_capture, 1/self.bandwidth))
        self.window = signal.windows.flattop(self.samples_per_capture)

    ## Methods

    ######## DEVICE MANAGEMENT ########
    def initialize_device(self):
        self.handle = bb_open_device()["handle"]
        bb_configure_ref_level(self.handle, self.ref_level)
        bb_configure_gain_atten(self.handle, BB_AUTO_GAIN, BB_AUTO_ATTEN)
        bb_configure_IQ_center(self.handle, self.center_freq)
        bb_configure_IQ(self.handle, self.decimation, self.filter_bw)
        bb_initiate(self.handle, BB_STREAMING, BB_STREAM_IQ)
    
    def close_device(self):
        bb_close_device(self.handle)
    
    def capture_data(self):
        self.logger.info('CAPTURING...')
        acquisition = []
        for _ in range(self.num_captures):
            iq = bb_get_IQ_unpacked(self.handle, self.samples_per_capture, BB_FALSE)["iq"]
            acquisition.append(iq)
        self.data.append(acquisition)
        self.logger.info('CALCULATING FFT...')
        self.calc_fft()
        return

    #### DFT CALCULATIONS ####
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

    # def find_peaks(self):
    #     for spectrum in self.fft_data:
    #         peaks = signal.find_peaks(spectrum, height=20)
    #         self.peaks.append(peaks)
        
    def plot_fft(self):
        center_indx = int(len(self.fft_data[-1])/2)
        peaks, _ = signal.find_peaks(self.fft_data[-1], prominence=1)

        if(len(peaks) > 0):
            closest_to_zero = np.argmin(np.abs(peaks - center_indx))
            peak = peaks[closest_to_zero]
            plt.scatter(self.freqs[peak], self.fft_data[-1][peak], color='red')

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
    
    def save_data(self, filename='data'):
        fn = filename + '.pkl'
        with open(fn, 'wb') as f:
            data_to_save = {'raw_iq': self.data, 'fft_avg': self.fft_data, 'peaks': self.peaks}
            pickle.dump(data_to_save, f)
