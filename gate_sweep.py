#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Jun  5 12:32:29 2019

@author: Tjorben Matthes
"""
import visa
import time
#import numpy as np
import matplotlib
import matplotlib.pyplot as plt
import csv

matplotlib.rcParams.update({'font.size': 20}) #change letter-size for plots

rm = visa.ResourceManager() #find usb-resources
device = 'USB0::0x05E6::0x2614::4426492::INSTR'
k = rm.open_resource(device)#fill brackets with resource

v_sd = 0.01

v_start = 90
v_stop = 0
v_step = 0.5
t_delay = 0.5

v_rampstep = 1
t_ramp = 0.5

filename = 'sweep_1' #set device number for saved plot and data

#define functions
def ramp(ramp_start, ramp_final, ramp_step, ramp_intervall):
    ramp_diff = ramp_final - ramp_start
    if ramp_diff > 0: #check if ramping has to go up
        r_steps = int(round(ramp_diff/ramp_step)) #set stepcount
        for i in range(r_steps+1): #for-loop for ramping up
            k.write('smub.source.levelv =', str(ramp_start + i*ramp_step)) #write new voltage on every loop iteration
            time.sleep(ramp_intervall) #wait specified time

    if ramp_diff < 0: #check if ramping has to go down
        r_steps = int(abs(round(ramp_diff/ramp_step))) #set stepcount
        for i in range(r_steps+1): #for-loop for ramping up
            k.write('smub.source.levelv =', str(ramp_start - i*ramp_step)) #write new voltage on every loop iteration
            time.sleep(ramp_intervall) #wait specified time
        
    k.write('smub.source.levelv =', str(ramp_final)) #apply final voltage for gate sweep
    return;
    
def sweep(v_start, v_stop, v_step, v_int):
    sweep_steps = round(abs((v_start-v_stop) / v_step)) #get step count (has to be an integer)
    voltage = [] #initialize list for voltage values
    cur = [] #initialize list for current values
    if v_start < v_stop: #check if sweeping has to go up
        for j in range(sweep_steps+1):
            k.write('smub.source.levelv =', str(v_start + j*v_step)) #set new voltage (note, that the first one is not change)
            time.sleep(t_delay) #wait till measuring
            k.write('current = smua.measure.i()') #measure current and write to internal variable
            cur.append(float(k.query('print(current)'))) #copy internal variable to local list
            voltage.append(v_start + j*v_step) #create list with voltage values
            
    if v_start > v_stop: #check if sweeping has to go down
        for j in range(sweep_steps+1):
            k.write('smub.source.levelv =', str(v_start - j*v_step)) #set new voltage (note, that the first one is not change)
            time.sleep(t_delay)  #wait till measuring
            k.write('current = smua.measure.i()') #measure current and write to internal variable
            cur.append(float(k.query('print(current)')))  #copy internal variable to local list
            voltage.append(v_start - j*v_step) #create list with voltage values
    return voltage, cur;

k.write('errorqueue.clear()') #clear error-cache

#setting source-drain voltage
k.write('smua.source.levelv =', str(v_sd)) #Set source-drain voltage
k.write('smua.source.output = 1')#turn on output
#ramping gate up
k.write('smub.source.levelv = 0') #set starting gate-voltage to 0
k.write('smub.source.output = 1') #turn on output
ramp(0, v_start, v_rampstep, t_ramp)

#sweeping the gate
voltage, cur = sweep(v_start, v_stop, v_step, t_delay)

voltage_b, cur_b = sweep(v_stop, v_start, v_step, t_delay)

#plotting
picture = plt.figure(figsize=(12,9))#size in inches, width * height 
plt.plot(voltage, cur, label='first sweep')
plt.plot(voltage_b, cur_b, label='backsweep')
plt.xlabel('$V_G$ (in V)')
plt.ylabel('$I_{SD}$ (in A)')
plt.legend()
plt.show
picture.savefig(filename+'.pdf', bbox_inches='tight') #save graph

#writing data
with open( filename +'.csv', 'w', newline = '') as f:
    fwriter = csv.writer(f, delimiter = ';', quotechar='"')
    lenv = len(voltage)
    fwriter.writerow(['voltage (in V)', 'current first sweep (in A)', 'current back sweep (in A)'])
    for i in range(lenv):
        data = [voltage[i], cur[i], cur_b[lenv-i-1]]
        fwriter.writerow(data)

#ramp down
k.write('volt = smub.measure.v()')
v_gnow = float(k.query('print(volt)')) #gets the voltage momentarilly apllied to the gate
ramp(v_gnow, 0, v_rampstep, t_ramp)
   
    
#shutting of outputs
k.write('smub.source.levelv = 0') #apply 0V
k.write('smua.source.levelv = 0')
k.write('smua.source.output = 0')
k.write('smub.source.output = 0')