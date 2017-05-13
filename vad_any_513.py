#!/bin/env python
#-*- encoding=utf8 -*-
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
import numpy as np
import wave
import sys
import pyaudio
import math
import time
sys.setrecursionlimit(1500)

global max_frame
max_frame = 120.0

g_colors = ['r', 'y', 'b']

class Interval:
	def __init__(self, begin, end):
		self.m_begin = begin
		self.m_end = end

class VadAny:
	global max_frame
	def __init__(self, vad_path, wav_path):
		self.m_wav_path = wav_path
		self.m_vad_path = vad_path
		self.m_plot_index = 0
		self.m_counter = 0
		self.m_x0 = 0
		self.m_y0 = 0
		self.m_x1 = 0
		self.m_y1 = 0
		self.m_pos = 0
		self.m_is_press = False
		
	def get_counter(self):
		return self.m_counter
		
	def inc_counter(self):
		if self.m_counter >= 100:
			self.m_counter = 0
		else:
			self.m_counter += 1
	
	def read_vad(self):
		print("%s", self.m_vad_path)
		self.m_intervals = [Interval(float(line.split(',')[0]), float(line.split(',')[1])) for line in open(self.m_vad_path, 'r') if len(line.split(',')) >= 2]
	
	def read_wave(self):
		self.m_spf = wave.open(self.m_wav_path, 'r')
		frames = self.m_spf.readframes(self.m_spf.getnframes())
		self.m_signals = np.fromstring(frames, 'Int16')
		self.m_fs = self.m_spf.getframerate()
		self.m_plot_num = math.floor(len(self.m_signals)/(max_frame*self.m_fs))
		self.m_plot_num += 1
		audio_begin = 0.0
		audio_end = float(len(self.m_signals)/float(self.m_fs))
		print("fs %d ,time %f : %f"%(self.m_fs, audio_begin, audio_end))
		self.m_time = np.linspace(audio_begin, audio_end, num = len(self.m_signals))
		print("len=%d %d"%(len(self.m_signals), len(self.m_time)))
		
	def start_audio(self):
		self.m_audio = pyaudio.PyAudio()
		self.m_stream = self.m_audio.open(format = self.m_audio.get_format_from_width(self.m_spf.getsampwidth()),
									channels = self.m_spf.getnchannels(),
									rate = self.m_spf.getframerate(),
									output = True,
									frames_per_buffer = 800)
		
	def get_xy(self, nums):
		begin = int(self.m_plot_index * max_frame * self.m_fs)
		end = int((self.m_plot_index + 1) * max_frame * self.m_fs)
		if end > len(self.m_signals):
			end = len(self.m_signals)
		print("xy %d - %d"%(begin, end))
		self.m_plot_index += nums
		if self.m_plot_index <= 0:
			self.m_plot_index = 0
		self.m_plot_index %= self.m_plot_num
		print("index--nex:%d, max: %d"%(self.m_plot_index, self.m_plot_num))
		span = []
		begin_time = float(begin)/self.m_fs
		end_time = float(end)/self.m_fs
		for i in self.m_intervals:
			if i.m_begin > end_time:
				break
			if i.m_end < begin_time:
				continue
			span.append(i)
		return self.m_time[begin:end], self.m_signals[begin:end], span
	
	def on_key_press(self,event):
		print("DEBUG on_key_press button: %s"%(event.key))
		if event.key == u"right":
			self.draw(1)
		elif event.key == u"left":
			self.draw(-1)
		else:
			print("invalid key: %s"%(event.key))
			
	def on_btn_press(self, event):
		if event.button == 2:
			self.on_play(event)
			return
		if event.button != 1:
			return
		self.m_pos_line.set_xdata([0,0])
		self.m_pos_line.figure.canvas.draw()
		self.m_is_press = True
		self.m_x0 = event.xdata
		self.m_y0 = event.ydata    
		self.m_x1 = event.xdata
		self.m_y1 = event.ydata
		self.m_rect.set_width(self.m_x1 - self.m_x0)
		self.m_rect.set_height(self.m_y1 - self.m_y0)
		self.m_rect.set_xy((self.m_x0, self.m_y0))
		self.m_rect.set_linestyle('dashed')
		self.m_ax.figure.canvas.draw()
		
	def on_btn_release(self, event):
		if event.button != 1 :
			return
		self.m_is_press = False
		self.m_x1 = event.xdata
		self.m_y1 = event.ydata
		self.m_rect.set_width(self.m_x1 - self.m_x0)
		self.m_rect.set_height(self.m_y1 - self.m_y0)
		self.m_rect.set_xy((self.m_x0, self.m_y0))
		self.m_rect.set_linestyle('solid')
		self.m_ax.figure.canvas.draw()
		return [self.m_x0,self.m_x1,self.m_y0,self.m_y1]
		
	def on_motion(self, event):
		if self.m_is_press is False:
			return
		self.m_x1 = event.xdata
		self.m_y1 = event.ydata
		self.m_rect.set_width(self.m_x1 - self.m_x0)
		self.m_rect.set_height(self.m_y1 - self.m_y0)
		self.m_rect.set_xy((self.m_x0, self.m_y0))
		self.m_rect.set_linestyle('dashed')
		self.m_ax.figure.canvas.draw()
			
	def on_play(self, event):
		self.m_pos = self.m_x0
		start_sig = self.m_x0 
		end_sig = self.m_x1
		if start_sig > end_sig :
			start_sig, end_sig = end_sig, start_sig
		start_sig = int(math.ceil(self.m_fs * start_sig))
		end_sig = int(math.ceil(self.m_fs * end_sig))
		temp_signals = self.m_signals[start_sig : end_sig]
		#stream.write(temp_signals, len(temp_signals))
		sample_rate = self.m_fs
		frame_begin = 0
		frame_end = sample_rate
		while frame_begin < len(temp_signals):		
			if frame_end > len(temp_signals):
				frame_end = len(temp_signals)
			frame_signals = temp_signals[int(frame_begin):int(frame_end)]
			self.m_stream.write(frame_signals, len(frame_signals))
			if len(frame_signals) > 0 :
				add = len(frame_signals) / float(self.m_fs)
				self.m_pos += add
			self.m_pos_line.set_xdata([self.m_pos, self.m_pos])
			self.m_pos_line.set_ydata([self.m_y0, self.m_y1])
			self.m_pos_line.figure.canvas.draw()
			frame_begin , frame_end = frame_end, frame_end + sample_rate
		print("DEBUG play finished")
	
	def draw(self, num):
		plt.cla()
		coor_x, coor_y, span = self.get_xy(num)
		self.m_txt, = self.m_subplt.plot(coor_x, coor_y, fillstyle='full')
		self.m_pos_line, = self.m_subplt.plot([0,0], [-32000,32000], color='red')
		for i in span:
			c = self.get_counter() % 3
			self.m_subplt.axvspan(i.m_begin, i.m_end, facecolor=g_colors[c], alpha=0.5)
			self.m_subplt.text(i.m_begin, 2000 * c, str(i.m_begin), color='r', fontsize='x-small')
			self.m_subplt.text(i.m_end, 2000 * c, str(i.m_end), color='r', fontsize='x-small')
			self.inc_counter()
		self.m_txt.figure.canvas.draw()
	
	def plot(self):
		self.m_figure = plt.figure(figsize=(12,7))
		self.m_subplt = self.m_figure.add_subplot(111)
		self.draw(1)
		self.m_ax = plt.gca()
		self.m_rect = Rectangle((self.m_x0, self.m_y0), self.m_x1 - self.m_x0, self.m_y1 - self.m_y0, facecolor='None', edgecolor='green')
		self.m_ax.add_patch(self.m_rect)
		self.m_ax.figure.canvas.draw()
		#connect event
		self.m_figure.canvas.mpl_connect("button_press_event", self.on_btn_press)
		self.m_figure.canvas.mpl_connect("button_release_event", self.on_btn_release)
		self.m_figure.canvas.mpl_connect("motion_notify_event", self.on_motion)
		self.m_figure.canvas.mpl_connect("key_press_event",self.on_key_press)
		
	def run(self):
		self.read_vad()
		self.read_wave()
		self.start_audio()
		self.plot()
		
if __name__ == '__main__':
	a = VadAny("D:\\pywav\\1.txt", "D:\\pywav\\test.wav")
	a.run()
	plt.show()
		
		
		