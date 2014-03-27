from sys import byteorder
from array import array
from struct import pack

import pyaudio
import wave

THRESHOLD = 500
CHUNK = 1024
FORMAT = pyaudio.paInt16
RATE = 16000

def is_silent(snd_data):
	return max(snd_data) < THRESHOLD

def normalize(snd_data):	#Average the volume out
	MAXIMUM = 16384
	r = array('h')
	times = float(MAXIMUM)/max(abs(i) for i in snd_data)
	for i in snd_data:
		r.append(int(i*times))
	return r

def trim(snd_data):	#Trim the blank spots at the start and end
	def _trim(snd_data):
		snd_started = False
		r = array('h')
		for i in snd_data:
			if not snd_started and abs(i)>THRESHOLD:
				snd_started = True
				r.append(i)

			elif snd_started:
				r.append(i)
		return r

	snd_data = _trim(snd_data) # Trim to the left
	snd_data.reverse()	 # Trim to the right
	snd_data = _trim(snd_data)
	snd_data.reverse()
	return snd_data

def record():
	p = pyaudio.PyAudio()
	stream = p.open(format=FORMAT, channels=1, rate=RATE,input=True, output=True,frames_per_buffer=CHUNK)
	num_silent = 0
	snd_started = False
	r = array('h')
	while 1:
		#print 'recording'	# little endian, signed short
		snd_data = array('h', stream.read(CHUNK))
		if byteorder == 'big':
			snd_data.byteswap()
		r.extend(snd_data)
		silent = is_silent(snd_data)	
		print "started:" ,snd_started," silent=",num_silent
		if silent and snd_started:
			num_silent += 1
		elif not silent and not snd_started:
			snd_started = True
		if not silent and snd_started and num_silent>0:
			num_silent=0
		if snd_started and num_silent > 50:
			break
	sample_width = p.get_sample_size(FORMAT)
	stream.stop_stream()
	stream.close()
	p.terminate()
	r = normalize(r)
	r = trim(r)
	#r = add_silence(r, 0.5)
	return sample_width, r

def record_to_file(path):	#Records from the microphone and outputs the resulting data to 'path'
	sample_width, data = record()
	data = pack('<' + ('h'*len(data)), *data)
	wf = wave.open(path, 'wb')	
	wf.setnchannels(1)
	wf.setsampwidth(sample_width)
	wf.setframerate(RATE)
	wf.writeframes(data)
	print 'written'
	wf.close()
