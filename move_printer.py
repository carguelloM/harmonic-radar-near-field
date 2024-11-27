import classes
from classes.g_code_cntrl_class import PrinterController

if __name__=="__main__":
    classes.setup_logging()
    myPrintControl = PrinterController()
    if not myPrintControl.init_controller():
        exit(-1)
    myPrintControl.interactive_moves()
