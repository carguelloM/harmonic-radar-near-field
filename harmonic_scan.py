import classes
from classes.bb60c_class import BB60C_INTERFACE
from classes.g_code_cntrl_class import PrinterController

if __name__=="__main__":
    ## setup logging
    classes.setup_logging()

    ## BB60C Object initialization ritual ##
    bb60c = BB60C_INTERFACE(center_freq=4.6e9)
    bb60c.initialize_device()
    name_dir = input("Enter the name of the directory to store data: ")
    bb60c.set_dir(name_dir)
    target_comment = input("Enter target name + description (no space): ")
    bb60c.set_comment(target_comment)

    ## XYZ Gantry Object initialization ritual ##
    gantry = PrinterController()

    ## note that init leaves the gantry at (1,1,1)
    if not gantry.init_controller():
        exit(-1)
    
    ## Move th gantry to the correct position 
    gantry.move_left(191) ## X position 1->192
    gantry.send_command()

    gantry.move_up(12) ## Y position 1->13
    gantry.send_command()

    gantry.table_up(150) ## Z position 1->151
    gantry.send_command()

    ## Start the scan
    step_inc = 6 ## each step is 6 mm (3x8 grid)
    num_rows = 8
    num_cols = 3
    for _ in range(num_rows):
        for _ in range(num_cols):
            ## do an acquisition (i.e. 10 captures avg)
            bb60c.capture_data()
            ## move the gantry 6 mm to the right
            gantry.move_right(step_inc)

        ## reset x position to leftmost position
        gantry.move_left(step_inc*num_cols)
        ## move the gantry up 6 mm
        gantry.move_up(step_inc)

    ## get all peaks for FFTs 
    bb60c.get_fft_peaks()

    ## save the data
    bb60c.save_data(target_comment)

    ## move the gantry to the origin
    gantry.finish_move()
    gantry.send_command()

    ## close the device
    bb60c.close_device()

    ## create plots ffts
    for i in range(num_rows*num_cols):
        bb60c.plot_fft(i)
    
    print("Program Done...Bye!")