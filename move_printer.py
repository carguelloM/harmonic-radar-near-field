from classes.g_code_cntrl_class import PrinterController

myPrintControl = PrinterController()
myPrintControl.init_controller()
myPrintControl.interactive_moves()
