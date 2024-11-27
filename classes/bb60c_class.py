from classes.bb_api import *
import numpy as np
from scipy import signal
from scipy.fft import fft, fftshift
import matplotlib.pyplot as plt
import logging
import pickle
import os

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

fft_data
|-> fft acquisition 1 (average of all captures)
|-> fft acquisition 2 (average of all captures)
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
        self.peaks_indxs = []
        self.peaks = []
        self.dir = None
        self.comment = None
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
        self.logger.info('Device Closed')
    
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

    ##### DFT RELATED CALCULATIONS ####
    def calc_fft(self):
        fft_acquisition = []
        ## last acquisition (i.e. 10 capture)
        acquisition = self.data[-1]
        for capture in acquisition:
            ## DFT of the capture
            dft = fftshift(fft(capture * self.window))
            dft_pwr = 20*np.log10(np.abs(dft)/self.samples_per_capture) + 13.01
            fft_acquisition.append(dft_pwr) 
        ## save only the average of the DFTs of the captures
        self.fft_data.append(np.mean(fft_acquisition, axis=0))

    def get_fft_peaks(self):
        center_indx = int(self.samples_per_capture/2) ## note all FFTs are the same size
        for spectrum in self.fft_data:
            peaks, _ = signal.find_peaks(spectrum, prominence=1)

            '''
            check if there's a peak at the center frequency
            for the scanning experiments this should be the case most of the time
            given the spurious second harmonic WE are transmitting
            '''
            if(len(peaks) > 0):
                closest_to_zero = np.argmin(np.abs(peaks - center_indx))
                single_peak = peaks[closest_to_zero]
                self.peaks_indxs.append(single_peak)
                self.peaks.append(spectrum[single_peak])
            else:
                self.peaks.append(None)
    

    #### DATA MANAGEMENT ####
    def set_dir(self, dir):
        if not os.path.exists(dir):
            os.makedirs(dir)
        self.dir = dir

    def set_comment(self, comment):
        basic_comment = 'Reference Level: ' + str(self.ref_level) + ' dBm\n' + 'Center Frequency: ' + str(self.center_freq) + ' Hz\n' + 'Decimation: ' + str(self.decimation) + '\n' + 'Filter Bandwidth: ' + str(self.filter_bw) + ' Hz\n'
        self.comment = basic_comment + comment

    def plot_fft(self, spectrum_index):
        fig_path = 'fft_spectrum_' + str(spectrum_index) + '.png'

        if self.dir:
            fig_path = self.dir + '/' + fig_path
        
        plt.plot(self.freqs, self.fft_data[spectrum_index], label='FFT Spectrum')
        if self.peaks[spectrum_index] is not None:
            plt.scatter(self.freqs[self.peaks_indxs[spectrum_index]], self.fft_data[spectrum_index][self.peaks_indxs[spectrum_index]], 
                    color='red', marker='x', label=f'Peak Value = {self.fft_data[spectrum_index][self.peaks_indxs[spectrum_index]]}')
        plt.title(f'FFT Spectrum #{spectrum_index}')
        plt.legend()
        plt.xlabel('Frequency (Hz)')
        plt.ylabel('Power (dBm)')
        plt.savefig(fig_path)
        plt.close()
        self.logger.info(f'FFT Spectrum {spectrum_index} plotted and saved to {fig_path}')
        return


    def save_data(self, filename='data'):
        fn = filename + '.pkl'

        ## if directory is specified add path before filename
        if self.dir:
            fn = self.dir + '/' + fn 

        with open(fn, 'wb') as f:
            data_to_save = {'raw_iq': self.data, 'fft_avg': self.fft_data, 'peaks': self.peaks, 
                            'peaks_indxs': self.peaks_indxs, 'Description': self.comment}  
            pickle.dump(data_to_save, f)
        self.logger.info(f'Data saved to {fn}')
        return
