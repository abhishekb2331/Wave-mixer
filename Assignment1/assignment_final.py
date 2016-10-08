from multiprocessing import Process, Manager
from multiprocessing import Process, Value, Array
from multiprocessing import Process, Queue
from sys import byteorder
from array import array
from struct import pack
import gobject
import gtk
import contextlib
import sys
import os
import pygtk
import pyaudio
import wave
import sys
import struct
import signal
THRESHOLD = 00
CHUNK_SIZE = 1024
FORMAT = pyaudio.paInt16
RATE = 44100
record=[0]
rec_file=['']
#record.append(0)
par=[-1,-1,-1]
pause=[0,0,0]
sol=['out1.wav','out2.wav','out3.wav']
mixing_file="mix_out.wav"
mix_par=[-1,0,0]
mix_pause=[0,0,0]
modulate_file="mod_out.wav"
mod_par=[-1,0,0]
mod_pause=[0,0,0]
duration=[0,0,0,0,0]
elapsed=[0,0,0,0,0]
fil=['','','']
modul=[0,0,0]
play=[-1,-1,-1,-1,-1]
x=[]
x.append('')
x.append('')
x.append('')
list1=[]
list2=[]
list3=[]
class Base:
	def change(self,widget):
		rec_file[0]=self.text.get_text()

	def is_silent(self,snd_data):
 		"Returns 'True' if below the 'silent' threshold"
		return max(snd_data) < THRESHOLD
	def normalize(self,snd_data):
   		"Average the volume out"
    		MAXIMUM = 16384
    		times = float(MAXIMUM)/max(abs(i) for i in snd_data)

    		r = array('h')
   		for i in snd_data:
        		r.append(int(i*times))
    		return r
	def trim(self,snd_data):
 		"Trim the blank spots at the start and end"
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
		# Trim to the left
   		snd_data = _trim(snd_data)

    # Trim to the right
    		snd_data.reverse()
    		snd_data = _trim(snd_data)
    		snd_data.reverse()
    		return snd_data

	def add_silence(self,snd_data, seconds):	
    		"Add silence to the start and end of 'snd_data' of length 'seconds' (float)"
    		r = array('h', [0 for i in xrange(int(seconds*RATE))])
    		r.extend(snd_data)
    		r.extend([0 for i in xrange(int(seconds*RATE))])
    		return r
	
	def record(self,q,d):
    		"""
    			Record a word or words from the microphone and 
    			return the data as an array of signed shorts.

    			Normalizes the audio, trims silence from the 
    			start and end, and pads with 0.5 seconds of 
    			blank sound to make sure VLC et al can play 
    			it without getting chopped off.
    		"""
    		p = pyaudio.PyAudio()
    		stream = p.open(format=FORMAT, channels=1, rate=RATE,
        			input=True, output=True,
        			frames_per_buffer=CHUNK_SIZE)

    		num_silent = 0
    		snd_started = False

    		r = array('h')
		while 1:
			l=1
       			 # little endian, signed short
        		snd_data = array('h', stream.read(CHUNK_SIZE))
        		if byteorder == 'big':
            			snd_data.byteswap()
        		r.extend(snd_data)
        		silent = self.is_silent(snd_data)

        		if silent and snd_started:
            			num_silent += 1
        		elif not silent and not snd_started:
            			snd_started = True

			#if snd_started and num_silent > 30:
				#break
		
			##print q.empty()
			if(q.empty()!=True):
				##print "ENTERD"
				l=q.get()
			##print silent,snd_started,num_silent,max(snd_data),THRESHOLD,record[0],l
			if(l==0):
				break
		sample_width = p.get_sample_size(FORMAT)
    		stream.stop_stream()
    		stream.close()
    		p.terminate()

    		r = self.normalize(r)
    		r = self.trim(r)
    		r = self.add_silence(r, 0.5)
		#q.put(1)
		#q.put(2)
		#q.put(sample_width)
		#f = open('workfile', 'w')
		#f.write(str(r))
		#f.close()
		d[0]=sample_width
		d[1]=r
		#q.put(r)
		##print "end"	
		##print q.qsize()
	#	return sample_width, r

	def record_to_file(self,widget):
		path=rec_file[0]
		if(path==''):
			path='demo.wav'
		record[0]=record[0]^1
		if(record[0]!=1):
			self.button24.set_label("RECORD")
		#num = Value('d', 0.0)
		#arr = Array(0,1)
		q.put(record[0])
		if(record[0]==1):
			self.button24.set_label("STOP")
			pid=os.fork()
			##print q.empty()
			if(pid==0):
				manager = Manager()
				d = manager.dict()
				phr = Process(target=self.record, args=(q,d))
				#"Records from the microphone and outputs the resulting data to 'path'"
				#sample_width, data = self.record()
				phr.start()
				##print "asd----"
				phr.join()
				##print "YEAh"
				#if(q.qsize==2):
				sample_width=d[0]
				#f = open('workfile', 'r')
				#up=f.read()
				#f.close()
				##print type(up)
				data=d[1]
				##print len(data)
  	  			data = pack('<' + ('h'*len(data)), *data)
	
		    		wf = wave.open(path, 'wb')
   				wf.setnchannels(1)
    				wf.setsampwidth(sample_width)
    				wf.setframerate(RATE)
   				wf.writeframes(data)
    				wf.close()
				sys.exit(0)
	
	
	def pause(self,widget,val):
		if(val<=3):
			if(pause[val-1]==0 and par[val-1]>0):
				if(val==1):
					self.button17.set_label("RESUME")
				if(val==2):
					self.button18.set_label("RESUME")
				if(val==3):
					self.button19.set_label("RESUME")
				pause[val-1]=1
				play[val-1]=0
				os.kill(par[val-1],signal.SIGSTOP)
			else:
				if(val==1):
					self.button17.set_label("PAUSE")
				if(val==2):
					self.button18.set_label("PAUSE")
				if(val==3):
					self.button19.set_label("PAUSE")
				os.kill(par[val-1],signal.SIGCONT)
				play[val-1]=1
				pause[val-1]=0
		elif(val==4):
			if(mix_pause[0]==0 and mix_par[0]>0):
				mix_pause[0]=1
				self.button21.set_label("RESUME")
				play[val-1]=0
				os.kill(mix_par[0],signal.SIGSTOP)
			else:
				mix_pause[0]=0
				self.button21.set_label("PAUSE")
				play[val-1]=1
				os.kill(mix_par[0],signal.SIGCONT)
		elif(val==5):
			if(mod_pause[0]==0 and mod_par[0]>0):
				self.button23.set_label("RESUME")
				mod_pause[0]=1
				play[val-1]=0
				os.kill(mod_par[0],signal.SIGSTOP)
			else:
				self.button23.set_label("PAUSE")
				mod_pause[0]=0
				play[val-1]=1
				os.kill(mod_par[0],signal.SIGCONT)

	def file_selected(self, widget,val):
		if(val==1):
			self.label100.set_text(os.path.basename(widget.get_filename()))
			#x[val-1]=os.path.basename(widget.get_filename())
			x[val-1]=(widget.get_filename())
 				#   #print dialog.get_filename(), 'selected'
		if(val==2):
			self.label101.set_text(os.path.basename(widget.get_filename()))
			#x[val-1]=os.path.basename(widget.get_filename())
			x[val-1]=(widget.get_filename())
		if(val==3):
			self.label102.set_text(os.path.basename(widget.get_filename()))
			#x[val-1]=os.path.basename(widget.get_filename())
			x[val-1]=(widget.get_filename())
		fil[val-1]=x[val-1]
		##print "Selected filepath: %s" % widget.get_filename()
	def destroy(self,widget,data=None):
		os.kill(0,9)
		sys.exit(0)
		gtk.main_quit()
		sys.exit(0)

	def on_clicked(self, widget):
		        if widget.get_active():
				#self.set_title("Check Button")
				yyt=1
		        else:
				#self.set_title("")
				yyt=0

	def amplify(self,val,amp):
		##print "yes"
		minimum_amp=-32768
		maximum_amp=32767
		f1=wave.open(x[val-1],'r') 
		f_rate=f1.getframerate() 
		s_width=f1.getsampwidth() 
		channel=f1.getnchannels() 
		n_frame=f1.getnframes()
		raw_data=f1.readframes(n_frame) 
		f1.close() 
		total_length=n_frame*channel 
		if s_width==1: 
			fmt="%iB"%total_length 
		else :
			fmt="%ih"%total_length 
		int_data=list((struct.unpack(fmt,raw_data)))
#		amp=raw_input()
		##print amp
		for i in range(len(int_data)):
			int_data[i]=min(max(int((amp)*int(int_data[i])),minimum_amp),maximum_amp);
		length=(len(int_data))
		if(s_width==1):
			        fmt="%iB"%(length)
		elif s_width==2:
			        fmt="%ih"%(length)
		raw_data=struct.pack(fmt,*(int_data))
		x[val-1]=sol[val-1]
		f=wave.open(sol[val-1],'w')
		f.setframerate(f_rate)
		f.setnframes(len(int_data))
		f.setsampwidth(s_width)
		f.setnchannels(channel)
		f.writeframes(raw_data)
		f.close()

	def timeshift(self,val,value):
		#print val,value
		minimum_amp=-32768
		maximum_amp=32767
		f1=wave.open(x[val-1],'r') 
		f_rate=f1.getframerate() 
		s_width=f1.getsampwidth() 
		channel=f1.getnchannels() 
		n_frame=f1.getnframes()
		raw_data=f1.readframes(n_frame) 
		f1.close() 
		total_length=n_frame*channel 
		if s_width==1: 
			fmt="%iB"%total_length 
		else :
			fmt="%ih"%total_length 
		int_data=list((struct.unpack(fmt,raw_data)))
		timeshift=value
		timeshift=(timeshift)*f_rate
		if(channel==2):
			timeshift=int(2*(timeshift))
		if(timeshift>0):
			int_data=[0]*int(timeshift)+int_data
		else:
			int_data=int_data[-int(timeshift):]
		length=(len(int_data))
		if(s_width==1):
			        fmt="%iB"%(length)
		elif s_width==2:
			        fmt="%ih"%(length)
		raw_data=struct.pack(fmt,*(int_data))
		x[val-1]=sol[val-1]
		f=wave.open(x[val-1],'w')
		f.setframerate(f_rate)
		f.setnframes(len(int_data))
		f.setsampwidth(s_width)
		f.setnchannels(channel)
		f.writeframes(raw_data)
		f.close()

	def reverse(self,val):
		minimum_amp=-32768
		maximum_amp=32767
		f1=wave.open(x[val-1],'r') 
		f_rate=f1.getframerate() 
		s_width=f1.getsampwidth() 
		channel=f1.getnchannels() 
		n_frame=f1.getnframes()
		raw_data=f1.readframes(n_frame) 
		f1.close() 
		total_length=n_frame*channel 
		if s_width==1: 
			fmt="%iB"%total_length 
		else :
			fmt="%ih"%total_length 
		int_data=list((struct.unpack(fmt,raw_data)))
		if(channel==2):
			list1=[]
			list2=[]
			for i in range(len(int_data)):
				if(i%2==0):
					list2.append(int_data[i])
				else:
					list1.append(int_data[i])
			list1.reverse()
			list2.reverse()
			int_data=[]
#			#print int_data,list1,list2
			for i in range((len(list1))):
				int_data.append(list2[i])
				int_data.append(list1[i])
		else:
			int_data.reverse()
		length=(len(int_data))
		if(s_width==1):
			        fmt="%iB"%(length)
		elif s_width==2:
			        fmt="%ih"%(length)
		raw_data=struct.pack(fmt,*(int_data))
		x[val-1]=sol[val-1]
		f=wave.open(x[val-1],'w')
		f.setframerate(f_rate)
		f.setnframes(len(int_data))
		f.setsampwidth(s_width)
		f.setnchannels(channel)
		f.writeframes(raw_data)
		f.close()

	def scale(self,val,value):
		#print val,value
		minimum_amp=-32768
		maximum_amp=32767
		f1=wave.open(x[val-1],'r') 
		f_rate=f1.getframerate() 
		s_width=f1.getsampwidth() 
		channel=f1.getnchannels() 
		n_frame=f1.getnframes()
		raw_data=f1.readframes(n_frame) 
		f1.close() 
		total_length=n_frame*channel 
		if s_width==1: 
			fmt="%iB"%total_length 
		else :
			fmt="%ih"%total_length 
		int_data=list((struct.unpack(fmt,raw_data)))
		shift=value
		shift=shift
		if(channel==1 and shift!=1):
			length=len(int_data)
			initial=0
			final=0
			list1=[]
			while(final<length):
				list1.append(int_data[final])
				initial+=shift
				final=int(initial)
			int_data=list1
		elif(channel==2 and shift!=1):
			length=len(int_data)
			initial=0
			final=0
			list1=[]
			list2=[]
			list3=[]
			list4=[]
			for i in xrange(length):
				if(i%2==0):
					list1.append(int_data[i])
				else:
					list2.append(int_data[i])
		
			length1=len(list1)
			##print len(list1),len(list2),shift
			initial=0
			while(final<length1):
				list3.append(list1[final])
				initial+=shift
				final=int(initial)
			initial=0
			length2=len(list2)
			final=0
			initial=0
			while(final<length2):
				list4.append(list2[final])
				initial+=shift
				final=int(initial)
			length=len(list3)
			int_data=[]
			for i in xrange(length):
				int_data.append(list3[i])
				int_data.append(list4[i])
		length=(len(int_data))
		if(s_width==1):
			        fmt="%iB"%(length)
		elif s_width==2:
			        fmt="%ih"%(length)
		raw_data=struct.pack(fmt,*(int_data))
		x[val-1]=sol[val-1]
		f=wave.open(x[val-1],'w')
		f.setframerate(f_rate)
		f.setnframes(len(int_data))
		f.setsampwidth(s_width)
		f.setnchannels(channel)
		f.writeframes(raw_data)
		f.close()

	def mod(self,widget):
		##print "mixing: ",mod_par[0]
		li=[]
		k=(-10,-10)
		try:
			k=os.waitpid(mod_par[0], os.WNOHANG)
			##print "YES",k,type(k)
			li.append(k)
		except OSError:
			##print "YES"
			mod_par[0]=-1
		##print li
		if(len(li)>0 and len(li[0])>0 and li[0][0]>0):
			mod_par[0]=-1
#		if(mix_par[0]>0 and os.waitpid(0, 0,signal.WNOHANG)>0):
#			#print 1
#			mix_par[0]=-1

		if(mod_par[0]>0):
			##print 2
			os.kill(mod_par[0],9)
			self.button22.set_label("PLAY")
			play[4]=-1
#			#print par[val-1]
#			par[val-1]=-1
			mod_par[0]=-1
			##print "asd"
		else:
			self.button22.set_label("STOP")
			flag=0
			list1=[]
			list2=[]
			list3=[]
			modul[0]=0
			modul[1]=0
			modul[2]=0
			entered=0
			for i in range(3):
				x[i]=fil[i]
				flag=0
				if(i==0):
					reversal=self.button2.get_active()
					modulation=self.button3.get_active()
					mixing=self.button4.get_active()
					amplitude=self.scale1.get_value()
					shift=self.scale2.get_value()
					scaling=self.scale3.get_value()
				elif(i==1):
					reversal=self.button6.get_active()
					modulation=self.button7.get_active()
					mixing=self.button8.get_active()
					amplitude=self.scale4.get_value()
					shift=self.scale5.get_value()
					scaling=self.scale6.get_value()
				elif(i==2):
					reversal=self.button10.get_active()
					modulation=self.button11.get_active()
					mixing=self.button12.get_active()
					amplitude=self.scale7.get_value()
					shift=self.scale8.get_value()
					scaling=self.scale9.get_value()
			#	#print modulation,i
				if(modulation==True and x[i]!=''):
					modul[i]=1
				if(reversal==True and x[i]!=''):
					self.reverse(i+1)
					flag=1
				if(amplitude!=1 and x[i]!=''):
					self.amplify(i+1,amplitude)
					flag=1
				if(shift!=0 and x[i]!=''):
					self.timeshift(i+1,shift)
					flag=1
				if(scaling!=0 and x[i]!=''):
					self.scale(i+1,scaling)
					flag=1
				minimum_amp=-32768
				maximum_amp=32767
			#	#print sol[i]
				if(modulation==True and x[i]!=''):
					entered=1
					modul[i]=1
					if(flag==1):
						f1=wave.open(sol[i],'r') 
					else:
						f1=wave.open(x[i],'r')
					f_rate=f1.getframerate() 
					s_width=f1.getsampwidth() 
					channel=f1.getnchannels() 
					n_frame=f1.getnframes()
					raw_data=f1.readframes(n_frame) 
					f1.close() 
					total_length=n_frame*channel 
					if s_width==1: 
						fmt="%iB"%total_length 
					else :
						fmt="%ih"%total_length 
					if(i==0):
						list1=list((struct.unpack(fmt,raw_data)))
					if(i==1):
						list2=list((struct.unpack(fmt,raw_data)))
					if(i==2):
						list3=list((struct.unpack(fmt,raw_data)))
			length1=len(list1)
			length2=len(list2)
			length3=len(list3)
			ans=[]
			#play[4]=1
			i=0
			l=max(max(length1,length2),length3)
			##print length1,length2,length3,l
			##print "max length : "+str(l)
			for i in xrange(length1,l,1):
				list1.append(0)
			for i in xrange(length2,l,1):
				list2.append(0)
			for i in xrange(length3,l,1):
				list3.append(0)
			i=0
			j=0
			##print modul[0],modul[1],modul[2]
			if(modul[0]!=0 and x[0]!=''):
				##print 1
				ans=list1
			else:
				ans=[1]*l
			if(modul[1]!=0 and x[1]!=''):
				i=0
				##print 2
				while(i<l):
					ans[i]=ans[i]*list2[i]
					ans[i]=min(max(ans[i],minimum_amp),maximum_amp)
					i+=1
			if(modul[2]!=0 and x[2]!=''):
				i=0
				##print 3
				while(i<l):
					ans[i]=ans[i]*list3[i]
					ans[i]=min(max(ans[i],minimum_amp),maximum_amp)
					i+=1
			##print len(ans),ans[100]
			#if(ans==list1):
				##print "YES"
			##print "LEFT"
			#while(i<l):
			#	j=0
			#	if(i<length1):
			#		ans.append(list1[i])
			#	else:
			#		ans.append(0)
			#	if(i<length2):
			#		ans[i]*=list2[i]
			#		ans[i]=min(max(ans[i],minimum_amp),maximum_amp)
			#	else:
			#		ans[i]=0
			#	if(i<length3):
			#		ans[i]*=list3[i]
			#		ans[i]=min(max(ans[i],minimum_amp),maximum_amp)
			#	else:
			#		ans[i]=0
			#	if(modul[0]!=0):
			#		j=1
			#		ans.append(list1[i])
#				if(modul[1]!=0):
					#if(len(ans)<i+1):
			#	if(modul[1]!=0 and j==0):
			#		j=1
			#		ans.append(list2[i])
			#	elif(modul[1]!=0):
			#		ans[i]=ans*list2[i]
			#	#if(modul[2]!=0):
					#if(len(ans)<i+1):
			#	if(modul[2]!=0 and j==0):
			#		j=1
			#		ans.append(list3[i])
			#	elif(modul[2]!=0):
			#		ans[i]=ans*list3[i]
			#	ans[i]=min(max(ans[i],minimum_amp),maximum_amp)
			#	i+=1
				##print i,l
		#	#print ans[7345],ans[7346]
			#length=(len(int_data))
			if(entered==1):
				length=l
				if(s_width==1):
				        fmt="%iB"%(length)
				elif s_width==2:
				        fmt="%ih"%(length)
				raw_data=struct.pack(fmt,*(ans))
	#			x[val-1]=sol[val-1]
				##print "ans"
				##print l,len(ans)
				##print "hi",l,f_rate,s_width,channel,len(raw_data)
				f=wave.open(modulate_file,'w')
				f.setframerate(f_rate)
				f.setnframes(l)
				f.setsampwidth(s_width)
				f.setnchannels(channel)
				f.writeframes(raw_data)
				f.close()
				wf = wave.open(modulate_file, 'rb')
				frames = wf.getnframes()
				rate = wf.getframerate()
				duration[4] = frames / float(rate)
				wf.close()
				play[4]=1
				elapsed[4]=0
				mod_par[0]=os.fork()
				if(mod_par[0]==0):
					CHUNK = 1024
					wf = wave.open(modulate_file, 'rb')
					p = pyaudio.PyAudio()
					stream = p.open(format=p.get_format_from_width(wf.getsampwidth()),channels=wf.getnchannels(),rate=wf.getframerate(),output=True)
					data = wf.readframes(CHUNK)
					while data != '':
						stream.write(data)
						data = wf.readframes(CHUNK)
					stream.stop_stream()
					stream.close()
					p.terminate()
					sys.exit(0)
					#x[val-1]=fil[val-1]
					#par[val-1]=-1

	def mix(self,widget):
		##print "mixing: ",mix_par[0]
		li=[]
		k=(-10,-10)
		try:
			k=os.waitpid(mix_par[0], os.WNOHANG)
			##print "YES",k,type(k)
			li.append(k)
		except OSError:
			##print "YES"
			mix_par[0]=-1
		##print li
		if(len(li)>0 and len(li[0])>0 and li[0][0]>0):
			mix_par[0]=-1
#		if(mix_par[0]>0 and os.waitpid(0, 0,signal.WNOHANG)>0):
#			#print 1
#			mix_par[0]=-1

		if(mix_par[0]>0):
			##print 2
			os.kill(mix_par[0],9)
			self.button20.set_label("PLAY")
			play[3]=-1
#			#print par[val-1]
#			par[val-1]=-1
			mix_par[0]=-1
			##print "asd"
		else:
			self.button20.set_label("STOP")
			flag=0
			list1=[]
			list2=[]
			list3=[]
			entered=0
			for i in range(3):
				x[i]=fil[i]
				flag=0
				if(i==0):
					reversal=self.button2.get_active()
					modulation=self.button3.get_active()
					mixing=self.button4.get_active()
					amplitude=self.scale1.get_value()
					shift=self.scale2.get_value()
					scaling=self.scale3.get_value()
				elif(i==1):
					reversal=self.button6.get_active()
					modulation=self.button7.get_active()
					mixing=self.button8.get_active()
					amplitude=self.scale4.get_value()
					shift=self.scale5.get_value()
					scaling=self.scale6.get_value()
				elif(i==2):
					reversal=self.button10.get_active()
					modulation=self.button11.get_active()
					mixing=self.button12.get_active()
					amplitude=self.scale7.get_value()
					shift=self.scale8.get_value()
					scaling=self.scale9.get_value()
				##print mixing,i
				if(reversal==True and x[i]!=''):
					self.reverse(i+1)
					flag=1
				if(amplitude!=1 and x[i]!=''):
					self.amplify(i+1,amplitude)
					flag=1
				if(shift!=0 and x[i]!=''):
					##print "Entered"
					self.timeshift(i+1,shift)
					flag=1
				if(scaling!=0 and x[i]!=''):
					self.scale(i+1,scaling)
					flag=1
				minimum_amp=-32768
				maximum_amp=32767
				##print sol[i]
				if(mixing==True and x[i]!=''):
					##print "HERE"
					entered=1
					if(flag==1):
						##print "solution", i
						f1=wave.open(sol[i],'r') 
					else:
						f1=wave.open(x[i],'r')
					f_rate=f1.getframerate() 
					s_width=f1.getsampwidth() 
					channel=f1.getnchannels() 
					n_frame=f1.getnframes()
					raw_data=f1.readframes(n_frame) 
					f1.close() 
					total_length=n_frame*channel 
					if s_width==1: 
						fmt="%iB"%total_length 
					else :
						fmt="%ih"%total_length 
					if(i==0):
						list1=list((struct.unpack(fmt,raw_data)))
					if(i==1):
						list2=list((struct.unpack(fmt,raw_data)))
					if(i==2):
						list3=list((struct.unpack(fmt,raw_data)))
			length1=len(list1)
			length2=len(list2)
			length3=len(list3)
			ans=[]
			i=0
			l=max(max(length1,length2),length3)
			##print length1,length2,length3
			##print "max length : "+str(l)
			while(i<l):
				if(i<length1):
					ans.append(list1[i])
				else:
					ans.append(0)
				if(i<length2):
					ans[i]+=list2[i]
					ans[i]=min(max(ans[i],minimum_amp),maximum_amp)
				if(i<length3):
					ans[i]+=list3[i]
					ans[i]=min(max(ans[i],minimum_amp),maximum_amp)
				i+=1
			#length=(len(int_data))
			if(entered==1):
				length=l
				if(s_width==1):
				        fmt="%iB"%(length)
				elif s_width==2:
				        fmt="%ih"%(length)
				raw_data=struct.pack(fmt,*(ans))
		#		x[val-1]=sol[val-1]
				##print "ans"
				##print l,len(ans)
				f=wave.open(mixing_file,'w')
				f.setframerate(f_rate)
				f.setnframes(l)
				f.setsampwidth(s_width)
				f.setnchannels(channel)
				f.writeframes(raw_data)
				f.close()
				wf = wave.open(mixing_file, 'rb')
				frames = wf.getnframes()
				rate = wf.getframerate()
				duration[3] = frames / float(rate)
				wf.close()
				play[3]=1
				elapsed[3]=0
				mix_par[0]=os.fork()
				if(mix_par[0]==0):
					CHUNK = 1024
					wf = wave.open(mixing_file, 'rb')
					p = pyaudio.PyAudio()
					stream = p.open(format=p.get_format_from_width(wf.getsampwidth()),channels=wf.getnchannels(),rate=wf.getframerate(),output=True)
					data = wf.readframes(CHUNK)
					while data != '':
						stream.write(data)
						data = wf.readframes(CHUNK)
					stream.stop_stream()
					stream.close()
					p.terminate()
					sys.exit(0)
				#x[val-1]=fil[val-1]
				#par[val-1]=-1
	def play(self,widget,val):
		#	r=2
		x[val-1]=fil[val-1]
		li=[]
		k=(-10,-10)
		try:
			k=os.waitpid(par[val-1], os.WNOHANG)
			##print "YES",k,type(k)
			li.append(k)
		except OSError:
			##print "YES"
			par[val-1]=-1
		##print li
		if(len(li)>0 and len(li[0])>0 and li[0][0]>0):
			par[val-1]=-1
#		if(k[0]==0):
#			par[val-1]=-1;
#		if(par[val-1]>0 and os.waitpid(par[val-1], os.WNOHANG)>0):
#			#print os.waitpid(par[val-1],os.WNOHANG)
#			par[val-1]=-1

		if(par[val-1]>0):
			#			#print os.waitpid(par[val-1],os.WNOHANG)
			if(val==1):
				self.button14.set_label("PLAY")
			if(val==2):
				self.button13.set_label("PLAY")
			if(val==3):
				self.button15.set_label("PLAY")
			play[val-1]=-1
			os.kill(par[val-1],9)
			##print par[val-1]
			par[val-1]=-1
			##print "asd"
		else:
			if(x[val-1]!=''):
				if(val==1):
					self.button14.set_label("STOP")
					reversal=self.button2.get_active()
					modulation=self.button3.get_active()
					mixing=self.button4.get_active()
					amplitude=self.scale1.get_value()
					shift=self.scale2.get_value()
					scaling=self.scale3.get_value()
				elif(val==2):
					self.button13.set_label("STOP")
					reversal=self.button6.get_active()
					modulation=self.button7.get_active()
					mixing=self.button8.get_active()
					amplitude=self.scale4.get_value()
					shift=self.scale5.get_value()
					scaling=self.scale6.get_value()
				elif(val==3):
					self.button15.set_label("STOP")
					reversal=self.button10.get_active()
					modulation=self.button11.get_active()
					mixing=self.button12.get_active()
					amplitude=self.scale7.get_value()
					shift=self.scale8.get_value()
					scaling=self.scale9.get_value()
		#		#print reversal,modulation,mixing,amplitude,shift,scaling
				wf = wave.open(x[val-1], 'rb')
				frames = wf.getnframes()
				rate = wf.getframerate()
				duration[val-1] = frames / float(rate)
				#print duration[val-1],frames,rate
				play[val-1]=1
				elapsed[val-1]=0
				wf.close()
				#par[val-1]=os.fork()
				#if(par[val-1]==0):
				if(reversal==True):
					self.reverse(val)
				if(amplitude!=1):
					self.amplify(val,amplitude)
				if(shift!=0):
					self.timeshift(val,shift)
				if(scaling!=0):
					self.scale(val,scaling)
					##print "asda"
				CHUNK = 1024
				wf = wave.open(x[val-1], 'rb')
				frames = wf.getnframes()
				rate = wf.getframerate()
				duration[val-1] = frames / float(rate)
				##print duration
				par[val-1]=os.fork()
				wf.close()
				if(par[val-1]==0):
					wf = wave.open(x[val-1], 'rb')
					p = pyaudio.PyAudio()
					stream = p.open(format=p.get_format_from_width(wf.getsampwidth()),channels=wf.getnchannels(),rate=wf.getframerate(),output=True)
					data = wf.readframes(CHUNK)
					while data != '':
						stream.write(data)
						data = wf.readframes(CHUNK)
#						check+=1
					##print duration
					stream.stop_stream()
					stream.close()
					p.terminate()
					wf.close()
					x[val-1]=fil[val-1]
					par[val-1]=-1
					sys.exit(0)
		#		return 0
	def browse(self,widget,val):
		###print val
#		filechooserbutton = gtk.FileChooserButton("Select A File", None)

#		window.connect("destroy", lambda w: gtk.main_quit()) 
#		filechooserbutton.connect("file-set", self.file_selected) 
#		window.add(filechooserbutton) 
#		window.show_all()
		dialog = gtk.FileChooserDialog("Open..",
                               None,
                               gtk.FILE_CHOOSER_ACTION_OPEN,
                               (gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL,
                                gtk.STOCK_OPEN, gtk.RESPONSE_OK))
		dialog.set_default_response(gtk.RESPONSE_OK)

		filter = gtk.FileFilter()
		filter.set_name("All files")
		filter.add_pattern("*")
		dialog.add_filter(filter)

		filter = gtk.FileFilter()
		filter.set_name("Images")
		filter.add_mime_type("image/png")
		filter.add_mime_type("image/jpeg")
		filter.add_mime_type("image/gif")
		filter.add_pattern("*.png")
		filter.add_pattern("*.jpg")
		filter.add_pattern("*.gif")
		filter.add_pattern("*.tif")
		filter.add_pattern("*.xpm")
		dialog.add_filter(filter)

		response = dialog.run()
		if response == gtk.RESPONSE_OK:
				if(val==1):
					self.label100.set_text(os.path.basename(dialog.get_filename()))
					x[val-1]=os.path.basename(dialog.get_filename())
					fil[val-1]=x[val-1]
 #   				#print dialog.get_filename(), 'selected'
				if(val==2):
					self.label101.set_text(os.path.basename(dialog.get_filename()))
					x[val-1]=os.path.basename(dialog.get_filename())
					fil[val-1]=x[val-1]
				if(val==3):
					self.label102.set_text(os.path.basename(dialog.get_filename()))
					x[val-1]=os.path.basename(dialog.get_filename())
					fil[val-1]=x[val-1]
		elif response == gtk.RESPONSE_CANCEL:
			##print 'Closed, no files selected'
			x[val-1]=""
		dialog.destroy()
	def progress_timeout(self,widget):
		for i in xrange(0,5,1):
			if(play[i]==1):
				elapsed[i]=min(elapsed[i]+0.1,duration[i])
		for i in xrange(0,5,1):
			if(i==0):
				if(duration[i]==0):
					self.pgbar.set_fraction(0.0)
					self.button14.set_label("PLAY")
					self.button17.set_label("PAUSE")
				else:
					if(play[i]!=-1):
						##print play[i],elapsed[i],duration[i]
						self.pgbar.set_fraction((elapsed[i]*1.0)/duration[i])
					else:
						elapsed[i]=0
						duration[i]=0
						self.pgbar.set_fraction(0.0)
				if(elapsed[i]==duration[i]):
					self.button14.set_label("PLAY")
					self.button17.set_label("PAUSE")
					self.pgbar.set_fraction(0.0)
			if(i==1):
				if(duration[i]==0):
					self.pgbar2.set_fraction(0.0)
					self.button13.set_label("PLAY")
					self.button18.set_label("PAUSE")
				else:
					if(play[i]!=-1):
						self.pgbar2.set_fraction((elapsed[i]*1.0)/duration[i])
					else:
						elapsed[i]=0
						duration[i]=0
						self.pgbar2.set_fraction(0.0)
				if(elapsed[i]==duration[i]):
					self.button13.set_label("PLAY")
					self.button18.set_label("PAUSE")
					self.pgbar2.set_fraction(0.0)
			if(i==2):
				if(duration[i]==0):
					self.pgbar3.set_fraction(0.0)
					self.button19.set_label("PAUSE")
					self.button15.set_label("PLAY")
				else:
					if(play[i]!=-1):
						self.pgbar3.set_fraction((elapsed[i]*1.0)/duration[i])
					else:
						elapsed[i]=0
						duration[i]=0
						self.pgbar3.set_fraction(0.0)
				if(elapsed[i]==duration[i]):
					self.button15.set_label("PLAY")
					self.button19.set_label("PAUSE")
					self.pgbar3.set_fraction(0.0)
			if(i==3):
				if(duration[i]==0):
					self.pgbar4.set_fraction(0.0)
					self.button21.set_label("PAUSE")
					self.button20.set_label("PLAY")
				else:
					if(play[i]!=-1):
						self.pgbar4.set_fraction((elapsed[i]*1.0)/duration[i])
					else:
						elapsed[i]=0
						duration[i]=0
						self.pgbar4.set_fraction(0.0)
				if(elapsed[i]==duration[i]):
					self.button20.set_label("PLAY")
					self.button21.set_label("PAUSE")
					self.pgbar4.set_fraction(0.0)
			if(i==4):
				if(duration[i]==0):
					self.pgbar5.set_fraction(0.0)
					self.button23.set_label("PAUSE")
					self.button22.set_label("PLAY")
				else:
					if(play[i]!=-1):
						self.pgbar5.set_fraction((elapsed[i]*1.0)/duration[i])
					else:
						elapsed[i]=0
						duration[i]=0
						self.pgbar5.set_fraction(0.0)
				if(elapsed[i]==duration[i]):
					self.button22.set_label("PLAY")
					self.button23.set_label("PAUSE")
					self.pgbar5.set_fraction(0.0)
		gobject.timeout_add (100, self.progress_timeout,self)
		return
	def __init__(self):
		self.window=gtk.Window(gtk.WINDOW_TOPLEVEL)
		self.window.set_position(gtk.WIN_POS_CENTER)
		self.window.set_size_request(800,800)
		self.window.set_title("Wave Mixer")
		files=gtk.FileFilter()
		files.add_pattern("*.wav")

		self.pix=gtk.gdk.pixbuf_new_from_file("equi.jpg")
		self.pix=self.pix.scale_simple(800,800,gtk.gdk.INTERP_BILINEAR)
		self.image=gtk.image_new_from_pixbuf(self.pix)
						

		self.fixed=gtk.Fixed()
		self.window.add(self.fixed)
		self.fixed.show()
		
		self.timer = gobject.timeout_add (100, self.progress_timeout,self)

		
		self.button=gtk.Button("Exit")
		self.button.connect("clicked",self.destroy)
		self.fixed.put(self.image,0,0)
#		self.button1 = gtk.FileChooserButton("Select A File", None)

#		self.window.connect("destroy", lambda w: gtk.main_quit()) 
#		filechooserbutton.connect("file-set", self.file_selected) 
		#window.add(filechooserbutton) 
		#window.show_all()
		#f = gtk.Frame()
		self.file_label1=gtk.Label("<b>Wave 1</b>")
		self.file_label1.set_use_markup(gtk.TRUE)
		self.file_label1.set_markup('<span size="14000"><b>Wave 1</b></span>')
		self.fixed.put(self.file_label1,20,40)
	
		
		self.label211=gtk.Label("<b>Wave Mixer</b>")
		self.label211.set_use_markup(gtk.TRUE)
		self.label211.set_markup('<span size="14000"><b>Wave Mixer</b></span>')
		self.fixed.put(self.label211,300,0)

		#f.add(self.file_label1)
	#	self.button1=gtk.Button("Select File")
	#	self.button1.connect("clicked",self.browse,1)
		self.button1=gtk.FileChooserButton("Select A File", None)
		self.button1.add_filter(files)
		self.button1.connect("file-set", self.file_selected,1)
		self.button1.set_size_request(100,40)
		self.fixed.put(self.button1, 20, 60)
		self.label100=gtk.Label("")
		self.fixed.put(self.label100,120,80)
		
		#f.add(self.button1)
		#f.add(self.label100)
		
		self.label1=gtk.Label("Amplitude")
		self.label1.set_use_markup(gtk.TRUE)
		self.label1.set_markup('<span size="12000"><b>Amplitude</b></span>')
		self.fixed.put(self.label1, 20, 110)
		self.label2=gtk.Label("Time Shift")
		self.label2.set_use_markup(gtk.TRUE)
		self.label2.set_markup('<span size="12000"><b>Time Shift</b></span>')
		self.fixed.put(self.label2, 20, 170)
		self.label3=gtk.Label("Time Scaling")
		self.label3.set_use_markup(gtk.TRUE)
		self.label3.set_markup('<span size="12000"><b>Time Scaling</b></span>')
		self.fixed.put(self.label3, 20, 230)
		
		#f.add(self.label1)
		#f.add(self.label2)
		#f.add(self.label3)

		self.scale1=gtk.HScale()
		self.scale1.set_range(0,5)
		self.scale1.set_increments(0.1,1)
		self.scale1.set_digits(1)
		self.scale1.set_value(1.0)
		self.scale1.set_size_request(160,45)
		self.fixed.put(self.scale1,20,125)

		#f.add(self.scale1)

		self.scale2=gtk.HScale()
		self.scale2.set_range(-1,1)
		self.scale2.set_increments(0.05,0.1)
		self.scale2.set_digits(2)
		self.scale2.set_size_request(160,45)
		self.fixed.put(self.scale2,20,185)

		#f.add(self.scale2)
	
		self.scale3=gtk.HScale()
		self.scale3.set_range(0,8)
		self.scale3.set_increments(0.125,0.5)
		self.scale3.set_digits(3)
		self.scale3.set_size_request(160,45)
		self.fixed.put(self.scale3,20,245)

		#f.add(self.scale3)

		self.button2 = gtk.CheckButton("Time Reversal")
		self.button2.set_active(False)
		self.button2.unset_flags(gtk.CAN_FOCUS)
		self.button2.connect("clicked", self.on_clicked)
		self.fixed.put(self.button2,20,290)

		#f.add(self.button2)
	
		self.button3 = gtk.CheckButton("Modulation")
		self.button3.set_active(False)
		self.button3.unset_flags(gtk.CAN_FOCUS)
		self.button3.connect("clicked", self.on_clicked)
		self.fixed.put(self.button3,20,330)
		
		#f.add(self.button3)

		self.button4= gtk.CheckButton("Mixing")
		self.button4.set_active(False)
		self.button4.unset_flags(gtk.CAN_FOCUS)
		self.button4.connect("clicked", self.on_clicked)
		self.fixed.put(self.button4,20,370)
		
		#f.add(self.button4)

		self.button14=gtk.Button("Play")
		self.button14.connect("clicked",self.play,1)
		self.button14.set_size_request(50,40)
		self.fixed.put(self.button14,20,410)
		
		#f.add(self.button14)

		self.button17=gtk.Button("Pause")
		self.button17.connect("clicked",self.pause,1)
		self.button17.set_size_request(70,40)
		self.fixed.put(self.button17,100,410)
		#f.add(self.button17)
#		self.box=gtk.VBox()
#		self.box.pack_start(self.button)
#		self.box.pack_start(self.button1,fill=False)
#		self.box.pack_start(self.label1)
#		self.box.pack_start(self.scale1)
#		self.box.pack_start(self.label2)
#		self.box.pack_start(self.scale2)
#		self.box.pack_start(self.label3)
#		self.box.pack_start(self.scale3)
#		self.box.pack_start(self.button2)
#		self.box.pack_start(self.button3)
#		self.box.pack_start(self.button4)
		self.pgbar=gtk.ProgressBar(adjustment=None)
		self.pgbar.set_orientation(gtk.PROGRESS_LEFT_TO_RIGHT)
		self.fixed.put(self.pgbar,20,490)
	
		#f.add(self.pgbar)

		#self.button5=gtk.Button("Select File")
		#self.button5.connect("clicked",self.browse,2)
		self.file_label2=gtk.Label("Wave 2")
		self.file_label2.set_use_markup(gtk.TRUE)
		self.file_label2.set_markup('<span size="14000"><b>Wave 2</b></span>')
		self.fixed.put(self.file_label2,300,40)
		self.button5=gtk.FileChooserButton("Select A File", None)
		self.button5.add_filter(files)
		self.button5.connect("file-set", self.file_selected,2)

		self.button5.set_size_request(100,40)
		self.fixed.put(self.button5,300,60)
		self.label101=gtk.Label("")
		self.fixed.put(self.label101,400,80)

		self.label4=gtk.Label("Amplitude")
		self.label4.set_use_markup(gtk.TRUE)
		self.label4.set_markup('<span size="12000"><b>Amplitude</b></span>')
		self.fixed.put(self.label4, 300, 110)
		self.label5=gtk.Label("Time Shift")
		self.label5.set_use_markup(gtk.TRUE)
		self.label5.set_markup('<span size="12000"><b>Time Shift</b></span>')
		self.fixed.put(self.label5, 300, 170)
		self.label6=gtk.Label("Time Scaling")
		self.label6.set_use_markup(gtk.TRUE)
		self.label6.set_markup('<span size="12000"><b>Time Scaling</b></span>')
		self.fixed.put(self.label6, 300, 230)
		
		self.scale4=gtk.HScale()
		self.scale4.set_range(0,5)
		self.scale4.set_increments(0.1,1)
		self.scale4.set_digits(1)
		self.scale4.set_value(1.0)
		self.scale4.set_size_request(160,45)
		self.fixed.put(self.scale4, 300, 125)
		
		self.scale5=gtk.HScale()
		self.scale5.set_range(-1,1)
		self.scale5.set_increments(0.05,0.1)
		self.scale5.set_digits(2)
		self.scale5.set_size_request(160,45)
		self.fixed.put(self.scale5, 300, 185)

		self.scale6=gtk.HScale()
		self.scale6.set_range(0,8)
		self.scale6.set_increments(0.125,0.5)
		self.scale6.set_digits(3)
		self.scale6.set_size_request(160,45)
		self.fixed.put(self.scale6, 300, 245)

		self.button6 = gtk.CheckButton("Time Reversal")
		self.button6.set_active(False)
		self.button6.unset_flags(gtk.CAN_FOCUS)
		self.button6.connect("clicked", self.on_clicked)
		self.fixed.put(self.button6, 300, 290)

		self.button7 = gtk.CheckButton("Modulation")
		self.button7.set_active(False)
		self.button7.unset_flags(gtk.CAN_FOCUS)
		self.button7.connect("clicked", self.on_clicked)
		self.fixed.put(self.button7, 300, 330)
		
		self.button8= gtk.CheckButton("Mixing")
		self.button8.set_active(False)
		self.button8.unset_flags(gtk.CAN_FOCUS)
		self.button8.connect("clicked", self.on_clicked)
		self.fixed.put(self.button8, 300, 370)
		
		self.button13=gtk.Button("Play")
		self.button13.connect("clicked",self.play,2)
		self.button13.set_size_request(50,40)
		self.fixed.put(self.button13,300,410)
		
		self.button18=gtk.Button("Pause")
		self.button18.connect("clicked",self.pause,2)
		self.button18.set_size_request(70,40)
		self.fixed.put(self.button18,380,410)

		self.pgbar2=gtk.ProgressBar(adjustment=None)
		self.pgbar2.set_orientation(gtk.PROGRESS_LEFT_TO_RIGHT)
		self.fixed.put(self.pgbar2,310,490)

#		self.box1=gtk.VBox()
#		self.box1.pack_start(self.button5)
#		self.box1.pack_start(self.label4)
#		self.box1.pack_start(self.scale4)
#		self.box1.pack_start(self.label5)
#		self.box1.pack_start(self.scale5)
#		self.box1.pack_start(self.label6)
#		self.box1.pack_start(self.scale6)
#		self.box1.pack_start(self.button6)
#		self.box1.pack_start(self.button7)
#		self.box1.pack_start(self.button8)
		
		#self.button9=gtk.Button("Select File")
		#self.button9.connect("clicked",self.browse,3)
		self.file_label3=gtk.Label("Wave 3")
		self.file_label3.set_use_markup(gtk.TRUE)
		self.file_label3.set_markup('<span size="14000"><b>Wave 3</b></span>')
		self.fixed.put(self.file_label3,580,40)
		self.button9=gtk.FileChooserButton("Select A File", None)
		self.button9.add_filter(files)
		self.button9.connect("file-set", self.file_selected,3)		
		self.button9.set_size_request(100,40)
		self.fixed.put(self.button9, 580, 60)
		self.label102=gtk.Label("")
		self.fixed.put(self.label102,680,80)

		self.label7=gtk.Label("Amplitude")
		self.label7.set_use_markup(gtk.TRUE)
		self.label7.set_markup('<span size="12000"><b>Amplitude</b></span>')
		self.fixed.put(self.label7, 580, 100)		
		self.label8=gtk.Label("Time Shift")
		self.label8.set_use_markup(gtk.TRUE)
		self.label8.set_markup('<span size="12000"><b>Time Shift</b></span>')
		self.fixed.put(self.label8, 580, 170)
		self.label9=gtk.Label("Time Scaling")
		self.label9.set_use_markup(gtk.TRUE)
		self.label9.set_markup('<span size="12000"><b>Time Scaling</b></span>')
		self.fixed.put(self.label9, 580, 230)

		self.scale7=gtk.HScale()
		self.scale7.set_range(0,5)
		self.scale7.set_increments(0.1,1)
		self.scale7.set_digits(1)
		self.scale7.set_value(1.0)
		self.scale7.set_size_request(160,45)
		self.fixed.put(self.scale7, 580, 125)
		
		self.scale8=gtk.HScale()
		self.scale8.set_range(-1,1)
		self.scale8.set_increments(0.05,0.1)
		self.scale8.set_digits(2)
		self.scale8.set_size_request(160,45)
		self.fixed.put(self.scale8, 580, 185)

		self.scale9=gtk.HScale()
		self.scale9.set_range(0,8)
		self.scale9.set_increments(0.125,0.5)
		self.scale9.set_digits(3)
		self.scale9.set_size_request(160,45)
		self.fixed.put(self.scale9, 580, 245)

		self.button10 = gtk.CheckButton("Time Reversal")
		self.button10.set_active(False)
		self.button10.unset_flags(gtk.CAN_FOCUS)
		self.button10.connect("clicked", self.on_clicked)
		self.fixed.put(self.button10, 580, 290)

		self.button11 = gtk.CheckButton("Modulation")
		self.button11.set_active(False)
		self.button11.unset_flags(gtk.CAN_FOCUS)
		self.button11.connect("clicked", self.on_clicked)
		self.fixed.put(self.button11, 580, 330)
		
		self.button12= gtk.CheckButton("Mixing")
		self.button12.set_active(False)
		self.button12.unset_flags(gtk.CAN_FOCUS)
		self.button12.connect("clicked", self.on_clicked)
		self.fixed.put(self.button12, 580, 370)
		
		self.button15=gtk.Button("Play")
		self.button15.connect("clicked",self.play,3)
		self.button15.set_size_request(50,40)
		self.fixed.put(self.button15,580,410)
	
		self.button19=gtk.Button("Pause")
		self.button19.connect("clicked",self.pause,3)
		self.button19.set_size_request(70,40)
		self.fixed.put(self.button19,660,410)
		
		self.pgbar3=gtk.ProgressBar(adjustment=None)
		self.pgbar3.set_orientation(gtk.PROGRESS_LEFT_TO_RIGHT)
		self.fixed.put(self.pgbar3,590,490)
		
		#self.button20=gtk.Button("Mix")
		#self.button20.connect("clicked",self.play,1)
		#self.button20.set_size_request(50,40)
		#self.fixed.put(self.button20,300,460)
		self.label20=gtk.Label("Mix And Play")
		self.label20.set_use_markup(gtk.TRUE)
		self.label20.set_markup('<span size="12000"><b>Mix And Play</b></span>')
		self.fixed.put(self.label20, 40, 520)		
		
		self.button20=gtk.Button("Play")
		self.button20.connect("clicked",self.mix)
		self.button20.set_size_request(50,40)
		self.fixed.put(self.button20,20,540)
	
		self.button21=gtk.Button("Pause")
		self.button21.connect("clicked",self.pause,4)
		self.button21.set_size_request(70,40)
		self.fixed.put(self.button21,100,540)
		
		self.pgbar4=gtk.ProgressBar(adjustment=None)
		self.pgbar4.set_orientation(gtk.PROGRESS_LEFT_TO_RIGHT)
		self.fixed.put(self.pgbar4,20,590)
		
		#self.button21=gtk.Button("Modulate")
		#self.button21.connect("clicked",self.play,1)
		#self.button21.set_size_request(100,40)
		#self.fixed.put(self.button21,500,460)
		self.label22=gtk.Label("Modulate And Play")
		self.label22.set_use_markup(gtk.TRUE)
		self.label22.set_markup('<span size="12000"><b>Modulate And Play</b></span>')
		self.fixed.put(self.label22, 610, 520)

		self.button22=gtk.Button("Play")
		self.button22.connect("clicked",self.mod)
		self.button22.set_size_request(50,40)
		self.fixed.put(self.button22,600,540)
	
		self.button23=gtk.Button("Pause")
		self.button23.connect("clicked",self.pause,5)
		self.button23.set_size_request(70,40)
		self.fixed.put(self.button23,680,540)
		
		self.pgbar5=gtk.ProgressBar(adjustment=None)
		self.pgbar5.set_orientation(gtk.PROGRESS_LEFT_TO_RIGHT)
		self.fixed.put(self.pgbar5,600,590)
		
		self.text=gtk.Entry()
		self.text.connect("changed",self.change)
		self.fixed.put(self.text,300,540)

		self.button24=gtk.Button("RECORD")
		self.button24.connect("clicked",self.record_to_file)
		self.button24.set_size_request(70,40)
		self.fixed.put(self.button24,340,570)
#		self.box2=gtk.VBox()
#		self.box2.pack_start(self.button9)
#		self.box2.pack_start(self.label7)
#		self.box2.pack_start(self.scale7)
#		self.box2.pack_start(self.label8)
#		self.box2.pack_start(self.scale8)
#		self.box2.pack_start(self.label9)
#		self.box2.pack_start(self.scale9)
#		self.box2.pack_start(self.button10)
#		self.box2.pack_start(self.button11)
#		self.box2.pack_start(self.button12)


#		self.box3=gtk.HBox()
#		self.box3.pack_start(self.button)
#		self.box3.pack_start(self.box)
#		self.box3.pack_start(self.box1)
#		self.box3.pack_start(self.box2)
#		self.box3.pack_start(self.hscale)
		#self.window.add(self.button)
#		self.window.add(self.box3)
		#self.window.add(f)
		self.window.show_all()
		self.window.connect("destroy",self.destroy)
	def main(self):
		gtk.main()
		sys.exit(0)
if __name__=="__main__":
	q=Queue()
	base=Base()
	base.main()
	sys.exit(0)
