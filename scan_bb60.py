import classes 
from classes.bb60c_class import BB60C_INTERFACE


if __name__=="__main__":
    ## Setup logging
    classes.setup_logging()
    # Create an instance of the BB60C class
    bb60c = BB60C_INTERFACE(center_freq=4.6e9)
    ## initialize the device
    bb60c.initialize_device()

    ## capture 10 spectrum and calculate the average FFT
    bb60c.capture_data()

    ## get all peaks for FFTs
    bb60c.get_fft_peaks()

    ## plot the data
    bb60c.plot_fft(0)
    
    ## close the device
    bb60c.close_device()

