import tkinter
import tkinter.ttk
import ctypes
import PIL
import PIL.ImageTk
import tkinter.filedialog
import cv2
import numpy
import pathlib
import os
import tkinter.font
from splashScreen import SplashWindow
import tkinter.colorchooser
import tkinter.scrolledtext
import yagmail
from PIL import Image, ImageFilter
import random
class ToolTip(object):
    def __init__(self, widget):
        self.widget = widget
        self.tipwindow = None
        self.id = None
        self.x = self.y = 0
    def showtip(self, text):
        self.text = text
        if self.tipwindow or not self.text:
            return
        x, y, cx, cy = self.widget.bbox("insert")
        x = x + self.widget.winfo_rootx() + 35
        y = y + cy + self.widget.winfo_rooty() +40
        self.tipwindow = tw = tkinter.Toplevel(self.widget)
        tw.wm_overrideredirect(1)
        tw.wm_geometry("+%d+%d" % (x, y))
        label = tkinter.Label(tw, text=self.text, justify=tkinter.LEFT,background="#ffffe0", relief=tkinter.SOLID, borderwidth=1,font=("tahoma", "8", "normal"))
        label.pack(ipadx=1)

    def hidetip(self):
        tw = self.tipwindow
        self.tipwindow = None
        if tw:
            tw.destroy()

def CreateToolTip(widget, text):
    toolTip = ToolTip(widget)
    def enter(event):
        toolTip.showtip(text)
    def leave(event):
        toolTip.hidetip()
    widget.bind('<Enter>', enter)
    widget.bind('<Leave>', leave)

class Window(tkinter.Tk):
    def __init__(self):
        tkinter.Tk.__init__(self)
        width,height=ctypes.windll.user32.GetSystemMetrics(0),ctypes.windll.user32.GetSystemMetrics(1)
        self.desktopWidth=width
        self.desktopHeight=height
        self.iconbitmap("icons/logo.ico")
        self.title("PhotoLab - A Photo Editing Tool")
        self.geometry(f"{self.desktopWidth}x{self.desktopHeight}+0+0")
        self.state("zoomed")
        self.resizable(0,0)
        self.configureMenu()
        self.configureToolBar()
        self.imageContainerFrame=tkinter.Frame(self)
        self.imageContainerFrame.pack(side=tkinter.BOTTOM,fill=tkinter.BOTH,expand=True)
        self.currentImage=None
        self.imageFileName=None
        self.lastModified=None
        self.scrollBar=tkinter.Scrollbar(self.imageContainerFrame,orient='vertical')
        self.scrollBar.pack(side=tkinter.RIGHT,fill=tkinter.Y)
        self.imageCanvas=tkinter.Canvas(self.imageContainerFrame,width=1550,height=650,background="#ADADAD",relief=tkinter.RAISED,bd=1,yscrollcommand=self.scrollBar.set) #bisque #E4E3E3
        self.imageCanvas.place(x=0,y=0)
        self.detailCanvas=tkinter.Canvas(self.imageContainerFrame,width=1550,height=150,background="#E4E3E3") #bisque
        self.detailCanvas.place(x=0,y=655)
        self.bind("<Control-o>",self._openImageShortcut)
        self.first=0
        self.processingImage=PIL.ImageTk.PhotoImage(PIL.Image.open("icons/process.png"))
        self.imageDS=[]
        self.actionDS=[]
        self.imageIdDS=[]
        self.undoPointer=0
        self.imageId=None
        self.protocol('WM_DELETE_WINDOW',self.windowClosing)
    def configureMenu(self):
        self.menuBar=tkinter.Menu(self)
        self.config(menu=self.menuBar)

        self.fileMenu=tkinter.Menu(self.menuBar,tearoff=0)
        self.fileMenu.add_command(label="New")
        self.fileMenu.add_command(label="Open",command=self._openImage)
        self.fileMenu.add_command(label="Save",state="disabled")
        self.fileMenu.add_command(label="Save As",state="disabled",command=self._saveFile)
        self.fileMenu.add_separator()
        self.fileMenu.add_command(label="Exit",command=self._exit)
        self.menuBar.add_cascade(label="File",menu=self.fileMenu)

        self.editMenu=tkinter.Menu(self.menuBar,tearoff=0)
        self.editMenu.add_command(label="Cut",state="disabled")
        self.editMenu.add_command(label="Copy",state="disabled")
        self.editMenu.add_command(label="Paste",state="disabled")
        self.menuBar.add_cascade(label="  Edit  ",menu=self.editMenu)

        self.viewMenu=tkinter.Menu(self.menuBar,tearoff=0)
        self.viewMenu.add_command(label="Zoom In",state="disabled",command=self._zoomIn)
        self.viewMenu.add_command(label="Zoom Out",state="disabled",command=self._zoomOut)
        self.menuBar.add_cascade(label="  View  ",menu=self.viewMenu)

        self.magnificationMenu=tkinter.Menu(self.menuBar,tearoff=0)
        self.magnificationMenu.add_command(label="50%",state="disabled",command=lambda: self._magnify(50,self.lastModified))
        self.magnificationMenu.add_command(label="100%",state="disabled",command=lambda: self._magnify(100,self.lastModified))
        self.magnificationMenu.add_command(label="150%",state="disabled",command=lambda: self._magnify(150,self.lastModified))
        self.magnificationMenu.add_command(label="200%",state="disabled",command=lambda: self._magnify(200,self.lastModified))
        self.viewMenu.add_cascade(label="Magnification",menu=self.magnificationMenu)

        self.transformMenu=tkinter.Menu(self.menuBar,tearoff=0)
        self.transformMenu.add_command(label="Crop",command=self._cropImage,state="disabled")
        self.transformMenu.add_command(label="Rotate",state="disabled",command=self._rotateRight)
        self.transformMenu.add_command(label="Rotate 90\u00B0 Right",command=self._rotateRight,state="disabled")
        self.transformMenu.add_command(label="Rotate 90\u00B0 Left",command=self._rotateLeft,state="disabled")
        self.transformMenu.add_command(label="Rotate 180\u00B0",command=self._flipVertical,state="disabled")
        self.transformMenu.add_command(label="Flip Horizontal",command=self._flipHorizontal,state="disabled")
        self.transformMenu.add_command(label="Flip Vertical",command=self._flipVertical,state="disabled")
        self.menuBar.add_cascade(label="  Transform  ",menu=self.transformMenu)

        self.filterMenu=tkinter.Menu(self.menuBar,tearoff=0)
        self.filterMenu.add_command(label="Mean",state="disabled")
        self.filterMenu.add_command(label="Median",state="disabled",command=self._medianBlurring)
        self.filterMenu.add_command(label="Fourier Transform",state="disabled")
        self.filterMenu.add_command(label="Gaussian Smoothing",state="disabled",command=self._gaussian)
        self.filterMenu.add_command(label="Unsharp",state="disabled")
        self.filterMenu.add_command(label="Laplacian",state="disabled",command=self._laplacian)
        self.menuBar.add_cascade(label="  Filter  ",menu=self.filterMenu)

        self.borderMenu=tkinter.Menu(self.menuBar,tearoff=0)
        self.borderMenu.add_command(label="Custom Border",state="disabled",command=self._customBorder)
        self.borderMenu.add_command(label="Normal Border",state="disabled",command=self._normalBorder)
        self.menuBar.add_cascade(label="  Border  ",menu=self.borderMenu)

        self.drawMenu=tkinter.Menu(self.menuBar,tearoff=0)
        self.drawMenu.add_command(label="Circle",state="disabled",command=self._drawCircle)
        self.drawMenu.add_command(label="Line",state="disabled",command=self._drawLine)
        self.drawMenu.add_command(label="Rectangle",state="disabled",command=self._drawRectangle)
        self.drawMenu.add_command(label="Text",state="disabled",command=self._drawText)
        self.menuBar.add_cascade(label="  Draw  ",menu=self.drawMenu)

        self.blurMenu=tkinter.Menu(self.menuBar,tearoff=0)
        self.blurMenu.add_command(label="Bilateral Blur",state="disabled",command=self._bilateral)
        self.blurMenu.add_command(label="Box Blur",state="disabled",command=self._box)
        self.blurMenu.add_command(label="General Blur",state="disabled",command=self._blur)
        self.blurMenu.add_command(label="Gaussian Blur",state="disabled",command=self._gaussian)
        self.menuBar.add_cascade(label="  Blur  ",menu=self.blurMenu)

        self.transitionMenu=tkinter.Menu(self.menuBar,tearoff=0)
        self.transitionMenu.add_command(label="Style 1",state="disabled",command=lambda: self._transition(1))
        self.transitionMenu.add_command(label="Style 2",state="disabled",command=lambda: self._transition(2))
        self.transitionMenu.add_command(label="Style 3",state="disabled",command=lambda: self._transition(3))
        self.transitionMenu.add_command(label="Style 4",state="disabled",command=lambda: self._transition(4))
        self.transitionMenu.add_command(label="Random",state="disabled",command=lambda: self._transition(0))
        self.menuBar.add_cascade(label="  Transition  ",menu=self.transitionMenu)
    def configureToolBar(self):
        #self.toolBar=tkinter.Frame(self,relief=tkinter.RAISED,bd=1,bg="#82f261") Green
        #self.toolBar=tkinter.Frame(self,relief=tkinter.RAISED,bd=1,bg="#f29435") #Orange
        #self.toolBar=tkinter.Frame(self,relief=tkinter.RAISED,bd=1,bg="#FFFDD0")
        #self.toolBar=tkinter.Frame(self,relief=tkinter.RAISED,bd=1,bg="#DA7FF4")#F6A267
        self.toolBar=tkinter.Frame(self,relief=tkinter.RAISED,bd=0,bg="#F6A267")#FAFFA7
        self.toolBar.pack(side=tkinter.TOP,fill=tkinter.X)


        self.imagePick=PIL.ImageTk.PhotoImage(PIL.Image.open("icons/pick.png"))
        self.toolBarPickButton=tkinter.Button(self.toolBar,image=self.imagePick,state=tkinter.DISABLED)
        self.toolBarPickButton.pack(side=tkinter.LEFT,padx=4,pady=4)
        CreateToolTip(self.toolBarPickButton, text = 'Pick')

        self.imageNew=PIL.ImageTk.PhotoImage(PIL.Image.open("icons/new.png"))
        self.toolBarNewButton=tkinter.Button(self.toolBar,image=self.imageNew)
        self.toolBarNewButton.pack(side=tkinter.LEFT,padx=4,pady=4)
        CreateToolTip(self.toolBarNewButton, text = 'New')

        self.imageOpen=PIL.ImageTk.PhotoImage(PIL.Image.open("icons/open.png"))
        self.toolBarOpenButton=tkinter.Button(self.toolBar,image=self.imageOpen,command=self._openImage)
        self.toolBarOpenButton.pack(side=tkinter.LEFT,padx=4,pady=4)
        CreateToolTip(self.toolBarOpenButton, text = 'Open')

        self.imageSave=PIL.ImageTk.PhotoImage(PIL.Image.open("icons/save.png"))
        self.toolBarSaveButton=tkinter.Button(self.toolBar,image=self.imageSave,state=tkinter.DISABLED,command=self._saveFile)
        self.toolBarSaveButton.pack(side=tkinter.LEFT,padx=4,pady=4)
        CreateToolTip(self.toolBarSaveButton, text = 'Save')

        self.imageCut=PIL.ImageTk.PhotoImage(PIL.Image.open("icons/cut.png"))
        self.toolBarCutButton=tkinter.Button(self.toolBar,image=self.imageCut,state=tkinter.DISABLED)
        self.toolBarCutButton.pack(side=tkinter.LEFT,padx=4,pady=4)
        CreateToolTip(self.toolBarCutButton, text = 'Cut')

        self.imageCopy=PIL.ImageTk.PhotoImage(PIL.Image.open("icons/copy.png"))
        self.toolBarCopyButton=tkinter.Button(self.toolBar,image=self.imageCopy,state=tkinter.DISABLED)
        self.toolBarCopyButton.pack(side=tkinter.LEFT,padx=4,pady=4)
        CreateToolTip(self.toolBarCopyButton, text = 'Copy')

        self.imagePaste=PIL.ImageTk.PhotoImage(PIL.Image.open("icons/paste.png"))
        self.toolBarPasteButton=tkinter.Button(self.toolBar,image=self.imagePaste,state=tkinter.DISABLED)
        self.toolBarPasteButton.pack(side=tkinter.LEFT,padx=4,pady=4)
        CreateToolTip(self.toolBarPasteButton, text = 'Paste')

        self.imageBrightness=PIL.ImageTk.PhotoImage(PIL.Image.open("icons/brightness.png"))
        self.toolBarBrightnessButton=tkinter.Button(self.toolBar,image=self.imageBrightness,command=self._brightness,state=tkinter.DISABLED)
        self.toolBarBrightnessButton.pack(side=tkinter.LEFT,padx=4,pady=4)
        CreateToolTip(self.toolBarBrightnessButton, text = 'Brightness')

        self.imageContrast=PIL.ImageTk.PhotoImage(PIL.Image.open("icons/contrast.png"))
        self.toolBarContrastButton=tkinter.Button(self.toolBar,image=self.imageContrast,command=self._contrast,state=tkinter.DISABLED)
        self.toolBarContrastButton.pack(side=tkinter.LEFT,padx=4,pady=4)
        CreateToolTip(self.toolBarContrastButton, text = 'Contrast')

        self.imageGrayScale=PIL.ImageTk.PhotoImage(PIL.Image.open("icons/gray_scale.png"))
        self.toolBarGrayScaleButton=tkinter.Button(self.toolBar,image=self.imageGrayScale,command=self._grayScale,state=tkinter.DISABLED)
        self.toolBarGrayScaleButton.pack(side=tkinter.LEFT,padx=4,pady=4)
        CreateToolTip(self.toolBarGrayScaleButton, text = 'Gray Scale')

        self.imageCrop=PIL.ImageTk.PhotoImage(PIL.Image.open("icons/crop.png"))
        self.toolBarCropButton=tkinter.Button(self.toolBar,image=self.imageCrop,command=self._cropImage,state=tkinter.DISABLED)
        self.toolBarCropButton.pack(side=tkinter.LEFT,padx=4,pady=4)
        CreateToolTip(self.toolBarCropButton, text = 'Crop')

        self.imageBorder=PIL.ImageTk.PhotoImage(PIL.Image.open("icons/border.png"))
        self.toolBarBorderButton=tkinter.Button(self.toolBar,image=self.imageBorder,state=tkinter.DISABLED,command=self._customBorder)
        self.toolBarBorderButton.pack(side=tkinter.LEFT,padx=4,pady=4)
        CreateToolTip(self.toolBarBorderButton, text = 'Border')

        self.imageResize=PIL.ImageTk.PhotoImage(PIL.Image.open("icons/resize.png"))
        self.toolBarResizeButton=tkinter.Button(self.toolBar,image=self.imageResize,state=tkinter.DISABLED)
        self.toolBarResizeButton.pack(side=tkinter.LEFT,padx=4,pady=4)
        CreateToolTip(self.toolBarResizeButton, text = 'Resize')

        self.imageHorizontalFlip=PIL.ImageTk.PhotoImage(PIL.Image.open("icons/horizontal_flip.png"))
        self.toolBarHorizontalFlipButton=tkinter.Button(self.toolBar,image=self.imageHorizontalFlip,command=self._flipHorizontal,state=tkinter.DISABLED)
        self.toolBarHorizontalFlipButton.pack(side=tkinter.LEFT,padx=4,pady=4)
        CreateToolTip(self.toolBarHorizontalFlipButton, text = 'Horizontal Flip')

        self.imageVerticalFlip=PIL.ImageTk.PhotoImage(PIL.Image.open("icons/vertical_flip.png"))
        self.toolBarVerticalFlipButton=tkinter.Button(self.toolBar,image=self.imageVerticalFlip,command=self._flipVertical,state=tkinter.DISABLED)
        self.toolBarVerticalFlipButton.pack(side=tkinter.LEFT,padx=4,pady=4)
        CreateToolTip(self.toolBarVerticalFlipButton, text = 'Vertical Flip')

        self.imageReset=PIL.ImageTk.PhotoImage(PIL.Image.open("icons/reset.png"))
        self.toolBarResetButton=tkinter.Button(self.toolBar,image=self.imageReset,command=self._resetImage,state=tkinter.DISABLED)
        self.toolBarResetButton.pack(side=tkinter.LEFT,padx=4,pady=4)
        CreateToolTip(self.toolBarResetButton, text = 'Reset')

        self.imageUndo=PIL.ImageTk.PhotoImage(PIL.Image.open("icons/undo.png"))
        self.toolBarUndoButton=tkinter.Button(self.toolBar,image=self.imageUndo,command=self._undoImage,state=tkinter.DISABLED)
        self.toolBarUndoButton.pack(side=tkinter.LEFT,padx=4,pady=4)
        CreateToolTip(self.toolBarUndoButton, text = 'Undo')

        self.imageMail=PIL.ImageTk.PhotoImage(PIL.Image.open("icons/email.png"))
        self.toolBarMailButton=tkinter.Button(self.toolBar,image=self.imageMail,command=self._mailImage,state=tkinter.DISABLED)
        self.toolBarMailButton.pack(side=tkinter.LEFT,padx=4,pady=4)
        CreateToolTip(self.toolBarMailButton, text = 'Mail Image')

        self.imageLine=PIL.ImageTk.PhotoImage(PIL.Image.open("icons/line.png"))
        self.toolBarLineButton=tkinter.Button(self.toolBar,image=self.imageLine,command=self._drawLine,state=tkinter.DISABLED)
        self.toolBarLineButton.pack(side=tkinter.LEFT,padx=4,pady=4)
        CreateToolTip(self.toolBarLineButton, text = 'Draw Line')

        self.imageCircle=PIL.ImageTk.PhotoImage(PIL.Image.open("icons/circle.png"))
        self.toolBarCircleButton=tkinter.Button(self.toolBar,image=self.imageCircle,command=self._drawCircle,state=tkinter.DISABLED)
        self.toolBarCircleButton.pack(side=tkinter.LEFT,padx=4,pady=4)
        CreateToolTip(self.toolBarCircleButton, text = 'Draw Circle')

        self.imageRectangle=PIL.ImageTk.PhotoImage(PIL.Image.open("icons/rectangle.png"))
        self.toolBarRectangleButton=tkinter.Button(self.toolBar,image=self.imageRectangle,command=self._drawRectangle,state=tkinter.DISABLED)
        self.toolBarRectangleButton.pack(side=tkinter.LEFT,padx=4,pady=4)
        CreateToolTip(self.toolBarRectangleButton, text = 'Draw Rectangle')

        self.imageText=PIL.ImageTk.PhotoImage(PIL.Image.open("icons/text.png"))
        self.toolBarTextButton=tkinter.Button(self.toolBar,image=self.imageText,command=self._drawText,state=tkinter.DISABLED)
        self.toolBarTextButton.pack(side=tkinter.LEFT,padx=4,pady=4)
        CreateToolTip(self.toolBarTextButton, text = 'Draw Text')
    def _enableOptions(self):
        self.transformMenu.entryconfig("Crop", state="normal")
        self.transformMenu.entryconfig("Rotate", state="normal")
        self.transformMenu.entryconfig("Rotate 90\u00B0 Right", state="normal")
        self.transformMenu.entryconfig("Rotate 90\u00B0 Left", state="normal")
        self.transformMenu.entryconfig("Rotate 180\u00B0", state="normal")
        self.transformMenu.entryconfig("Flip Horizontal", state="normal")
        self.transformMenu.entryconfig("Flip Vertical", state="normal")

        self.editMenu.entryconfig("Cut", state="normal")
        self.editMenu.entryconfig("Copy", state="normal")
        self.editMenu.entryconfig("Paste", state="normal")

        self.filterMenu.entryconfig("Mean", state="normal")
        self.filterMenu.entryconfig("Median", state="normal")
        self.filterMenu.entryconfig("Fourier Transform", state="normal")
        self.filterMenu.entryconfig("Gaussian Smoothing", state="normal")
        self.filterMenu.entryconfig("Unsharp", state="normal")
        self.filterMenu.entryconfig("Laplacian", state="normal")

        self.viewMenu.entryconfig("Zoom In", state="normal")
        self.viewMenu.entryconfig("Zoom Out", state="normal")

        self.magnificationMenu.entryconfig("50%",state="normal")
        self.magnificationMenu.entryconfig("100%",state="normal")
        self.magnificationMenu.entryconfig("150%",state="normal")
        self.magnificationMenu.entryconfig("200%",state="normal")

        self.fileMenu.entryconfig("Save",state="normal")
        self.fileMenu.entryconfig("Save As",state="normal")

        self.borderMenu.entryconfig("Custom Border",state="normal")
        self.borderMenu.entryconfig("Normal Border",state="normal")

        self.drawMenu.entryconfig("Circle",state="normal")
        self.drawMenu.entryconfig("Line",state="normal")
        self.drawMenu.entryconfig("Rectangle",state="normal")
        self.drawMenu.entryconfig("Text",state="normal")

        self.blurMenu.entryconfig("Bilateral Blur",state="normal")
        self.blurMenu.entryconfig("Box Blur",state="normal")
        self.blurMenu.entryconfig("General Blur",state="normal")
        self.blurMenu.entryconfig("Gaussian Blur",state="normal")

        self.transitionMenu.entryconfig("Style 1",state="normal")
        self.transitionMenu.entryconfig("Style 2",state="normal")
        self.transitionMenu.entryconfig("Style 3",state="normal")
        self.transitionMenu.entryconfig("Style 4",state="normal")
        self.transitionMenu.entryconfig("Random",state="normal")
    def _enableButtons(self):
        self.toolBarPickButton.config(state=tkinter.NORMAL)
        self.toolBarSaveButton.config(state=tkinter.NORMAL)
        self.toolBarCutButton.config(state=tkinter.NORMAL)
        self.toolBarCopyButton.config(state=tkinter.NORMAL)
        self.toolBarPasteButton.config(state=tkinter.NORMAL)
        self.toolBarBrightnessButton.config(state=tkinter.NORMAL)
        self.toolBarContrastButton.config(state=tkinter.NORMAL)
        self.toolBarCropButton.config(state=tkinter.NORMAL)
        self.toolBarBorderButton.config(state=tkinter.NORMAL)
        self.toolBarResizeButton.config(state=tkinter.NORMAL)
        self.toolBarGrayScaleButton.config(state=tkinter.NORMAL)
        self.toolBarResetButton.config(state=tkinter.NORMAL)
        self.toolBarUndoButton.config(state=tkinter.NORMAL)
        self.toolBarHorizontalFlipButton.config(state=tkinter.NORMAL)
        self.toolBarVerticalFlipButton.config(state=tkinter.NORMAL)
        self.toolBarMailButton.config(state=tkinter.NORMAL)
        self.toolBarLineButton.config(state=tkinter.NORMAL)
        self.toolBarCircleButton.config(state=tkinter.NORMAL)
        self.toolBarRectangleButton.config(state=tkinter.NORMAL)
        self.toolBarTextButton.config(state=tkinter.NORMAL)

    def _exit(self):
        for i in self.actionDS:
            if i==self.tempReset: continue
            if pathlib.Path(i).is_file():
                os.remove(i)
        self.quit()
        self.destroy()
        exit()

    def _openImage(self):
        self.imageFileName=tkinter.filedialog.askopenfilename(initialdir='/',title="Select an Image",filetypes=(("jpg files","*.jpg"),("png files","*.png")))
        self.lastModified=self.imageFileName
        self.tempReset=self.imageFileName
        if len(self.imageFileName)==0: return
        self.currentImage=PIL.ImageTk.PhotoImage(PIL.Image.open(self.imageFileName))
        self.resetImage=PIL.ImageTk.PhotoImage(PIL.Image.open(self.imageFileName))
        for i in self.imageIdDS:
            self.imageCanvas.delete(self.imageId)
        self.imageId=self.imageCanvas.create_image(500,300,image=self.currentImage,anchor="center")
        self.imageIdDS.append(self.imageId)
        self._enableButtons()
        self._enableOptions()
        self._populateDetails()
        self.imageDS.append(self.currentImage)
        self.actionDS.append(self.imageFileName)
    def _populateDetails(self):
        imageData=cv2.imread(self.imageFileName)
        if self.first==0:
            self.detailCanvas.create_text(2,2,font=tkinter.font.Font(family="verdana",size=14),text="Image Details:",anchor="nw")
            self.detailsName=self.detailCanvas.create_text(2,30,font=tkinter.font.Font(family="verdana",size=10),text=f"Name: {pathlib.Path(self.imageFileName).name}",anchor="nw")
            self.detailsDimension=self.detailCanvas.create_text(2,45,font=tkinter.font.Font(family="verdana",size=10),text=f"Dimensions: {imageData.shape[1]}x{imageData.shape[0]}",anchor="nw")
            self.detailsSize=self.detailCanvas.create_text(2,60,font=tkinter.font.Font(family="verdana",size=10),text=f"Size: {pathlib.Path(self.imageFileName).stat().st_size//1024} KB",anchor="nw")
            self.detailsPath=self.detailCanvas.create_text(2,75,font=tkinter.font.Font(family="verdana",size=10),text=f"Path: {self.imageFileName}",anchor="nw")
            self.first=1
        else:
            self.detailCanvas.delete(self.detailsName)
            self.detailCanvas.delete(self.detailsDimension)
            self.detailCanvas.delete(self.detailsSize)
            self.detailCanvas.delete(self.detailsPath)
            self.detailsName=self.detailCanvas.create_text(2,30,font=tkinter.font.Font(family="verdana",size=10),text=f"Name: {pathlib.Path(self.imageFileName).name}",anchor="nw")
            self.detailsDimension=self.detailCanvas.create_text(2,45,font=tkinter.font.Font(family="verdana",size=10),text=f"Dimensions: {imageData.shape[1]}x{imageData.shape[0]}",anchor="nw")
            self.detailsSize=self.detailCanvas.create_text(2,60,font=tkinter.font.Font(family="verdana",size=10),text=f"Size: {pathlib.Path(self.imageFileName).stat().st_size//1024} KB",anchor="nw")
            self.detailsPath=self.detailCanvas.create_text(2,75,font=tkinter.font.Font(family="verdana",size=10),text=f"Path: {self.imageFileName}",anchor="nw")
    def _resetImage(self):
        #print("In Reset")
        for i in self.imageIdDS:
            self.imageCanvas.delete(self.imageId)
        self.currentImage=self.resetImage
        self.imageId=self.imageCanvas.create_image(500,300,image=self.currentImage,anchor="center")
        self.imageIdDS.append(self.imageId)
        self.imageFileName=self.tempReset
        self.lastModified=self.imageFileName
        for i in self.actionDS:
            #print(type(i))
            if i==self.tempReset: continue
            if pathlib.Path(i).is_file():
                os.remove(i)
        self.imageDS=[]
        self.actionDS=[]
        self.imageDS.append(self.currentImage)
        self.actionDS.append(self.tempReset)
        self.undoPointer=0
        #print(f"->{type(self.imageFileName)}")
        os.chdir("C:\\pyprojects\\photolab\\backup")

    def _grayScale(self):
        for i in self.imageIdDS:
            self.imageCanvas.delete(self.imageId)
        if self.currentImage==None: return
        imageData=cv2.imread(self.imageFileName)
        for r in range(imageData.shape[0]):
            for c in range(imageData.shape[1]):
                pixel=imageData[r][c]
                red=int(pixel[2])*0.3
                green=int(pixel[1])*0.59
                blue=int(pixel[0])*0.11
                total=red+blue+green
                imageData[r][c]=(total,total,total)
        cv2.imwrite("gScale.jpg",imageData)
        self.currentImage=PIL.ImageTk.PhotoImage(PIL.Image.open("gScale.jpg"))
        self.imageFileName=str(pathlib.Path("gScale.jpg"))
        self.lastModified=self.imageFileName
        self.imageId=self.imageCanvas.create_image(500,300,image=self.currentImage,anchor="center")
        self.imageIdDS.append(self.imageId)
        self.imageDS.append(self.currentImage)
        self.actionDS.append("gScale.jpg")
        self.undoPointer+=1
    def _contrast(self):
        self.miniWindow=tkinter.Tk()
        self.miniWindow.title("Set Contrast")
        self.miniWindow.iconbitmap("icons/logo.ico")
        self.miniWindow.geometry("250x150")
        self.scale=tkinter.ttk.Scale(self.miniWindow,orient=tkinter.HORIZONTAL,from_=-255,to=255,cursor="circle",length=200)
        self.scale.set(0)
        self.scale.place(x=25,y=50)
        self.miniWindow.okButton=tkinter.ttk.Button(self.miniWindow,text="Set",command=self.contrastHandler)
        self.miniWindow.okButton.place(x=90,y=100)

    def contrastHandler(self):
        for i in self.imageIdDS:
            self.imageCanvas.delete(self.imageId)
        contrast=int(self.scale.get())
        if self.currentImage==None: return
        self.miniWindow.destroy()
        imageData=cv2.imread(self.imageFileName)
        f=(259*(contrast+255))/(255*(259-contrast))
        for r in range(imageData.shape[0]):
            for c in range(imageData.shape[1]):
                rgb=imageData[r][c]
                red=rgb[2]
                green=rgb[1]
                blue=rgb[0]
                newRed=(f*(red-128))+128
                newGreen=(f*(green-128))+128
                newBlue=(f*(blue-128))+128
                if newRed>255: newRed=255
                if newRed<0: newRed=0
                if newGreen>255: newGreen=255
                if newGreen<0: newGreen=0
                if newBlue>255: newBlue=255
                if newBlue<0: newBlue=0
                imageData[r][c]=(newBlue,newGreen,newRed)
        cv2.imwrite("contrastImage.jpg",imageData)
        self.currentImage=PIL.ImageTk.PhotoImage(PIL.Image.open("contrastImage.jpg"))
        self.imageFileName=str(pathlib.Path("contrastImage.jpg"))
        self.lastModified=self.imageFileName
        self.imageId=self.imageCanvas.create_image(500,300,image=self.currentImage,anchor="center")
        self.imageIdDS.append(self.imageId)
        self.imageDS.append(self.currentImage)
        self.actionDS.append("contrastImage.jpg")
        self.undoPointer+=1

    def _brightness(self):
        self.miniWindow=tkinter.Tk()
        self.miniWindow.title("Set Brightness")
        self.miniWindow.iconbitmap("icons/logo.ico")
        self.miniWindow.geometry("250x150")
        self.scale=tkinter.ttk.Scale(self.miniWindow,orient=tkinter.HORIZONTAL,from_=-255,to=255,cursor="circle",length=200)
        self.scale.set(0)
        self.scale.place(x=25,y=50)
        self.miniWindow.okButton=tkinter.ttk.Button(self.miniWindow,text="Set",command=self.brightnessHandler)
        self.miniWindow.okButton.place(x=90,y=100)

    def brightnessHandler(self):
        for i in self.imageIdDS:
            self.imageCanvas.delete(self.imageId)
        brightness=int(self.scale.get())
        if self.currentImage==None: return
        self.miniWindow.destroy()
        imageData=cv2.imread(self.imageFileName)
        for r in range(imageData.shape[0]):
            for c in range(imageData.shape[1]):
                rgb=imageData[r][c]
                red=rgb[2]
                green=rgb[1]
                blue=rgb[0]
                red+=brightness
                green+=brightness
                blue+=brightness
                if red>255: red=255
                if red<0: red=0
                if green>255: green=255
                if green<0: green=0
                if blue>255: blue=255
                if blue<0: blue=0
                imageData[r][c]=(blue,green,red)
        cv2.imwrite("brightnessImage.jpg",imageData)
        self.currentImage=PIL.ImageTk.PhotoImage(PIL.Image.open("brightnessImage.jpg"))
        self.imageFileName=str(pathlib.Path("brightnessImage.jpg"))
        self.lastModified=self.imageFileName
        self.imageId=self.imageCanvas.create_image(500,300,image=self.currentImage,anchor="center")
        self.imageIdDS.append(self.imageId)
        self.imageDS.append(self.currentImage)
        self.actionDS.append("brightnessImage.jpg")
        self.undoPointer+=1
    def _rotateRight(self):
        for i in self.imageIdDS:
            self.imageCanvas.delete(self.imageId)
        if self.currentImage==None: return
        imageData=cv2.imread(self.imageFileName)
        oldR=imageData.shape[0]
        oldC=imageData.shape[1]
        newImage=numpy.zeros((oldC,oldR,3))
        
        r=0
        while r<oldR:
            c=0
            while c<oldC:
                newImage[c][oldR-r-1]=imageData[r][c]
                c+=1
            r+=1
        cv2.imwrite("rotateRight.jpg",newImage)
        self.currentImage=PIL.ImageTk.PhotoImage(PIL.Image.open("rotateRight.jpg"))
        self.imageFileName=str(pathlib.Path("rotateRight.jpg"))
        self.lastModified=self.imageFileName
        self.imageId=self.imageCanvas.create_image(500,300,image=self.currentImage,anchor="center")
        self.imageIdDS.append(self.imageId)
        self.imageDS.append(self.currentImage)
        self.actionDS.append("rotateRight.jpg")
        self.undoPointer+=1
    def _rotateLeft(self):
        for i in self.imageIdDS:
            self.imageCanvas.delete(self.imageId)
        if self.currentImage==None: return
        imageData=cv2.imread(self.imageFileName)
        oldR=imageData.shape[0]
        oldC=imageData.shape[1]
        newImage=numpy.zeros((oldC,oldR,3))
        
        c=0
        while c<oldC:
            r=0
            while r<oldR:
                newImage[oldC-c-1][r]=imageData[r][c]
                r+=1
            c+=1
        cv2.imwrite("rotateLeft.jpg",newImage)
        self.currentImage=PIL.ImageTk.PhotoImage(PIL.Image.open("rotateLeft.jpg"))
        self.imageFileName=str(pathlib.Path("rotateLeft.jpg"))
        self.lastModified=self.imageFileName
        self.imageId=self.imageCanvas.create_image(500,300,image=self.currentImage,anchor="center")
        self.imageIdDS.append(self.imageId)
        self.imageDS.append(self.currentImage)
        self.actionDS.append("rotateLeft.jpg")
        self.undoPointer+=1
    def _cropImage(self):
        self.x=None
        self.y=None
        self.x1=None
        self.y1=None
        self.miniWindow=tkinter.Tk()
        self.miniWindow.title("Crop Image")
        self.miniWindow.geometry("300x200")
        self.miniWindow.iconbitmap("icons/logo.ico")
        self.miniWindow.start=tkinter.ttk.Label(self.miniWindow,text="Start Point Coordinates",font=("Arial Bold",10))
        self.miniWindow.start.place(x=90,y=10)
        self.miniWindow.cropX=tkinter.ttk.Label(self.miniWindow,text="x-coordinate")
        self.miniWindow.cropX.place(x=15,y=35)
        self.miniWindow.cropY=tkinter.ttk.Label(self.miniWindow,text="y-coordinate")
        self.miniWindow.cropY.place(x=15,y=60)
        self.miniWindow.end=tkinter.ttk.Label(self.miniWindow,text="Crop Size Dimensions",font=("Arial Bold",10))
        self.miniWindow.end.place(x=90,y=85)
        self.miniWindow.cropX1=tkinter.ttk.Label(self.miniWindow,text="x-axis")
        self.miniWindow.cropX1.place(x=15,y=110)
        self.miniWindow.cropY1=tkinter.ttk.Label(self.miniWindow,text="y-axis")
        self.miniWindow.cropY1.place(x=15,y=135)
        self.miniWindow.entry1=tkinter.ttk.Entry(self.miniWindow,width=10)
        self.miniWindow.entry1.place(x=120,y=35)
        self.miniWindow.entry2=tkinter.ttk.Entry(self.miniWindow,width=10)
        self.miniWindow.entry2.place(x=120,y=60)
        self.miniWindow.entry3=tkinter.ttk.Entry(self.miniWindow,width=10)
        self.miniWindow.entry3.place(x=120,y=110)
        self.miniWindow.entry4=tkinter.ttk.Entry(self.miniWindow,width=10)
        self.miniWindow.entry4.place(x=120,y=135)
        self.miniWindow.okButton=tkinter.ttk.Button(self.miniWindow,text="Crop",command=self.getImageCropped)
        self.miniWindow.okButton.place(x=110,y=170)

    def getImageCropped(self):
        for i in self.imageIdDS:
            self.imageCanvas.delete(self.imageId)
        if self.currentImage==None: return
        
        imageData=cv2.imread(self.imageFileName)
        c1=int(self.miniWindow.entry1.get())
        r1=int(self.miniWindow.entry2.get())
        c2=int(self.miniWindow.entry3.get())-1
        r2=int(self.miniWindow.entry4.get())-1
        cropFrom=(c1,r1)
        cropSize=(c2,r2)
        if r2>=imageData.shape[0]: r2=imageData.shape[0]-1
        if c2>=imageData.shape[1]: c2=imageData.shape[1]-1
        cropSize=(c2-c1+1,r2-r1+1)
        newImage=numpy.zeros((cropSize[1],cropSize[0],3))
        rr=0
        r=r1
        count=0
        
        while r<=r2:
            cc=0
            c=c1
            while c<=c2:
                count+=1
                newImage[rr][cc]=imageData[r][c]
                c+=1
                cc+=1
            rr+=1
            r+=1
        cv2.imwrite("crop.jpg",newImage)
        self.currentImage=PIL.ImageTk.PhotoImage(PIL.Image.open("crop.jpg"))
        self.imageFileName=str(pathlib.Path("crop.jpg"))
        self.lastModified=self.imageFileName
        self.imageId=self.imageCanvas.create_image(500,300,image=self.currentImage,anchor="center")
        self.imageIdDS.append(self.imageId)
        self.miniWindow.destroy()
        self.imageDS.append(self.currentImage)
        self.actionDS.append("crop.jpg")
        self.undoPointer+=1
    def _flipHorizontal(self):
        for i in self.imageIdDS:
            self.imageCanvas.delete(self.imageId)
        if self.currentImage==None: return
        imageData=cv2.imread(self.imageFileName)
        height=int(imageData.shape[0])
        width=int(imageData.shape[1])
        newImage=numpy.zeros((imageData.shape[0],imageData.shape[1],3))
        i=0
        while i<height:
            e=0
            f=width-1
            while e<width:
                newImage[i][e]=imageData[i][f]
                e+=1
                f-=1
            i+=1
        cv2.imwrite("flipH.jpg",newImage)
        self.currentImage=PIL.ImageTk.PhotoImage(PIL.Image.open("flipH.jpg"))
        self.imageFileName=str(pathlib.Path("flipH.jpg"))
        self.lastModified=self.imageFileName
        self.imageId=self.imageCanvas.create_image(500,300,image=self.currentImage,anchor="center")
        self.imageIdDS.append(self.imageId)
        self.imageDS.append(self.currentImage)
        self.actionDS.append("flipH.jpg")
        self.undoPointer+=1
    def _flipVertical(self):
        for i in self.imageIdDS:
            self.imageCanvas.delete(self.imageId)
        if self.currentImage==None: return
        imageData=cv2.imread(self.imageFileName)
        height=int(imageData.shape[0])
        width=int(imageData.shape[1])
        newImage=numpy.zeros((imageData.shape[0],imageData.shape[1],3))
        i=0
        while i<width:
            e=0
            f=height-1
            while e<height:
                newImage[e][i]=imageData[f][i]
                e+=1
                f-=1
            i+=1
        cv2.imwrite("flipV.jpg",newImage)
        self.currentImage=PIL.ImageTk.PhotoImage(PIL.Image.open("flipV.jpg"))
        self.imageFileName=str(pathlib.Path("flipV.jpg"))
        self.lastModified=self.imageFileName
        self.imageId=self.imageCanvas.create_image(500,300,image=self.currentImage,anchor="center")
        self.imageIdDS.append(self.imageId)
        self.imageDS.append(self.currentImage)
        self.actionDS.append("flipV.jpg")
        self.undoPointer+=1
    def _openImageShortcut(self,event):
        self._openImage()
    def _undoImage(self):
        #print(self.imageDS)
        #print(self.undoPointer)
        #print(self.actionDS)
        if self.undoPointer==0: 
            self.imageDS=[]
            self.actionDS=[]
            self.imageDS.append(self.currentImage)
            self.actionDS.append(self.imageFileName)
            return
        for i in self.imageIdDS:
            self.imageCanvas.delete(self.imageId)
        self.imageId=self.imageCanvas.create_image(500,300,image=self.imageDS[self.undoPointer-1],anchor="center")
        self.imageIdDS.append(self.imageId)
        self.undoPointer-=1
        #print(f"Image File Name: {self.imageFileName}")
        self.currentImage=self.imageDS[self.undoPointer]
        self.imageFileName=self.actionDS[self.undoPointer]
        self.lastModified=self.imageFileName
    def _saveFile(self):
        self.savee=str(tkinter.filedialog.asksaveasfile(initialdir='/',initialfile='image.jpg',defaultextension='.jpg',title="Save Image",filetypes=(("jpg files","*.jpg"),("png files","*.png"))).name)
        #print(self.savee)
        p=self.savee[::-1]
        a=p.find("/")
        fileName=self.savee[::-1][0:a][::-1]
        #print(fileName)
        self.savee=p[a+1:]
        self.savee=self.savee[::-1]
        #print(self.savee)
        imageData=cv2.imread(self.imageFileName)
        os.chdir(pathlib.Path(self.savee))
        cv2.imwrite(fileName,imageData)
        self._releaseTempImages()
    def _releaseTempImages(self):
        #print("\n\nReleasing\n")
        os.chdir("C:\\pyprojects\\photolab\\backup")
        for i in self.actionDS:
            #print(type(i))
            if i==self.tempReset: continue
            if pathlib.Path(i).is_file():
                os.remove(i)
    def _customBorder(self):
        self.x=None
        self.y=None
        self.x1=None
        self.y1=None
        self.miniWindow=tkinter.Tk()
        self.miniWindow.title("Set Image Border")
        self.miniWindow.geometry("300x200")
        self.miniWindow.pickColorButton=tkinter.ttk.Button(self.miniWindow,text="Pick Color",command=self.getColorPicker)
        self.miniWindow.pickColorButton.place(x=10,y=20)
        self.miniWindow.askWidthLabel=tkinter.ttk.Label(self.miniWindow,text="Choose Width")
        self.miniWindow.askWidthLabel.place(x=10,y=50)
        self.miniWindow.widthComboBox=tkinter.ttk.Combobox(self.miniWindow,width=20,state="readonly")
        self.miniWindow.widthComboBox.place(x=100,y=50)
        self.miniWindow.widthComboBox['values']=("2","4","6","8","10")
        self.miniWindow.iconbitmap("icons/logo.ico")
        self.miniWindow.okButton=tkinter.ttk.Button(self.miniWindow,text="Process",command=self.getImageBorder)
        self.miniWindow.okButton.place(x=110,y=170)
    def getImageBorder(self):
        for i in self.imageIdDS:
            self.imageCanvas.delete(self.imageId)
        borderWidth=int(self.miniWindow.widthComboBox.get())
        self.miniWindow.destroy()
        imageData=cv2.imread(self.imageFileName)
        height=imageData.shape[0]
        width=imageData.shape[1]
        r=0
        while r<width:
            for i in range(borderWidth):
                imageData[i][r]=self.colorPickerTuple
                imageData[height-(i+1)][r]=self.colorPickerTuple
            r+=1
        r=width
        c=0
        while c<height:
            for i in range(borderWidth):
                imageData[c][i]=self.colorPickerTuple
                imageData[c][width-(i+1)]=self.colorPickerTuple
            c+=1
        cv2.imwrite("borderImage.jpg",imageData)
        self.currentImage=PIL.ImageTk.PhotoImage(PIL.Image.open("borderImage.jpg"))
        self.imageFileName=str(pathlib.Path("borderImage.jpg"))
        self.lastModified=self.imageFileName
        self.imageId=self.imageCanvas.create_image(500,300,image=self.currentImage,anchor="center")
        self.imageIdDS.append(self.imageId)
        self.imageDS.append(self.currentImage)
        self.actionDS.append("borderImage.jpg")
        self.undoPointer+=1
    def _normalBorder(self):
        for i in self.imageIdDS:
            self.imageCanvas.delete(self.imageId)
        borderWidth=5
        self.colorPickerTuple=(0,0,255)
        imageData=cv2.imread(self.imageFileName)
        height=imageData.shape[0]
        width=imageData.shape[1]
        r=0
        while r<width:
            for i in range(borderWidth):
                imageData[i][r]=self.colorPickerTuple
                imageData[height-(i+1)][r]=self.colorPickerTuple
            r+=1
        r=width
        c=0
        while c<height:
            for i in range(borderWidth):
                imageData[c][i]=self.colorPickerTuple
                imageData[c][width-(i+1)]=self.colorPickerTuple
            c+=1
        cv2.imwrite("borderImage.jpg",imageData)
        self.currentImage=PIL.ImageTk.PhotoImage(PIL.Image.open("borderImage.jpg"))
        self.imageFileName=str(pathlib.Path("borderImage.jpg"))
        self.lastModified=self.imageFileName
        self.imageId=self.imageCanvas.create_image(500,300,image=self.currentImage,anchor="center")
        self.imageIdDS.append(self.imageId)
        self.imageDS.append(self.currentImage)
        self.actionDS.append("borderImage.jpg")
        self.undoPointer+=1
    def getColorPicker(self):
        color_code = tkinter.colorchooser.askcolor(title ="Choose color")
        a=color_code[0][0]
        b=color_code[0][1]
        c=color_code[0][2]
        self.colorPickerTuple=(c,b,a)
        self.miniWindow.displayLabel=tkinter.ttk.Label(self.miniWindow,text=f"Choosen Color Code is {color_code[1]}",font=("Verdana",10))
        self.miniWindow.displayLabel.place(x=40,y=80)
        self.miniWindow.focus_force()
    def _zoomIn(self):
        for i in self.imageIdDS:
            self.imageCanvas.delete(self.imageId)
        imageData=cv2.imread(self.imageFileName)
        w=int(imageData.shape[1]*2)
        h=int(imageData.shape[0]*2)
        dim=(w,h)
        img=cv2.resize(imageData,dim,interpolation=cv2.INTER_CUBIC)
        cv2.imwrite("zoomedIn.jpg",img)
        self.currentImage=PIL.ImageTk.PhotoImage(PIL.Image.open("zoomedIn.jpg"))
        self.imageFileName=str(pathlib.Path("zoomedIn.jpg"))
        self.lastModified=self.imageFileName
        self.imageId=self.imageCanvas.create_image(500,300,image=self.currentImage,anchor="center")
        self.imageIdDS.append(self.imageId)
        self.imageDS.append(self.currentImage)
        self.actionDS.append("zoomedIn.jpg")
        self.undoPointer+=1
    def _zoomOut(self):
        for i in self.imageIdDS:
            self.imageCanvas.delete(self.imageId)
        imageData=cv2.imread(self.imageFileName)
        w=int(imageData.shape[1]*0.5)
        h=int(imageData.shape[0]*0.5)
        dim=(w,h)
        img=cv2.resize(imageData,dim,interpolation=cv2.INTER_CUBIC)
        cv2.imwrite("zoomedOut.jpg",img)
        self.currentImage=PIL.ImageTk.PhotoImage(PIL.Image.open("zoomedOut.jpg"))
        self.imageFileName=str(pathlib.Path("zoomedOut.jpg"))
        self.lastModified=self.imageFileName
        self.imageId=self.imageCanvas.create_image(500,300,image=self.currentImage,anchor="center")
        self.imageIdDS.append(self.imageId)
        self.imageDS.append(self.currentImage)
        self.actionDS.append("zoomedOut.jpg")
        self.undoPointer+=1
    def _magnify(self,per,fileName):
        
        per=per/100
        for i in self.imageIdDS:
            self.imageCanvas.delete(self.imageId)
        imageData=cv2.imread(fileName)
        w=int(imageData.shape[1]*per)
        h=int(imageData.shape[0]*per)
        dim=(w,h)
        img=cv2.resize(imageData,dim,interpolation=cv2.INTER_CUBIC)
        cv2.imwrite("magnified.jpg",img)
        self.currentImage=PIL.ImageTk.PhotoImage(PIL.Image.open("magnified.jpg"))
        self.imageFileName=str(pathlib.Path("magnified.jpg"))
        self.imageId=self.imageCanvas.create_image(500,300,image=self.currentImage,anchor="center")
        self.imageIdDS.append(self.imageId)
        self.imageDS.append(self.currentImage)
        self.actionDS.append("magnified.jpg")
        self.undoPointer+=1
    def _laplacian(self):
        imageData=cv2.imread(self.ImageFileName)
    def windowClosing(self):
        self._exit()
    def _drawLine(self):
        self.x=None
        self.y=None
        self.x1=None
        self.y1=None
        self.miniWindow=tkinter.Tk()
        self.miniWindow.title("Draw Line")
        self.miniWindow.geometry("300x300")
        self.miniWindow.iconbitmap("icons/logo.ico")
        self.miniWindow.start=tkinter.ttk.Label(self.miniWindow,text="Start Point Coordinates",font=("Arial Bold",10))
        self.miniWindow.start.place(x=90,y=10)
        self.miniWindow.cropX=tkinter.ttk.Label(self.miniWindow,text="x-coordinate")
        self.miniWindow.cropX.place(x=15,y=35)
        self.miniWindow.cropY=tkinter.ttk.Label(self.miniWindow,text="y-coordinate")
        self.miniWindow.cropY.place(x=15,y=60)
        self.miniWindow.end=tkinter.ttk.Label(self.miniWindow,text="End Point Coordinates",font=("Arial Bold",10))
        self.miniWindow.end.place(x=90,y=85)
        self.miniWindow.cropX1=tkinter.ttk.Label(self.miniWindow,text="x-axis")
        self.miniWindow.cropX1.place(x=15,y=110)
        self.miniWindow.cropY1=tkinter.ttk.Label(self.miniWindow,text="y-axis")
        self.miniWindow.cropY1.place(x=15,y=135)
        self.miniWindow.entry1=tkinter.ttk.Entry(self.miniWindow,width=10)
        self.miniWindow.entry1.place(x=120,y=35)
        self.miniWindow.entry2=tkinter.ttk.Entry(self.miniWindow,width=10)
        self.miniWindow.entry2.place(x=120,y=60)
        self.miniWindow.entry3=tkinter.ttk.Entry(self.miniWindow,width=10)
        self.miniWindow.entry3.place(x=120,y=110)
        self.miniWindow.entry4=tkinter.ttk.Entry(self.miniWindow,width=10)
        self.miniWindow.entry4.place(x=120,y=135)
        self.miniWindow.pickColorButton=tkinter.ttk.Button(self.miniWindow,text="Pick Color",command=self.colorPickerShapes)
        self.miniWindow.pickColorButton.place(x=15,y=160)
        self.miniWindow.iconbitmap("icons/logo.ico")
        self.miniWindow.askWidthLabel=tkinter.ttk.Label(self.miniWindow,text="Choose Thickness")
        self.miniWindow.askWidthLabel.place(x=10,y=240)
        self.miniWindow.widthComboBox=tkinter.ttk.Combobox(self.miniWindow,width=20,state="readonly")
        self.miniWindow.widthComboBox.place(x=110,y=240)
        self.miniWindow.widthComboBox['values']=("2","4","6","8","10")
        self.miniWindow.okButton=tkinter.ttk.Button(self.miniWindow,text="Draw",command=self.getLineDrawn)
        self.miniWindow.okButton.place(x=110,y=270)
    def getLineDrawn(self):
        for i in self.imageIdDS:
            self.imageCanvas.delete(self.imageId)
        self.x=int(self.miniWindow.entry1.get())
        self.y=int(self.miniWindow.entry2.get())
        self.x1=int(self.miniWindow.entry3.get())
        self.y1=int(self.miniWindow.entry4.get())
        thickness=int(self.miniWindow.widthComboBox.get())
        self.miniWindow.destroy()
        imageData=cv2.imread(self.imageFileName)
        start=(self.x, self.y)
        end=(self.x1, self.y1)
        cv2.line(imageData,start,end,self.colorPickerTuple, thickness)
        cv2.imwrite("drawLine.jpg",imageData)
        self.currentImage=PIL.ImageTk.PhotoImage(PIL.Image.open("drawLine.jpg"))
        self.imageFileName=str(pathlib.Path("drawLine.jpg"))
        self.lastModified=self.imageFileName
        self.imageId=self.imageCanvas.create_image(500,300,image=self.currentImage,anchor="center")
        self.imageIdDS.append(self.imageId)
        self.imageDS.append(self.currentImage)
        self.actionDS.append("drawLine.jpg")
        self.undoPointer+=1
    def colorPickerShapes(self):
        color_code = tkinter.colorchooser.askcolor(title ="Choose color")
        a=color_code[0][0]
        b=color_code[0][1]
        c=color_code[0][2]
        self.colorPickerTuple=(c,b,a)
        self.miniWindow.displayLabel=tkinter.ttk.Label(self.miniWindow,text=f"Choosen Color Code is {color_code[1]}",font=("Verdana",10))
        self.miniWindow.displayLabel.place(x=40,y=200)
        self.miniWindow.focus_force()
    def _mailImage(self):
        self.miniWindow=tkinter.Tk()
        self.miniWindow.iconbitmap("icons/logo.ico")
        self.miniWindow.title("Send Image as E-mail")
        self.miniWindow.geometry("400x300")
        self.miniWindow.iconbitmap("icons/logo.ico")
        self.miniWindow.sendToLabel=tkinter.ttk.Label(self.miniWindow,text="Send to",font=("Verdana",10))
        self.miniWindow.sendToLabel.place(x=15,y=10)
        self.miniWindow.sendToEntry=tkinter.ttk.Entry(self.miniWindow,width=40)
        self.miniWindow.sendToEntry.place(x=80,y=10)
        self.miniWindow.subjectLabel=tkinter.ttk.Label(self.miniWindow,text="Subject",font=("Verdana",10))
        self.miniWindow.subjectLabel.place(x=15,y=40)
        self.miniWindow.subjectEntry=tkinter.ttk.Entry(self.miniWindow,width=40)
        self.miniWindow.subjectEntry.place(x=80,y=40)
        self.miniWindow.textLabel=tkinter.ttk.Label(self.miniWindow,text="Message\n(optional) ",font=("Verdana",10))
        self.miniWindow.textLabel.place(x=15,y=80)
        self.miniWindow.textArea=tkinter.scrolledtext.ScrolledText(self.miniWindow,width=30,height=8)
        self.miniWindow.textArea.place(x=80,y=80)
        self.miniWindow.sendButton=tkinter.ttk.Button(self.miniWindow,text="Send",command=self.sendMail)
        self.miniWindow.sendButton.place(x=100,y=250)
    def sendMail(self):
        self.focus_force()
        sendTo=self.miniWindow.sendToEntry.get()
        subject=self.miniWindow.subjectEntry.get()
        message=self.miniWindow.textArea.get(1.0,'end')
        self.miniWindow.destroy()
        yag = yagmail.SMTP(user='tanishqrawatcs19@acropolis.in', password='626423083089824164791710200111102001')
        yag.send(to=sendTo, subject=subject, contents=message,attachments=self.imageFileName)
    def _drawCircle(self):
        self.x=None
        self.y=None
        self.x1=None
        self.y1=None
        self.miniWindow=tkinter.Tk()
        self.miniWindow.title("Draw Circle")
        self.miniWindow.geometry("300x250")
        self.miniWindow.iconbitmap("icons/logo.ico")
        self.miniWindow.start=tkinter.ttk.Label(self.miniWindow,text="Center Point Coordinates",font=("Arial Bold",10))
        self.miniWindow.start.place(x=15,y=10)
        self.miniWindow.cropX=tkinter.ttk.Label(self.miniWindow,text="x-coordinate")
        self.miniWindow.cropX.place(x=15,y=35)
        self.miniWindow.cropY=tkinter.ttk.Label(self.miniWindow,text="y-coordinate")
        self.miniWindow.cropY.place(x=15,y=60)
        self.miniWindow.cropY=tkinter.ttk.Label(self.miniWindow,text="radius")
        self.miniWindow.cropY.place(x=15,y=100)
        self.miniWindow.entry1=tkinter.ttk.Entry(self.miniWindow,width=10)
        self.miniWindow.entry1.place(x=120,y=35)
        self.miniWindow.entry2=tkinter.ttk.Entry(self.miniWindow,width=10)
        self.miniWindow.entry2.place(x=120,y=60)
        self.miniWindow.entry3=tkinter.ttk.Entry(self.miniWindow,width=10)
        self.miniWindow.entry3.place(x=120,y=100)
        self.miniWindow.pickColorButton=tkinter.ttk.Button(self.miniWindow,text="Pick Color",command=self.colorPickerShapes)
        self.miniWindow.pickColorButton.place(x=15,y=135)
        self.miniWindow.iconbitmap("icons/logo.ico")
        self.miniWindow.askWidthLabel=tkinter.ttk.Label(self.miniWindow,text="Choose Thickness")
        self.miniWindow.askWidthLabel.place(x=10,y=170)
        self.miniWindow.widthComboBox=tkinter.ttk.Combobox(self.miniWindow,width=20,state="readonly")
        self.miniWindow.widthComboBox.place(x=110,y=170)
        self.miniWindow.widthComboBox['values']=("2","4","6","8","10")
        self.miniWindow.okButton=tkinter.ttk.Button(self.miniWindow,text="Draw",command=self.getCircleDrawn)
        self.miniWindow.okButton.place(x=110,y=220)
    def getCircleDrawn(self):
        for i in self.imageIdDS:
            self.imageCanvas.delete(self.imageId)
        self.x=int(self.miniWindow.entry1.get())
        self.y=int(self.miniWindow.entry2.get())
        radius=int(self.miniWindow.entry3.get())
        thickness=int(self.miniWindow.widthComboBox.get())
        self.miniWindow.destroy()
        imageData=cv2.imread(self.imageFileName)
        center=(self.x, self.y)
        cv2.circle(imageData, center, radius, self.colorPickerTuple, thickness)
        cv2.imwrite("drawCircle.jpg",imageData)
        self.currentImage=PIL.ImageTk.PhotoImage(PIL.Image.open("drawCircle.jpg"))
        self.imageFileName=str(pathlib.Path("drawCircle.jpg"))
        self.lastModified=self.imageFileName
        self.imageId=self.imageCanvas.create_image(500,300,image=self.currentImage,anchor="center")
        self.imageIdDS.append(self.imageId)
        self.imageDS.append(self.currentImage)
        self.actionDS.append("drawCircle.jpg")
        self.undoPointer+=1

    def _drawRectangle(self):
        self.x=None
        self.y=None
        self.x1=None
        self.y1=None
        self.miniWindow=tkinter.Tk()
        self.miniWindow.title("Draw Rectangle")
        self.miniWindow.geometry("300x300")
        self.miniWindow.iconbitmap("icons/logo.ico")
        self.miniWindow.start=tkinter.ttk.Label(self.miniWindow,text="Start Point Coordinates",font=("Arial Bold",10))
        self.miniWindow.start.place(x=90,y=10)
        self.miniWindow.cropX=tkinter.ttk.Label(self.miniWindow,text="x-coordinate")
        self.miniWindow.cropX.place(x=15,y=35)
        self.miniWindow.cropY=tkinter.ttk.Label(self.miniWindow,text="y-coordinate")
        self.miniWindow.cropY.place(x=15,y=60)
        self.miniWindow.end=tkinter.ttk.Label(self.miniWindow,text="End Point Coordinates",font=("Arial Bold",10))
        self.miniWindow.end.place(x=90,y=85)
        self.miniWindow.cropX1=tkinter.ttk.Label(self.miniWindow,text="x-axis")
        self.miniWindow.cropX1.place(x=15,y=110)
        self.miniWindow.cropY1=tkinter.ttk.Label(self.miniWindow,text="y-axis")
        self.miniWindow.cropY1.place(x=15,y=135)
        self.miniWindow.entry1=tkinter.ttk.Entry(self.miniWindow,width=10)
        self.miniWindow.entry1.place(x=120,y=35)
        self.miniWindow.entry2=tkinter.ttk.Entry(self.miniWindow,width=10)
        self.miniWindow.entry2.place(x=120,y=60)
        self.miniWindow.entry3=tkinter.ttk.Entry(self.miniWindow,width=10)
        self.miniWindow.entry3.place(x=120,y=110)
        self.miniWindow.entry4=tkinter.ttk.Entry(self.miniWindow,width=10)
        self.miniWindow.entry4.place(x=120,y=135)
        self.miniWindow.pickColorButton=tkinter.ttk.Button(self.miniWindow,text="Pick Color",command=self.colorPickerShapes)
        self.miniWindow.pickColorButton.place(x=15,y=160)
        self.miniWindow.iconbitmap("icons/logo.ico")
        self.miniWindow.askWidthLabel=tkinter.ttk.Label(self.miniWindow,text="Choose Thickness")
        self.miniWindow.askWidthLabel.place(x=10,y=240)
        self.miniWindow.widthComboBox=tkinter.ttk.Combobox(self.miniWindow,width=20,state="readonly")
        self.miniWindow.widthComboBox.place(x=110,y=240)
        self.miniWindow.widthComboBox['values']=("2","4","6","8","10")
        self.miniWindow.okButton=tkinter.ttk.Button(self.miniWindow,text="Draw",command=self.getRectangleDrawn)
        self.miniWindow.okButton.place(x=110,y=270)
    def getRectangleDrawn(self):
        for i in self.imageIdDS:
            self.imageCanvas.delete(self.imageId)
        self.x=int(self.miniWindow.entry1.get())
        self.y=int(self.miniWindow.entry2.get())
        self.x1=int(self.miniWindow.entry3.get())
        self.y1=int(self.miniWindow.entry4.get())
        thickness=int(self.miniWindow.widthComboBox.get())
        self.miniWindow.destroy()
        imageData=cv2.imread(self.imageFileName)
        start=(self.x, self.y)
        end=(self.x1, self.y1)
        cv2.rectangle(imageData,start,end,self.colorPickerTuple, thickness)
        cv2.imwrite("drawRectangle.jpg",imageData)
        self.currentImage=PIL.ImageTk.PhotoImage(PIL.Image.open("drawRectangle.jpg"))
        self.imageFileName=str(pathlib.Path("drawRectangle.jpg"))
        self.lastModified=self.imageFileName
        self.imageId=self.imageCanvas.create_image(500,300,image=self.currentImage,anchor="center")
        self.imageIdDS.append(self.imageId)
        self.imageDS.append(self.currentImage)
        self.actionDS.append("drawRectangle.jpg")
        self.undoPointer+=1
    def _medianBlurring(self):
        self.miniWindow=tkinter.Tk()
        self.miniWindow.title("Blur Image")
        self.miniWindow.iconbitmap("icons/logo.ico")
        self.miniWindow.geometry("250x150")
        self.miniWindow.scale=tkinter.ttk.Scale(self.miniWindow,orient=tkinter.HORIZONTAL,from_=3,to=11,cursor="circle",length=200)
        self.miniWindow.scale.set(0)
        self.miniWindow.scale.place(x=25,y=50)
        self.miniWindow.okButton=tkinter.ttk.Button(self.miniWindow,text="Set",command=self.medianBlurring)
        self.miniWindow.okButton.place(x=90,y=100)
    def medianBlurring(self):
        for i in self.imageIdDS:
            self.imageCanvas.delete(self.imageId)
        impact=int(self.miniWindow.scale.get())
        if not impact%2: impact+=1
        print(impact)
        self.miniWindow.destroy()
        imageData=cv2.imread(self.imageFileName)
        median = cv2.medianBlur(imageData,impact)
        cv2.imwrite("medianBlurred.jpg",median)
        self.currentImage=PIL.ImageTk.PhotoImage(PIL.Image.open("medianBlurred.jpg"))
        self.imageFileName=str(pathlib.Path("medianBlurred.jpg"))
        self.lastModified=self.imageFileName
        self.imageId=self.imageCanvas.create_image(500,300,image=self.currentImage,anchor="center")
        self.imageIdDS.append(self.imageId)
        self.imageDS.append(self.currentImage)
        self.actionDS.append("medianBlurred.jpg")
        self.undoPointer+=1
    def _gaussian(self):
        for i in self.imageIdDS:
            self.imageCanvas.delete(self.imageId)
        imageData=cv2.imread(self.imageFileName)
        imageData=cv2.GaussianBlur(imageData, (7, 7), 0)
        cv2.imwrite("gaussianSmoothing.jpg",imageData)
        self.currentImage=PIL.ImageTk.PhotoImage(PIL.Image.open("gaussianSmoothing.jpg"))
        self.imageFileName=str(pathlib.Path("gaussianSmoothing.jpg"))
        self.lastModified=self.imageFileName
        self.imageId=self.imageCanvas.create_image(500,300,image=self.currentImage,anchor="center")
        self.imageIdDS.append(self.imageId)
        self.imageDS.append(self.currentImage)
        self.actionDS.append("gaussianSmoothing.jpg")
        self.undoPointer+=1
    def _drawText(self):
        self.colorPickerTuple=(0,0,0)
        self.miniWindow=tkinter.Tk()
        self.miniWindow.title("Draw Text")
        self.miniWindow.geometry("300x270")
        self.miniWindow.iconbitmap("icons/logo.ico")
        self.miniWindow.start=tkinter.ttk.Label(self.miniWindow,text="Text Coordinates",font=("Arial Bold",10))
        self.miniWindow.start.place(x=90,y=10)
        self.miniWindow.cropX=tkinter.ttk.Label(self.miniWindow,text="x-coordinate")
        self.miniWindow.cropX.place(x=15,y=35)
        self.miniWindow.cropY=tkinter.ttk.Label(self.miniWindow,text="y-coordinate")
        self.miniWindow.cropY.place(x=15,y=60)
        self.miniWindow.entry1=tkinter.ttk.Entry(self.miniWindow,width=10)
        self.miniWindow.entry1.place(x=120,y=35)
        self.miniWindow.entry2=tkinter.ttk.Entry(self.miniWindow,width=10)
        self.miniWindow.entry2.place(x=120,y=60)
        self.miniWindow.askTextLabel=tkinter.ttk.Label(self.miniWindow,text="Enter Text")
        self.miniWindow.askTextLabel.place(x=15,y=90)
        self.miniWindow.entry3=tkinter.ttk.Entry(self.miniWindow,width=30)
        self.miniWindow.entry3.place(x=90,y=90)
        self.miniWindow.askFontLabel=tkinter.ttk.Label(self.miniWindow,text="Choose Font")
        self.miniWindow.askFontLabel.place(x=15,y=120)
        self.miniWindow.fontComboBox=tkinter.ttk.Combobox(self.miniWindow,width=20,state="readonly")
        self.miniWindow.fontComboBox.place(x=100,y=120)
        self.miniWindow.fontComboBox['values']=("Style-1","Style-2","Style-3","Style-4","Style-5","Style-6","Style-7","Style-8")
        self.miniWindow.askFontSizeLabel=tkinter.ttk.Label(self.miniWindow,text="Choose Font Size")
        self.miniWindow.askFontSizeLabel.place(x=15,y=150)
        self.miniWindow.sizeComboBox=tkinter.ttk.Combobox(self.miniWindow,width=20,state="readonly")
        self.miniWindow.sizeComboBox.place(x=120,y=150)
        self.miniWindow.sizeComboBox['values']=("10","12","14","16","20","22","24")
        self.miniWindow.pickColorButton=tkinter.ttk.Button(self.miniWindow,text="Pick Color",command=self.colorPickerShapes)
        self.miniWindow.pickColorButton.place(x=15,y=175)
        self.miniWindow.okButton=tkinter.ttk.Button(self.miniWindow,text="Draw",command=self.getTextDrawn)
        self.miniWindow.okButton.place(x=110,y=240)
    def getTextDrawn(self):
        for i in self.imageIdDS:
            self.imageCanvas.delete(self.imageId)
        x=int(self.miniWindow.entry1.get())
        y=int(self.miniWindow.entry2.get())
        text=self.miniWindow.entry3.get()
        font=self.miniWindow.fontComboBox.get()[6:]
        fonts=[cv2.FONT_HERSHEY_SIMPLEX,cv2.FONT_HERSHEY_DUPLEX,cv2.FONT_HERSHEY_PLAIN,cv2.FONT_HERSHEY_COMPLEX,cv2.FONT_HERSHEY_TRIPLEX,cv2.FONT_HERSHEY_COMPLEX_SMALL,cv2.FONT_HERSHEY_SCRIPT_SIMPLEX,cv2.FONT_HERSHEY_SCRIPT_COMPLEX]
        font=fonts[int(font)-1]
        fontSize=self.miniWindow.sizeComboBox.get()
        self.miniWindow.destroy()
        imageData=cv2.imread(self.imageFileName)
        image = cv2.putText(imageData, text,(x,y), font,1,self.colorPickerTuple, 4, cv2.LINE_AA)
        cv2.imwrite("textImage.jpg",image)
        self.currentImage=PIL.ImageTk.PhotoImage(PIL.Image.open("textImage.jpg"))
        self.imageFileName=str(pathlib.Path("textImage.jpg"))
        self.lastModified=self.imageFileName
        self.imageId=self.imageCanvas.create_image(500,300,image=self.currentImage,anchor="center")
        self.imageIdDS.append(self.imageId)
        self.imageDS.append(self.currentImage)
        self.actionDS.append("textImage.jpg")
        self.undoPointer+=1
    def _blur(self):
        for i in self.imageIdDS:
            self.imageCanvas.delete(self.imageId)
        imageData=cv2.imread(self.imageFileName)
        blurImg = cv2.blur(imageData,(10,10))
        cv2.imwrite("blur.jpg",blurImg)
        self.currentImage=PIL.ImageTk.PhotoImage(PIL.Image.open("blur.jpg"))
        self.imageFileName=str(pathlib.Path("blur.jpg"))
        self.lastModified=self.imageFileName
        self.imageId=self.imageCanvas.create_image(500,300,image=self.currentImage,anchor="center")
        self.imageIdDS.append(self.imageId)
        self.imageDS.append(self.currentImage)
        self.actionDS.append("blur.jpg")
        self.undoPointer+=1
    def _bilateral(self):
        for i in self.imageIdDS:
            self.imageCanvas.delete(self.imageId)
        imageData=cv2.imread(self.imageFileName)
        bilateral = cv2.bilateralFilter(imageData, 5, 70, 70)
        cv2.imwrite("bilateral.jpg",bilateral)
        self.currentImage=PIL.ImageTk.PhotoImage(PIL.Image.open("bilateral.jpg"))
        self.imageFileName=str(pathlib.Path("bilateral.jpg"))
        self.lastModified=self.imageFileName
        self.imageId=self.imageCanvas.create_image(500,300,image=self.currentImage,anchor="center")
        self.imageIdDS.append(self.imageId)
        self.imageDS.append(self.currentImage)
        self.actionDS.append("bilateral.jpg")
        self.undoPointer+=1
    def _box(self):
        for i in self.imageIdDS:
            self.imageCanvas.delete(self.imageId)
        imageData=Image.open(self.imageFileName)
        imageData =imageData.filter(ImageFilter.BoxBlur(4))
        imageData.save("boxBlur.jpg")
        self.currentImage=PIL.ImageTk.PhotoImage(PIL.Image.open("boxBlur.jpg"))
        self.imageFileName=str(pathlib.Path("boxBlur.jpg"))
        self.lastModified=self.imageFileName
        self.imageId=self.imageCanvas.create_image(500,300,image=self.currentImage,anchor="center")
        self.imageIdDS.append(self.imageId)
        self.imageDS.append(self.currentImage)
        self.actionDS.append("boxBlur.jpg")
        self.undoPointer+=1
    def _transition(self,style):
        for i in self.imageIdDS:
            self.imageCanvas.delete(self.imageId)
        style=style-1
        if style==-1:
            style=random.randint(0,14)
        lst=[cv2.COLOR_BGR2RGB,cv2.COLOR_BGR2RGBA,cv2.COLOR_BGR2GRAY,cv2.COLOR_BGR2HLS,cv2.COLOR_BGR2HLS_FULL,cv2.COLOR_BGR2HSV,cv2.COLOR_BGR2HSV_FULL,cv2.COLOR_BGR2LAB,cv2.COLOR_BGR2LUV,cv2.COLOR_BGR2Lab,cv2.COLOR_BGR2Luv,cv2.COLOR_BGR2XYZ,cv2.COLOR_BGR2YCR_CB,cv2.COLOR_BGR2YCrCb,cv2.COLOR_BGR2YUV]
        imageData=cv2.imread(self.imageFileName)
        imageData=cv2.cvtColor(imageData,lst[style])
        cv2.imwrite("transition.jpg",imageData)
        self.currentImage=PIL.ImageTk.PhotoImage(PIL.Image.open("transition.jpg"))
        self.imageFileName=str(pathlib.Path("transition.jpg"))
        self.lastModified=self.imageFileName
        self.imageId=self.imageCanvas.create_image(500,300,image=self.currentImage,anchor="center")
        self.imageIdDS.append(self.imageId)
        self.imageDS.append(self.currentImage)
        self.actionDS.append("transition.jpg")
        self.undoPointer+=1
def main():
    sp.destroy()
    window=Window()
sp=SplashWindow()
sp.after(11000,main)
tkinter.mainloop()