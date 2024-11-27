import classes 
from classes.bb60c_class import BB60C_INTERFACE


if __name__=="__main__":
    ## Setup logging
    classes.setup_logging()
    # Create an instance of the BB60C class
    bb60c = BB60C_INTERFACE(center_freq=4.6e9)
    ## initialize the device
    bb60c.initialize_device()
    ## create a directory to store data
    bb60c.set_dir('data_test')
    ## Get 5 Acquisitions
    for _ in range(5):
        ## Each acquisition has 10 captures (avg -> 1 acquisition)
        bb60c.capture_data()

    ## get all peaks for FFTs (should be 5 peaks or 1 per acquisition)
    bb60c.get_fft_peaks()

    for i in range(5):
        ## plot all FFTs
        bb60c.plot_fft(i)

    ## save the data 
    bb60c.save_data("test_data")
    ## close the device
    bb60c.close_device()

