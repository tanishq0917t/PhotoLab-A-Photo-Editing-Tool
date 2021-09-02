import tkinter
import PIL
import PIL.ImageTk
import tkinter.ttk
class SplashWindow(tkinter.Tk):
    def __init__(self):
        tkinter.Tk.__init__(self)
        self.geometry("700x490+350+150")
        self.overrideredirect(True)
        self.canvas=tkinter.Canvas(self,height=470,width=700)
        self.canvas.place(x=0,y=0)
        self.progress = tkinter.ttk.Progressbar(self, orient = tkinter.HORIZONTAL,length = 700, mode = 'determinate')
        self.progress.place(x=0,y=468)
        self.after(10,self.bar)
    def bar(self):
        img=PIL.ImageTk.PhotoImage(PIL.Image.open("icons/background.png"))
        img2=PIL.ImageTk.PhotoImage(PIL.Image.open("icons/background2.png"))
        img3=PIL.ImageTk.PhotoImage(PIL.Image.open("icons/background3.png"))
        self.canvas.create_image(0,0,image=img,anchor="nw")
        import time
        a=0
        count=0
        while a<=100:
            self.progress['value'] = a
            self.update_idletasks()
            if a>30:
                self.canvas.create_image(0,0,image=img2,anchor="nw")
            if a>65:
                self.canvas.create_image(0,0,image=img3,anchor="nw")
            time.sleep(1)
            if count%2: a+=15
            else: a+=5
            count+=1