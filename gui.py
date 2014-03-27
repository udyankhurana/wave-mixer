import pygtk, gtk, os, signal, time, gobject, os.path, pango
from equalizer_main import *
from record_audio import *

class Equalizer:
	def __init__(self):
		if os.path.exists("rec_output.wav"):
			os.system("rm rec_output.wav")		
		self.window=gtk.Window(gtk.WINDOW_TOPLEVEL)
		self.window.set_size_request(800, 650)
		self.window.set_border_width(10)
		self.window.set_title("Wave Mixer")
		self.window.connect("delete_event", lambda w,e: gtk.main_quit())
		self.window.set_icon_from_file(self.get_resource_path("icons/icon.png"))
		self.fixed=gtk.Fixed() 
		self.window.add(self.fixed)
		self.timer = gobject.timeout_add (100, self.progress_timeout, self)				
		
		self.paused=[0]*3
		self.mix_pid=1111111111	#initialized to value which wont have a process
		self.mod_pid=1111111111	#so that stop does not kill window
		self.rec_pid=1111111111	
		self.recplay_pid=1111111111	
		self.rec_pause=0
		self.mod_pause=0
		self.mix_pause=0
		self.waveobj=[]
		self.files=['']*3
		self.ascale_values=[1]*3
		self.tscale_values=[1]*3
		self.tshift_values=[0]*3
		self.pid_values=[1111111111]*3
		self.tr_values=[False,False,False]
		self.mod_values=[False,False,False]
		self.mix_values=[False,False,False]
		self.time_elapsed=[0]*5	
		self.time_running=[0]*5
		self.progressbar=[]	# 0-2 normal, 3 - mix, 4 - mod	

		label = gtk.Label()			
		label.set_use_markup(True)
		label.set_markup("<big><b><u>WAVE MIXER</u></b></big>")
		self.fixed.put(label,300,1)

		for i in range(5):
			self.waveobj.append(wave_functions())

		for i in range(3):		
			filechooserbutton = gtk.FileChooserButton("Select A File", None)
			filechooserbutton.connect("file-set", self.file_selected,i)        
			filechooserbutton.set_width_chars(15)  
			self.fixed.put(filechooserbutton,20+270*i,35)

			label_as = gtk.Label("Amplitude")
			self.fixed.put(label_as,20+270*i,80)  			

			ascale=gtk.HScale() 		
			ascale.set_range(0,5) 
			ascale.set_increments(0.5, 1) 
			ascale.set_digits(2)	#no of decimal places
			ascale.set_value(1) 	#default value
			ascale.set_size_request(160, 45) 
			ascale.connect("value-changed", self.ascale_moved,i) 
			self.fixed.put(ascale,20+270*i,110)    

			label_tshift = gtk.Label("Time Shift")
			self.fixed.put(label_tshift,20+270*i,170)		

			tshift=gtk.HScale() 		
			tshift.set_range(-1,1) 
			tshift.set_increments(0.1, 1) 
			tshift.set_digits(2) 
			tshift.set_value(0) 
			tshift.set_size_request(160, 45) 
			tshift.connect("value-changed", self.tshift_moved,i) 
			self.fixed.put(tshift,20+270*i,190)    

			label_tscale = gtk.Label("Time Scaling")
			self.fixed.put(label_tscale,20+270*i,250)		

			tscale=gtk.HScale() 		
			tscale.set_range(0,8) 
			tscale.set_increments(0.5, 1) 
			tscale.set_digits(1) 
			tscale.set_value(1) 
			tscale.set_size_request(160, 45) 
			tscale.connect("value-changed", self.tscale_moved,i) 
			self.fixed.put(tscale,20+270*i,270)  		

			tr = gtk.CheckButton("Time Reversal")
			tr.connect("toggled",self.change_tr,i)
			self.fixed.put(tr,20+270*i,330) 

			mod = gtk.CheckButton("Select for Modulation")
			mod.connect("toggled",self.change_mod,i)
			self.fixed.put(mod,20+270*i,360)	

			mix = gtk.CheckButton("Select for Mixing")	
			mix.connect("toggled",self.change_mix,i)
			self.fixed.put(mix,20+270*i,390)
			
			image=gtk.Image()
			#image.set_from_file("pbg.jpg")
			pixbuf = gtk.gdk.pixbuf_new_from_file("icons/ut.jpg")
			scaled_buf = pixbuf.scale_simple(30,30,gtk.gdk.INTERP_BILINEAR)	#scaling images
			image.set_from_pixbuf(scaled_buf)
			image.show()
			playbutton = gtk.Button()	#if doesnt work write "Play" 
			playbutton.add(image)
			playbutton.connect("clicked", self.button_clicked,i)
			self.fixed.put(playbutton,10+270*i,430) 
			
			image=gtk.Image()
			pixbuf = gtk.gdk.pixbuf_new_from_file("icons/pause.jpg")
			scaled_buf = pixbuf.scale_simple(30,30,gtk.gdk.INTERP_BILINEAR)
			image.set_from_pixbuf(scaled_buf)
			image.show()
			pausebutton = gtk.Button() #if doesnt work write "Pause/Resume" 
			pausebutton.add(image)
			pausebutton.connect("clicked", self.pausebutton_clicked,i)
			self.fixed.put(pausebutton,55+270*i,430) 

			image=gtk.Image()
			pixbuf = gtk.gdk.pixbuf_new_from_file("icons/stop.jpg")
			scaled_buf = pixbuf.scale_simple(30,30,gtk.gdk.INTERP_BILINEAR)
			image.set_from_pixbuf(scaled_buf)
			image.show()
			stopbutton = gtk.Button() 
			stopbutton.add(image)
			stopbutton.connect("clicked", self.stopbutton_clicked,i)
			self.fixed.put(stopbutton,100+270*i,430)

			progressbar = gtk.ProgressBar(None) #For Mix
			progressbar.set_orientation(gtk.PROGRESS_LEFT_TO_RIGHT) 
			progressbar.set_fraction(0.0) 
			self.progressbar.append(progressbar)
			self.fixed.put(progressbar,10+270*i,480)
		
		label = gtk.Label()			
		label.set_use_markup(True)
		label.set_markup("<b><u>MIX AND PLAY</u></b>")
		self.fixed.put(label,20,530)		

		image=gtk.Image()
		pixbuf = gtk.gdk.pixbuf_new_from_file("icons/ut.jpg")
		scaled_buf = pixbuf.scale_simple(30,30,gtk.gdk.INTERP_BILINEAR)
		image.set_from_pixbuf(scaled_buf)
		image.show()
		mixbutton = gtk.Button() #if doesnt work write "Mix and Play" 
		mixbutton.add(image)
		mixbutton.connect("clicked", self.mixbutton_clicked)
		self.fixed.put(mixbutton,20,560)

		image=gtk.Image()
		pixbuf = gtk.gdk.pixbuf_new_from_file("icons/pause.jpg")
		scaled_buf = pixbuf.scale_simple(30,30,gtk.gdk.INTERP_BILINEAR)
		image.set_from_pixbuf(scaled_buf)
		image.show()
		mixpause = gtk.Button() 
		mixpause.add(image)
		mixpause.connect("clicked", self.mixpause_clicked)
		self.fixed.put(mixpause,65,560)

		image=gtk.Image()
		pixbuf = gtk.gdk.pixbuf_new_from_file("icons/stop.jpg")
		scaled_buf = pixbuf.scale_simple(30,30,gtk.gdk.INTERP_BILINEAR)
		image.set_from_pixbuf(scaled_buf)
		image.show()
		mixstop = gtk.Button()
		mixstop.add(image)
		mixstop.connect("clicked", self.mixstop_clicked)
		self.fixed.put(mixstop,110,560)
		
		progressbar = gtk.ProgressBar(None) #For Mix
		progressbar.set_orientation(gtk.PROGRESS_LEFT_TO_RIGHT) 
		progressbar.set_fraction(0.0) 
		self.progressbar.append(progressbar)
		self.fixed.put(progressbar,20,610)

		label = gtk.Label()			
		label.set_use_markup(True)
		label.set_markup("<b><u>MODULATE AND PLAY</u></b>")
		self.fixed.put(label,280,530)		

		image=gtk.Image()
		pixbuf = gtk.gdk.pixbuf_new_from_file("icons/ut.jpg")
		scaled_buf = pixbuf.scale_simple(30,30,gtk.gdk.INTERP_BILINEAR)
		image.set_from_pixbuf(scaled_buf)
		image.show()
		modbutton = gtk.Button() #if doesnt work write "Mod and Play" 
		modbutton.add(image)
		modbutton.connect("clicked", self.modbutton_clicked)
		self.fixed.put(modbutton,290,560)

		image=gtk.Image()
		pixbuf = gtk.gdk.pixbuf_new_from_file("icons/pause.jpg")
		scaled_buf = pixbuf.scale_simple(30,30,gtk.gdk.INTERP_BILINEAR)
		image.set_from_pixbuf(scaled_buf)
		image.show()
		modpause = gtk.Button() 
		modpause.add(image)
		modpause.connect("clicked", self.modpause_clicked)
		self.fixed.put(modpause,335,560)

		image=gtk.Image()
		pixbuf = gtk.gdk.pixbuf_new_from_file("icons/stop.jpg")
		scaled_buf = pixbuf.scale_simple(30,30,gtk.gdk.INTERP_BILINEAR)
		image.set_from_pixbuf(scaled_buf)
		image.show()
		modstop = gtk.Button()
		modstop.add(image)
		modstop.connect("clicked", self.modstop_clicked)
		self.fixed.put(modstop,380,560)
		
		progressbar = gtk.ProgressBar(None) #For Mix
		progressbar.set_orientation(gtk.PROGRESS_LEFT_TO_RIGHT) 
		progressbar.set_fraction(0.0) 
		self.progressbar.append(progressbar)
		self.fixed.put(progressbar,280,610)

		label = gtk.Label()			
		label.set_use_markup(True)
		label.set_markup("<b><u>RECORD AUDIO</u></b>")
		self.fixed.put(label,560,530)	
		
		image=gtk.Image()
		pixbuf = gtk.gdk.pixbuf_new_from_file("icons/record.jpg")
		scaled_buf = pixbuf.scale_simple(40,40,gtk.gdk.INTERP_BILINEAR)
		image.set_from_pixbuf(scaled_buf)
		image.show()
		recbutton = gtk.Button()
		recbutton.add(image)
		recbutton.connect("clicked", self.recbutton_clicked)
		self.fixed.put(recbutton,520,560)	

		#quote = "<span foreground='black' size='15000'>Play Last\nRecording</span>"
		image=gtk.Image()
		pixbuf = gtk.gdk.pixbuf_new_from_file("icons/ut.jpg")
		scaled_buf = pixbuf.scale_simple(40,40,gtk.gdk.INTERP_BILINEAR)
		image.set_from_pixbuf(scaled_buf)
		image.show()
		recplay = gtk.Button()	#"Play Last Recording"
		recplay.add(image)
		recplay.connect("clicked", self.recplay_clicked)
		self.fixed.put(recplay,575,560)

		image=gtk.Image()
		pixbuf = gtk.gdk.pixbuf_new_from_file("icons/pause.jpg")
		scaled_buf = pixbuf.scale_simple(40,40,gtk.gdk.INTERP_BILINEAR)
		image.set_from_pixbuf(scaled_buf)
		image.show()
		recpause = gtk.Button()	#"Play Last Recording"
		recpause.add(image)
		recpause.connect("clicked", self.recpause_clicked)
		self.fixed.put(recpause,630,560)

		image=gtk.Image()
		pixbuf = gtk.gdk.pixbuf_new_from_file("icons/stop.jpg")
		scaled_buf = pixbuf.scale_simple(40,40,gtk.gdk.INTERP_BILINEAR)
		image.set_from_pixbuf(scaled_buf)
		image.show()
		recstop = gtk.Button()	#"Play Last Recording"
		recstop.add(image)
		recstop.connect("clicked", self.recstop_clicked)
		self.fixed.put(recstop,685,560)

		self.window.show_all()

	def progress_timeout(self,pbobj):
		for i in range(3): 
			if(self.pid_values[i]!=1111111111): 		
				self.progressbar[i].set_fraction(((self.time_elapsed[i]+time.time()-self.time_running[i])/(self.waveobj[i].wave_info[3]/self.waveobj[i].wave_info[2])))
		if(self.mix_pid!=1111111111): 
			self.progressbar[3].set_fraction(((self.time_elapsed[3]+time.time()-self.time_running[3])/(self.waveobj[3].wave_info[3]/self.waveobj[3].wave_info[2])))  		
		if(self.mod_pid!=1111111111): 
			self.progressbar[4].set_fraction(((self.time_elapsed[4]+time.time()-self.time_running[4])/(self.waveobj[4].wave_info[3]/self.waveobj[4].wave_info[2]))) 
		return True

	def get_resource_path(self,rel_path):
		dir_of_py_file = os.path.dirname(__file__)
	    	rel_path_to_resource = os.path.join(dir_of_py_file, rel_path)
	    	abs_path_to_resource = os.path.abspath(rel_path_to_resource)
	    	return abs_path_to_resource

	def file_selected(self, widget,val):
		self.files[val]=widget.get_filename()

	def ascale_moved(self, widget,val):
		self.ascale_values[val]=widget.get_value()

	def tshift_moved(self, widget,val):
		self.tshift_values[val]=widget.get_value()

	def tscale_moved(self, widget,val):
		self.tscale_values[val]=widget.get_value()

	def change_tr(self,widget,val):
		self.tr_values[val]=widget.get_active()
		print "timereverse=",self.tr_values[val]

	def change_mod(self,widget,val):
		self.mod_values[val]=widget.get_active()
		print "mod=",self.mod_values[val]

	def change_mix(self,widget,val):
		self.mix_values[val]=widget.get_active()
		print "mix=",self.mix_values[val]

	def button_clicked(self, widget,val):	
		print "PLAY BUTTON PRESSED from val=%d" %(val)
		if self.files[val]!='':			
			self.waveobj[val].read(self.files[val])
			if(self.ascale_values[val]!=1):
				self.waveobj[val].Amplitude_Scaling(self.ascale_values[val])
			if(self.tshift_values[val]!=0):
				self.waveobj[val].Time_Shifting(self.tshift_values[val])
			if(self.tscale_values[val]!=1):
				self.waveobj[val].Time_Scaling(self.tscale_values[val])
			if self.tr_values[val]==True:
				self.waveobj[val].Time_Reversal()
			self.waveobj[val].write()
			self.time_elapsed[val] = 0.0 
			self.time_running[val]=time.time()
			pid=os.fork()
			self.pid_values[val]=pid
			if pid==0:
				self.waveobj[val].play_audio('201202101_temp.wav')
				sys.exit(0)

	def pausebutton_clicked(self, widget,val):
		if self.pid_values[val]!=1111111111:
			print "Pause BUTTON PRESSED from val=%d" %(val)
			if self.paused[val]==1:
				self.paused[val]=0
				self.time_running[val] = time.time()
				os.kill(self.pid_values[val],signal.SIGCONT)	
			else:	
				os.kill(self.pid_values[val],signal.SIGSTOP)
				self.time_elapsed[val]= self.time_elapsed[val]+time.time()-self.time_running[val] 
				self.time_running[val] = 0.0
				self.paused[val]=1

	def stopbutton_clicked(self, widget,val):
		print "STOP BUTTON PRESSED from val=%d" %(val)
		self.progressbar[val].set_fraction(0.0)
		self.time_elapsed[val]=0 
		self.time_running[val] = time.time()
		if self.pid_values[val]!=1111111111:
			os.kill(self.pid_values[val],9)
		self.pid_values[val]=1111111111
	
	def modbutton_clicked(self, widget):
		print "MOD BUTTON PRESSED"		
		x=[]
		y=[]
		for val in range(3):
			if self.files[val]!='' and self.mod_values[val]==True:
				self.waveobj[val].read(self.files[val])
				if(self.ascale_values[val]!=1):
					self.waveobj[val].Amplitude_Scaling(self.ascale_values[val])
				if(self.tshift_values[val]!=0):
					self.waveobj[val].Time_Shifting(self.tshift_values[val])
				if(self.tscale_values[val]!=1):
					self.waveobj[val].Time_Scaling(self.tscale_values[val])
				if self.tr_values[val]==True:
					self.waveobj[val].Time_Reversal()
				x.append(self.waveobj[val].int_data)	
				y.append(self.waveobj[val].wave_info)
		if len(x)>0:	
			self.waveobj[4].Modulation(x,y)
			self.waveobj[4].write()
			self.time_elapsed[4] = 0.0 
			self.time_running[4]=time.time()
			pid=os.fork()
			self.mod_pid=pid
			if pid==0:
				self.waveobj[4].play_audio('201202101_temp.wav')
				sys.exit(0)

	def modpause_clicked(self, widget):
		if self.mod_pid!=1111111111:
			print "MODPause BUTTON PRESSED "
			if self.mod_pause==1:
				self.mod_pause=0
				self.time_running[4] = time.time()
				os.kill(self.mod_pid,signal.SIGCONT)	
			else:	
				os.kill(self.mod_pid,signal.SIGSTOP)
				self.time_elapsed[4]= self.time_elapsed[4]+time.time()-self.time_running[4] 
				self.time_running[4] = 0.0
				self.mod_pause=1

	
	def modstop_clicked(self, widget): 
		print "MODSTOP BUTTON PRESSED"
		self.progressbar[4].set_fraction(0.0)
		self.time_elapsed[4]=0 
		self.time_running[4] = time.time()
		if self.mod_pid!=1111111111:
			os.kill(self.mod_pid,9)
		self.mod_pid=1111111111 

	def mixbutton_clicked(self, widget):
		print "MIX BUTTON PRESSED"		
		x=[]
		y=[]
		for val in range(3):
			if self.files[val]!='' and self.mix_values[val]==True:
				self.waveobj[val].read(self.files[val])
				if(self.ascale_values[val]!=1):
					self.waveobj[val].Amplitude_Scaling(self.ascale_values[val])
				if(self.tshift_values[val]!=0):
					self.waveobj[val].Time_Shifting(self.tshift_values[val])
				if(self.tscale_values[val]!=1):
					self.waveobj[val].Time_Scaling(self.tscale_values[val])
				if self.tr_values[val]==True:
					self.waveobj[val].Time_Reversal()
				x.append(self.waveobj[val].int_data)	
				y.append(self.waveobj[val].wave_info)	
		if len(x)>0:
			self.waveobj[3].Mixing(x,y)
			self.waveobj[3].write()
			self.time_elapsed[3] = 0.0 
			self.time_running[3]=time.time()
			pid=os.fork()
			self.mix_pid=pid
			if pid==0:
			 	self.waveobj[3].play_audio('201202101_temp.wav')
				sys.exit(0)  
	
	def mixpause_clicked(self, widget):
		if self.mix_pid!=1111111111:
			print "MIXPause BUTTON PRESSED "
			if self.mix_pause==1:
				self.mix_pause=0
				self.time_running[3] = time.time()
				os.kill(self.mix_pid,signal.SIGCONT)	
			else:	
				os.kill(self.mix_pid,signal.SIGSTOP)
				self.time_elapsed[3]= self.time_elapsed[3]+time.time()-self.time_running[3] 
				self.time_running[3] = 0.0
				self.mix_pause=1

	def mixstop_clicked(self, widget): 
		print "MIXSTOP BUTTON PRESSED"
		self.progressbar[3].set_fraction(0.0)
		self.time_elapsed[3]=0 
		self.time_running[3] = time.time()
		if self.mix_pid!=1111111111:
			os.kill(self.mix_pid,9)
		self.mix_pid=1111111111
	
	def recbutton_clicked(self, widget):	
		print "RECOrD BUTTON PRESSED"
		pid=os.fork()
		self.rec_pid=pid
		if pid==0:
			record_to_file('rec_output.wav') #can't stop it urself but wont hang screen		
			sys.exit(0) 

	def recplay_clicked(self, widget):	
		print "PLAY RECOrDing BUTTON PRESSED"
		zz=wave_functions()
		pid=os.fork()
		self.recplay_pid=pid
		if pid==0:
			if os.path.exists("rec_output.wav"):			
				zz.play_audio('rec_output.wav')
			sys.exit(0) 

	def recpause_clicked(self, widget):
		if self.recplay_pid!=1111111111:
			print "RECPause BUTTON PRESSED "
			if self.rec_pause==1:
				self.rec_pause=0
				os.kill(self.recplay_pid,signal.SIGCONT)	
			else:	
				os.kill(self.recplay_pid,signal.SIGSTOP)
				self.rec_pause=1

	def recstop_clicked(self, widget): 
		print "RecSTOP BUTTON PRESSED"
		if self.recplay_pid!=1111111111:
			os.kill(self.recplay_pid,9)
		self.recplay_pid=1111111111

def main():
	gtk.main()
	return 0

if __name__ == "__main__":
	Equalizer()
	main()

