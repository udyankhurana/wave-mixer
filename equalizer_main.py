#(2, 2, 44100, 192386, 'NONE', 'not compressed')
#nchannels(mono/stereo), sampwidth(16bit), framerate(fps), nframes, comptype(none), compname(not compressed)

	#########NOT HANDLED ALL CASES############
import wave, struct, pyaudio, sys
class wave_functions():
	def __init__(self):
		self.int_data=[]	# modify this for now, and issue a read if we want to start fresh
		self.wave_info=[]
	
	def read(self,filename):
		self.int_data=[]
		f=wave.open(filename,'r')
		self.wave_info=f.getparams()	
		encoded_data=f.readframes(self.wave_info[3])
		f.close()
		if self.wave_info[1]==1:	#8bit
			comp_fmt="%iB" %(self.wave_info[3]*self.wave_info[0])
		elif self.wave_info[1]==2:	#16bit
			comp_fmt="%ih" %(self.wave_info[3]*self.wave_info[0])
		self.int_data=struct.unpack(comp_fmt,encoded_data)
		self.int_data=list(self.int_data)
	
	def write(self):
		x=wave.open('201202101_temp.wav','w')
		x.setparams(self.wave_info)
		if self.wave_info[1]==1:	#8bit
			comp_fmt="%iB" %(self.wave_info[3]*self.wave_info[0])
		elif self.wave_info[1]==2:	#16bit
			comp_fmt="%ih" %(self.wave_info[3]*self.wave_info[0])
		reencoded_data=struct.pack(comp_fmt,*(self.int_data))
		x.writeframes(reencoded_data)
		x.close()
		
	def Amplitude_Scaling(self,scale_factor):	#AMPLITUDE SCALING				
		for i in range(len(self.int_data)):
			if self.int_data[i]*scale_factor>32767:
				self.int_data[i]=32767
			elif self.int_data[i]*scale_factor<-32767:
				self.int_data[i]=-32767
			else:
				self.int_data[i]=int(self.int_data[i]*scale_factor)	
		

	def Time_Reversal(self):	#TIME REVERSAL
		lendata=len(self.int_data)
		if self.wave_info[0]==1:	#mono
			self.int_data.reverse()
		elif self.wave_info[0]==2:	#stereo
			left_side=[]
			right_side=[]
			for i in range(lendata):
				if i%2==0:
					left_side.append(self.int_data[i])
				else:
					right_side.append(self.int_data[i])
			left_side.reverse()
			right_side.reverse()
			j=0
			for i in range(lendata/2):
				self.int_data[j]=left_side[i]
				self.int_data[j+1]=right_side[i]
				j+=2

	def Time_Scaling(self,scale_factor):	#TIME SCALING
		wave_info2=list(self.wave_info)
		sc=1.0*scale_factor
		i=0
		var=i*sc
		int_data2=[]
		while (var<len(self.int_data)):
			if var.is_integer() and int(var)%self.wave_info[0]==0:
				int_data2.append(self.int_data[int(var)])
				if self.wave_info[0]==2:	#stereo
					int_data2.append(self.int_data[int(var)+1])
			else:
				int_data2.append(0)
				if self.wave_info[0]==2:
					int_data2.append(0)
			i+=1
			if self.wave_info[0]==2:
				i+=1
			var=i*sc
		wave_info2[3]=(wave_info2[3]*1.0)/scale_factor
		if not wave_info2[3].is_integer():
			wave_info2[3]=int(wave_info2[3])+1
		else:
			wave_info2[3]=int(wave_info2[3])
		self.wave_info=list(wave_info2)
		self.int_data=list(int_data2)

	def Time_Shifting(self,shift):	
		frames_to_shift=int(shift*self.wave_info[2])
		wave_info2=list(self.wave_info)
		wave_info2[3]=self.wave_info[3]+frames_to_shift
		int_data2=[]
		if shift>0:
			for i in range(frames_to_shift):
				int_data2.append(0)
				if wave_info2[0]==2:	#if stereo
					int_data2.append(0)
			for i in range(len(self.int_data)):
				int_data2.append(self.int_data[i])			
		else:
			z=abs(frames_to_shift)
			for i in range(z*wave_info2[0],len(self.int_data)):
					int_data2.append(self.int_data[i])
		self.wave_info=list(wave_info2)
		self.int_data=list(int_data2)

	def Mixing(self,datas,infos):
		if len(datas)>1:	
			aa=1		
			for i in range(len(infos)-1):			
				if infos[i][0]!=infos[i+1][0] or infos[i][1]!=infos[i+1][1] and infos[i][2]!=infos[i+1][2]:
					aa=0
			
			if aa==1:	#MIXING STARTS					
				x=[]			
				for i in range(len(datas)):
					x.append(len(datas[i]))
				mini=x.index(min(x))		
				maxi=x.index(max(x))		
				self.wave_info=list(infos[maxi])
				int_data2=list(datas[maxi])
				if len(datas)==2:			
					for i in range(x[mini]):
						int_data2[i]+=datas[mini][i]
						if int_data2[i]>32767:
							int_data2[i]=32767
						elif int_data2[i]<-32767:
							int_data2[i]=-32767
				elif len(datas)==3:
					for i in range(x[mini]):
						int_data2[i]+=datas[mini][i]+datas[3-mini-maxi][i]
						if int_data2[i]>32767:
							int_data2[i]=32767
						elif int_data2[i]<-32767:
							int_data2[i]=-32767
					for i in range(x[mini],x[3-mini-maxi]):
						int_data2[i]+=datas[3-mini-maxi][i]
						if int_data2[i]>32767:
							int_data2[i]=32767
						elif int_data2[i]<-32767:
							int_data2[i]=-32767
			self.int_data=list(int_data2)
		else:
			self.int_data=datas[0]
			self.wave_info=infos[0]

	def Modulation(self,datas,infos):	
		if len(datas)>1:
			aa=1		
			for i in range(len(infos)-1):			
				if infos[i][0]!=infos[i+1][0] or infos[i][1]!=infos[i+1][1] and infos[i][2]!=infos[i+1][2]:
					aa=0
			
			if aa==1:	#MODULATING STARTS					
				x=[]			
				for i in range(len(datas)):
					x.append(len(datas[i]))
				#print x
				mini=x.index(min(x))		
				maxi=x.index(max(x))		
				self.wave_info=list(infos[maxi])
				int_data2=list(datas[maxi])
				if len(datas)==2:			
					for i in range(x[mini]):
						int_data2[i]*=datas[mini][i]
						if int_data2[i]>32767:
							int_data2[i]=32767
						elif int_data2[i]<-32767:
							int_data2[i]=-32767
				elif len(datas)==3:
					for i in range(x[mini]):
						int_data2[i]*=(datas[mini][i]*datas[3-mini-maxi][i])
						if int_data2[i]>32767:
							int_data2[i]=32767
						elif int_data2[i]<-32767:
							int_data2[i]=-32767
					for i in range(x[mini],x[3-mini-maxi]):
						int_data2[i]*=datas[3-mini-maxi][i]
						if int_data2[i]>32767:
							int_data2[i]=32767
						elif int_data2[i]<-32767:
							int_data2[i]=-32767
			self.int_data=list(int_data2)
		else:
			self.int_data=datas[0]
			self.wave_info=infos[0]


	def play_audio(self,filename):
		chunk = 1024 #size of data read at one go
		wf = wave.open(filename, 'rb')
		x=wf.getparams()
		p = pyaudio.PyAudio()	#creates a PyAudio class object
		stream = p.open(format=p.get_format_from_width(x[1]),channels=x[0],rate=x[2],output=True) #open stream based on file attributes
		data = wf.readframes(chunk)	#read a chunk of data
		while data != '':	#while there is some data, keep writing to output stream and reading more data
		    stream.write(data)	
		    data = wf.readframes(chunk)

		stream.stop_stream()	#can use for pausing audio	
		stream.close()	#close ouput stream (end audio)
		p.terminate()	#terminate pyAudio object
	
	def record_audio(self,recording_time):	#record audio from microphone
		CHUNK = 1024
		FORMAT = pyaudio.paInt16	#16bit
		CHANNELS = 1	#mono
		RATE = 16000	#16 kHz
		WAVE_OUTPUT_FILENAME = "rec_output.wav"
		p = pyaudio.PyAudio()
		stream = p.open(format=FORMAT,channels=CHANNELS,rate=RATE,input=True,frames_per_buffer=CHUNK)
		print("** Recording Starts **")
		frames = []
		for i in range(0, int(RATE / CHUNK * recording_time)):
			data = stream.read(CHUNK)
			frames.append(data)
		print("** Recording Ends **")
		stream.stop_stream()
		stream.close()
		p.terminate()
		wf = wave.open(WAVE_OUTPUT_FILENAME, 'wb')
		wf.setnchannels(CHANNELS)
		wf.setsampwidth(p.get_sample_size(FORMAT))
		wf.setframerate(RATE)
		wf.writeframes(b''.join(frames))
		wf.close()
