import os
import ctypes

class WindowsInhibitor:
    '''
    Prevent OS sleep/hibernate in windows; code from:
    https://github.com/h3llrais3r/Deluge-PreventSuspendPlus/blob/master/preventsuspendplus/core.py
    API documentation:
    https://msdn.microsoft.com/en-us/library/windows/desktop/aa373208(v=vs.85).aspx
    '''
    ES_CONTINUOUS        = 0x80000000
    ES_SYSTEM_REQUIRED   = 0x00000001
    ES_AWAYMODE_REQUIRED = 0x00000040

    def __init__(self):
        pass

    def inhibit(self):
        if os.name == 'nt': #Prevent Windows from going to sleep
            try:
                ctypes.windll.kernel32.SetThreadExecutionState(
                    WindowsInhibitor.ES_CONTINUOUS | \
                    WindowsInhibitor.ES_SYSTEM_REQUIRED)
            except:
                return False
            return True
        else:
            return False

    def uninhibit(self):
        import ctypes
        #print("")
        if os.name == 'nt': #Allow Windows to go to sleep
            try:
                ctypes.windll.kernel32.SetThreadExecutionState(
                    WindowsInhibitor.ES_CONTINUOUS)
            except:
                return False
            return True
        else:
            return False


            
if __name__ == "__main__":
    import time
    osSleep = WindowsInhibitor()
    print("no sleep = ",osSleep.inhibit())
    t_init=time.time()
    d_time=0
    while d_time < 20:
        time.sleep(5)
        d_time = time.time()-t_init
        print d_time
    if osSleep:
        print("stop no sleep = ",osSleep.uninhibit())
