from classes.g_code_cntrl_class import PrinterController

myPrintControl = PrinterController()
if not myPrintControl.init_controller():
    exit(-1)
myPrintControl.interactive_moves()
