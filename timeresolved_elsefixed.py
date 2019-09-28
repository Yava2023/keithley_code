# -*- coding: utf-8 -*-
"""
Created on Thu Jun  6 14:59:25 2019

@author: Tjorben Matthes
"""

import visa
import time
import csv
import matplotlib
import matplotlib.pyplot as plt

matplotlib.rcParams.update({'font.size': 20}) #change letter-size for plots

rm = visa.ResourceManager() #find usb-resources
k = rm.open_resource('USB0::0x05E6::0x2614::4426492::INSTR')#fill brackets with resource

v_sd = 0.01
v_gate = 0
v_rampstep = 1
t_ramp = 0.5

t_interval = 0.050
t_total = 300

filename = 'time_resolved_1' #set name for saved plot and data

#define function
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

k.write('errorqueue.clear()') #clear error-cache

#setting source-drain voltage
k.write('smua.source.levelv =', str(v_sd)) #Set source-drain voltage
k.write('smua.source.output = 1')#turn on output
#ramping gate up
k.write('smub.source.levelv = 0') #set starting gate-voltage to 0
k.write('smub.source.output = 1') #turn on output
ramp(0, v_gate, v_rampstep, t_ramp)

#do time_resolved measurement
ct_max = round(t_total/t_interval) #calculate maximum number of measurements

#prefine arrays for the measurement with 0s
t_measure = [0.0] * ct_max #array for the exact times of measurement
cur = [0.0] * ct_max #array for the current measurements

t_diff = 0 #set starting time difference to reference time to 0
ct = 0 #set loop-counter to 0
t_ref = time.perf_counter() #get time from system-clock and use as reference

while t_diff < t_total:
    k.write('current = smua.measure.i()') #measure current and write to internal variable
    t_diff = time.perf_counter() - t_ref #get time of measurement
    t_measure[ct] =float(t_diff) #write time of measurement in array
    cur[ct]=float(k.query('print(current)')) #copy internal variable to local list
    ct = ct +1 #count 1 up
    time.sleep(t_interval) #wait specified interval

#cut arrays to the measured values
t_measure = t_measure[0:ct]
cur = cur[0:ct]
    
#plotting
picture = plt.figure(figsize=(12,9))#size in inches, width * height
plt.plot(t_measure, cur)
plt.xlabel('time (in s)')
plt.ylabel('$I_{SD}$ (in A)')
plt.show()
picture.savefig(str(filename)+'.pdf', bbox_inches='tight') #save graph
    
#writing data
with open(str(filename)+'.csv', 'w', newline = '') as f:
    fwriter = csv.writer(f, delimiter = '\t', quotechar = '"')
    counts = len(t_measure)
    fwriter.writerow(['time (in s)', 'current (in A)'])
    for i in range(counts):
        data = [t_measure[i], cur[i]]
        fwriter.writerow(data)

#ramping gate down
k.write('volt = smub.measure.v()')
v_gnow = float(k.query('print(volt)')) #gets the voltage momentarilly apllied to the gate
ramp(v_gnow, 0, v_rampstep, t_ramp)

#shutting of outputs
k.write('smub.source.levelv = 0') #apply 0V
k.write('smua.source.levelv = 0')
k.write('smua.source.output = 0')
k.write('smub.source.output = 0')