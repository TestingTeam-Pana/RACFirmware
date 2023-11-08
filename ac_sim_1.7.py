import tkinter as tk
from tkinter import *
from tkinter import messagebox
import threading
import time
import serial
import random
import datetime

g_simulator_ver = "1.7"
comport_row   = 1
button_row    = 2
temp_row      = 4
mode_row      = 10
status_row    = 11

# AC Properties
g_ac_temp       = 24
g_room_temp     = 26
g_ac_mode       = 0
g_fan_speed     = 0
gen_mode      = 0
g_gen_mode    = 0
g_nano_eg     = 0
g_sleep_mode  = 0   
g_power_on    = 1
g_convert_mode = 110
g_motion_simulate      = 0
g_en_mutli_cmd_support = 0
vertical_swing_ctrl    = 1
horizonatal_swing_ctrl = 1
eco_mode               = 0
g_powerful_mode        = 0
econavi_or_msensor_ctrl= 0
user_prgrmd_timer      = [0] * 8
start_stop_filter_calib= 0
disp_ctrl              = 1
evap_clean_mode        = 0
g_default_sleep_mode   = 0
g_pid_value            = [0x01, 0x01]

# Some model of AC 
# 102179 is AC model with out matter
# 130199 is AC model with matter 
g_model_id             = [130, 199]  # Update model id here for testing needs 
g_hamcu_psn            = [0] * 33 # 23ABCDEFGH12345
g_hamcu_psn_len        = 0 
g_pkt_version          = 2 
g_select_CAC           = 0     # select CAC model otherwise AC model default
g_port_val             = 0
  
ser = serial.Serial()

def send_cmd(cla, cmd, data, is_data):
    global g_pkt_version
    hamcu_cmd = [g_pkt_version, 0, cla, cmd]
    if is_data == True:
        print('Is data True= {}', len(data))
        hamcu_cmd.append(len(data))

        for i in range(len(data)):
            if isinstance(data[i], int):
                hamcu_cmd.append(data[i])
            else:
                hamcu_cmd.append(ord(data[i]))
            #hamcu_cmd.append(data[i])

    for i in range(75 - len(hamcu_cmd)):
        hamcu_cmd.append(0)
    chk_sum = 0
    print("HAMCU CMD:", hamcu_cmd)
    for i in hamcu_cmd:
        if isinstance(i, int):
            chk_sum += i
        else:
            chk_sum += ord(i)
        chk_sum = chk_sum & 0xFF
    hamcu_cmd.append(256 - chk_sum) 
    print('hamcucmd:',hamcu_cmd)
#    print(list(map(hex, hamcu_cmd)))
    ser.write(hamcu_cmd)
    print('Command Sent =', cmd)
    update_ac_ui_status()

def button1_clicked():
    print('"Onboard Button" button Clicked')
    data = [2]
    send_cmd(0, 28, data, True)

def button2_clicked():
    print('"Power" button Clicked')
    global g_power_on
    if(g_power_on == 1):
        g_power_on = 0x00
    elif(g_power_on == 0x00):
        g_power_on = 0x01
    data = [0x00, 0x00, g_power_on]
    send_cmd(0xA1, 0x03, data, True)

def button3_clicked():
    print('"Room temp Simulate Button" button Clicked')
    global g_room_temp
    #g_room_temp[0] = int(random.randint(16, 30))
    #g_room_temp[1] = int(random.randint(0, 99))

    rm_tmp_int = random.randint(16, 30)
    rm_tmp_dec = random.randint(0, 99)
    print("Room Temp:", rm_tmp_int)
    print("Room Temp Dec:", rm_tmp_dec)
    g_room_temp = rm_tmp_int
    roomtemp_status.config(text=f"{g_room_temp}")

    data = [0x11, 0x02, rm_tmp_int, rm_tmp_dec]
    send_cmd(0xA1, 0x03, data, True)

def button4_clicked():
    print('"Factory Reset" button Clicked')
    send_cmd(0x00, 0x19, 0x00, False)
def nanoeg_checked():
    global g_nano_eg
    if nanoe_var.get() == 1:
        print("Nano-e/g Checked")
        g_nano_eg = 1
    elif nanoe_var.get() == 0:
        print("Nano-e/g Un-Checked")
        g_nano_eg = 0        
    data = [0x03, 0x00, g_nano_eg]
    send_cmd(0xA1, 0x03, data, True)

def powerful_checked():
    global g_powerful_mode 
    if powerful_var.get() == 1:
        print("Powerful Mode Checked")
        g_powerful_mode = 1
    elif powerful_var.get() == 0:
        print("Powerful Mode Un-Checked")
        g_powerful_mode = 0  
    data = [0x08, 0x00, g_powerful_mode]
    send_cmd(0xA1, 0x03, data, True)

def multicmd_checked():
    global g_en_mutli_cmd_support
    if multicmd_var.get() == 1:
        print("Multi Cmd Checked")
        g_en_mutli_cmd_support = 1
    elif multicmd_var.get() == 0:
        print("Multi Cmd Un-Checked")
        g_en_mutli_cmd_support = 0      

def port1_entry():
    global g_port_val
    global g_power_on
    global disp_ctrl

    g_port_val = port1.get()

    g_power_on = 0x01
    disp_ctrl = 0x01
    update_ac_ui_status()
    t1 = threading.Thread(target=rx_task, name='t1')
    t1.daemon = True

    # starting threads
    t1.start()


def submit_entry1():
    global g_ac_temp
    entry1_value = entry1.get()
    print("Temp:", entry1_value)

    if entry1_value.isdigit() and 16 <= int(entry1_value) <= 30:
        g_ac_temp = int(entry1_value)
        print("Set AC Temp:", entry1_value)
        data = [0x01, 0x00, g_ac_temp, 0]
        send_cmd(0xA1, 0x03, data, True)
    else:
        print("Invalid Temprature value : Enter 16-30")
        messagebox.showerror("Error", "Invalid Temprature value : Enter 16-30 ")
    
    entry1.delete(0, tk.END)
    #entry1.insert(0, g_ac_temp)


def submit_entry4():
    line_test_str = entry4.get()
    
    #line_test_str = "ABCDEFGH123456789"
    print('"Line Test" button was clicked')
                   
    print('line test str', line_test_str)
    #line_test_entry.set_text(str(line_test_str))
    #data =[65, 66, 67, 68, 69, 70, 71, 49, 50, 51, 52, 53, 54, 55, 56, 57]
    #data = [50, 48, 67, 80, 65, 74, 67, 71, 83, 85, 48, 48, 48, 48, 50]
    
    #For pansoninc brand SN should start with year (Ex: 21(year) )
    data = [0x32, 0x31, 0x41, 0x42, 0x43, 0x44, 0x45, 0x46, 0x47, 0x48, 0x30, 0x30, 0x30, 0x30, 0x31]
    now  = datetime.datetime.now()
    year = now.year - 2000    
    year_str = str(year)
    rand1    = random.randint(0, 9)
    rand2    = random.randint(0, 9)
    rand3    = random.randint(0, 9)
    rand4    = random.randint(0, 9)  
    rand5    = random.randint(0, 9)  
    rand6    = random.randint(0, 9)  

    data[0]  = 0x30 + int(year_str[0]) # start with year, for example year 2021, it should start with '2' '1'
    data[1]  = 0x30 + int(year_str[1])
    data[9]  = 0x30 + rand1
    data[10] = 0x30 + rand2
    data[11] = 0x30 + rand3
    data[12] = 0x30 + rand4
    data[13] = 0x30 + rand5
    data[14] = 0x30 + rand6
    print(data)        
    send_cmd(0xA3, 0x01, data, True)  

def submit_entry3():
    global data1
    entry3_value = entry3.get()
    print("Raw Command:", entry3_value)
    data1 = entry3_value.split(",")
    #data1 = list(map(int, data1, base=16))
    for i in range(len(data1)):
        data1[i] = int(data1[i],base=16)
    data1.insert(1, 0)
    print("New Raw Data", data1)
    send_cmd(0xA1, 0x03, data1, True)

def submit_entry5():
    QRcode_value = entry5.get()
    print("QR Code:", QRcode_value)
    print("Length", len(QRcode_value))
    #for i in range(0 , len(QRcode_value)):
    #    if isinstance(QRcode_value[i], int):
    #        QRcode_value[i] = QRcode_value[i]
    #    else:
    #        QRcode_value[i] = ord(QRcode_value[i])
    send_cmd(0xA3, 0x01, QRcode_value, True)

def submit_entry6():
    PSN_value = entry6.get()
    print("PSN:", PSN_value)
    print("Length", len(PSN_value))
    send_cmd(0xA3, 0x01, PSN_value, True)

def submit_entry2():
    global g_fan_speed
    entry2_value = entry2.get()
    print("Fan Speed:", entry2_value)
    if entry2_value.isdigit() and 0 <= int(entry2_value) <= 6 :
        g_fan_speed = int(entry2_value)
        print("Set Fan Speed:", g_fan_speed)
        data = [0x02, 0x00, g_fan_speed]
        send_cmd(0xA1, 0x03, data, True)
    else:
        print("Invalid entry for Fan speed")
        messagebox.showerror("Error", "Invalid entry for Fan Speed, Valid 0 - 6 ")

    entry2.delete(0, tk.END)

def update_ac_ui_status():
    global g_ac_temp
    global g_ac_mode
    global g_fan_speed
    global g_nano_eg    
    global g_gen_mode
    global g_power_on
    global g_powerful_mode   

    global vertical_swing_ctrl  
    global horizonatal_swing_ctrl  

    global eco_mode  
 
    global econavi_or_msensor_ctrl  
    global gen_mode  
    global user_prgrmd_timer 
    global start_stop_filter_calib  
    global disp_ctrl  
    global evap_clean_mode
    global g_pkt_version  
    global g_select_CAC
    global g_room_temp
    global g_hamcu_psn
     
    print("UPATING UI STATUS")
    if g_ac_mode == 0x00 :
        ac_mode_name = "Auto"
    elif g_ac_mode == 0x01 :
        ac_mode_name = "Cool"
    elif g_ac_mode == 0x02 :
        ac_mode_name = "Dry"
    elif g_ac_mode == 0x03 :
        ac_mode_name = "Fan"
    elif g_ac_mode == 0x04 :
        ac_mode_name = "Heat"
        
    if g_power_on == 0x00 :
        ac_power_status_str = "OFF"
    elif g_power_on == 0x01 :
        ac_power_status_str = "ON"

    if disp_ctrl == 0x00 :
        ac_display_status_str = "OFF"
    elif disp_ctrl == 0x01 :
        ac_display_status_str = "ON"

    if g_nano_eg == 0x00 :
        nanoe_status_str = "OFF"
    elif g_nano_eg == 0x01 :
        nanoe_status_str = "ON"

    if g_powerful_mode == 0x00 :
        powerful_mode_str = "OFF"
    elif g_powerful_mode == 0x01 :
        powerful_mode_str = "ON"

    if g_fan_speed == 0x00 :
        fan_speed_str = "Auto"
    elif g_fan_speed == 0x01 :
        fan_speed_str = "Quiet (1)"
    elif g_fan_speed == 0x02 :
        fan_speed_str = "Low (2)"
    elif g_fan_speed == 0x03 :
        fan_speed_str = "Medium 1 (3)"
    elif g_fan_speed == 0x04 :
        fan_speed_str = "Medium (4)"
    elif g_fan_speed == 0x05 :
        fan_speed_str = "High 1(5)"
    elif g_fan_speed == 0x06:
        fan_speed_str = "High (6)"

    psn_str = ''.join(chr(i) for i in g_hamcu_psn)
    
    temp_status.config(text=f"{g_ac_temp}")
    roomtemp_status.config(text=f"{g_room_temp}")
    mode_status.config(text=f"{ac_mode_name}")
    fan_status.config(text=f"{fan_speed_str}")
    power_status.config(text=f"{ac_power_status_str}")
    display_status.config(text=f"{ac_display_status_str}")
    nanoeg1_status.config(text=f"{nanoe_status_str}")
    pwrful_status.config(text=f"{powerful_mode_str}")
    psn_status.config(text=f"{psn_str}")


def on_radio_button_change():
    global g_ac_mode
    
    selected_option = radio_var.get()
    print("Selected option:", selected_option)
    ac_mode_name = selected_option

    if selected_option == "Auto":
        g_ac_mode = 0x00 
        print('Auto Selected')
        data = [0x06, 0x00, g_ac_mode]
        send_cmd(0xA1, 0x03, data, True)
    elif selected_option == "Cool":
        g_ac_mode = 0x01 
        print('Cool Selected')
        data = [0x06, 0x00, g_ac_mode]
        send_cmd(0xA1, 0x03, data, True)
    elif selected_option == "Dry":
        g_ac_mode = 0x02 
        print('Dry Selected')
        data = [0x06, 0x00, g_ac_mode]
        send_cmd(0xA1, 0x03, data, True)
    elif selected_option == 'Fan':
        g_ac_mode = 0x03                 
        print("Fan selected")
        data = [0x06, 0x00, g_ac_mode]
        send_cmd(0xA1, 0x03, data, True)
    elif selected_option == 'Heat':
        g_ac_mode = 0x04                
        print("Heat selected")
        data = [0x06, 0x00, 0x04]
        send_cmd(0xA1, 0x03, data, True)                
    else:
        print("Invalid mode ", selected_option)
    #radio_var.set(None)

def process_input(msg):
    print('msg[0]', msg[0])
    print('msg[1]', msg[1])
    print('msg[2]', msg[2])
    print('msg[3]', msg[3])
    if msg[3] & 128:
        print('RESPONSE')
        resp = ser.read(73)
        print('RESP = ', resp)
        if((msg[2] == 0xa3) and msg[3]== 0x81):
            print('Line test Version Number Major ={} Minor = {}', str(resp[2]), str(resp[3]))     
    else:
        print('COMMAND')
        cmd = ser.read(72)
        print('CMD =', list(map(hex, cmd)))
        send_resp(msg, cmd)

def send_resp(msg, cmd):
    global g_nano_eg
    global g_ac_temp
    global g_ac_mode
    global g_gen_mode
    global g_en_mutli_cmd_support
    global g_sleep_mode
    global g_power_on
    global g_convert_mode
    
    global g_fan_speed 
    global vertical_swing_ctrl  
    global horizonatal_swing_ctrl  
    global eco_mode  
    global g_powerful_mode  
    global econavi_or_msensor_ctrl  
    global gen_mode  
    global user_prgrmd_timer 
    global start_stop_filter_calib  
    global disp_ctrl  
    global evap_clean_mode
    global g_pkt_version  
    global g_select_CAC
    global g_hamcu_psn_len
    global g_hamcu_psn
    global g_model_id
    global g_pid_value
  
    if((msg[2] == 0x00) and (msg[3] == 0x06 or msg[3] == 0x0C or msg[3] == 0x10 or msg[3] == 0x11 or msg[3] == 0x12
        or msg[3] == 0x18 or msg[3] == 0x1A or msg[3] == 0x1D or msg[3] == 0x21 or msg[3] == 0x22 or msg[3] == 0x23 
        or msg[3] == 0x24 or msg[3] == 0x1F or msg[3] == 0x1E or msg[3] == 0x26 or msg[3] == 0x27 or msg[3] == 0x28)):
        print('CLASS 0 CMD')
        # Query adpter ver 
        if(msg[3]==0x06):
            hamcu_resp = [msg[0], msg[1], msg[2], msg[3]+128, 0, 1, 1]	
        # Supported inf ver 
        elif(msg[3]==0x10): 
            hamcu_resp = [msg[0], msg[1], msg[2], msg[3]+128, 0, 1, 1]
        # Operational state 
        elif(msg[3]==0x18): 
            if (g_en_mutli_cmd_support):
                # Magmeet hamcu
                hamcu_resp = [msg[0], msg[1], msg[2], msg[3]+128, 0, 3, 1, 1, 0]	 
            else:
                hamcu_resp = [msg[0], msg[1], msg[2], msg[3]+128, 0, 0, 0]	   	 
        # Get dev mdl 
        elif(msg[3]==0x11):
            if (g_select_CAC):
               hamcu_resp = [msg[0], msg[1], msg[2], msg[3]+128, 0, 4, 102, 200, g_pid_value[0], g_pid_value[1]]  # 102200 is valid model for CAC category                       
            else:       
               hamcu_resp = [msg[0], msg[1], msg[2], msg[3]+128, 0, 4, g_model_id[0], g_model_id[1], g_pid_value[0], g_pid_value[1]]  # 10232, 102179 are valid models for AC category                       
        # Get dev capabilities 
        elif(msg[3]==0x12): 
            hamcu_resp = [msg[0], msg[1], msg[2], msg[3]+128, 0, 4, 0, 0, 0, 0] 
        # Get appliance state = "H11 H12 H13"
        elif(msg[3]==0x1A):
            hamcu_resp = [msg[0], msg[1], msg[2], msg[3]+128, 0, 1+12, 1, 0x48, 0x31, 0x31, 0x20, 0x48, 0x31, 0x32, 0x20, 0x48, 0x31, 0x33, 0x20]
        # Get lockdown states     
        elif(msg[3]==0x25):
            hamcu_resp = [msg[0], msg[1], msg[2], msg[3]+128, 0, 2, 0, 0]
        # Update hamcu disp
        elif(msg[3]==0x26):
            print('DISP CMD')
            #if (msg[5]==0x00):
            #    print('CLEAR DISP INFO')
            #else:
            #    print('SET DISP INFO')
            #print(msg[5])
            #print("INFO: %c %c" %(chr(msg[8]), chr(msg[9])))
            hamcu_resp = [msg[0], msg[1], msg[2], msg[3]+128]
        elif(msg[3]==0x27):  # Set hamcu psn
            print('Set PSN CMD')
            g_hamcu_psn_len = cmd[0] 
            # Copy PSN            
            for i in range(g_hamcu_psn_len):
                g_hamcu_psn[i] = cmd[1+i]
            hamcu_resp = [msg[0], msg[1], msg[2], msg[3]+128]            
        elif(msg[3]==0x28):  # Get hamcu psn
            print('Get PSN CMD')
            hamcu_resp = [msg[0], msg[1], msg[2], msg[3]+128, 0, g_hamcu_psn_len]
            for i in range(g_hamcu_psn_len):
                hamcu_resp.append(g_hamcu_psn[i])
        else:
            hamcu_resp = [msg[0], msg[1], msg[2], msg[3]+128]
        
        for i in range(76 - len(hamcu_resp)):
            hamcu_resp.append(0)
        chk_sum = 0
        hamcu_resp[0] = g_pkt_version
        
        for i in hamcu_resp:
            chk_sum += i
        chk_sum = chk_sum & 0xFF
        hamcu_resp.append(256 - chk_sum) 
        update_ac_ui_status()
        ser.write(hamcu_resp)
    elif((msg[2] == 0xa1) and (msg[3] == 0x05)):  #Set all properties
        print('in set all prop data', cmd[1]) 
        tx_data = [msg[0],msg[1],msg[2],msg[3]+128]  
        for i in range(76 - len(tx_data)):
            tx_data.append(0)
        
        tx_data[0] = g_pkt_version
       
        offset = 1                
        if(cmd[offset + 0] != 0xFF):  
            g_power_on = cmd[offset + 0]             	
            print('Recieved power on/off command =',g_power_on)
            
        if (cmd[offset + 1] != 0xFF) and (cmd[offset +2] != 0xFF):
            g_ac_temp = cmd[offset + 1] 
            print('Received AC Temp =',g_ac_temp)
            ac_temp_entry.set_text(str(g_ac_temp))
            
        if (cmd[offset + 3] != 0xFF):
            g_fan_speed = cmd[offset + 3] 
            print('Recieved Fan speed =',g_fan_speed) 
        
        if (cmd[offset + 4] != 0xFF):
            vertical_swing_ctrl = cmd[offset + 4] 
            print('Recieved vertical_swing_ctrl =',vertical_swing_ctrl) 
        
        if (cmd[offset + 5] != 0xFF):
            horizonatal_swing_ctrl = cmd[offset + 5] 
            print('Recieved horizonatal_swing_ctrl =',horizonatal_swing_ctrl) 
        
        if (cmd[offset + 6] != 0xFF):
            g_ac_mode = cmd[offset + 6] 
            print('Recieved ac mode =',g_ac_mode)
            
        if (cmd[offset + 7] != 0xFF):
            g_nano_eg = cmd[offset + 7] 
            print('Recieved nanoeg =',g_nano_eg) 
            
        if (cmd[offset + 8] != 0xFF):
            eco_mode = cmd[offset + 8] 
            print('Recieved eco mode =',eco_mode)
        
        if (cmd[offset + 9] != 0xFF):
            g_powerful_mode = cmd[offset + 9] 
            print('Recieved powerful mode =',g_powerful_mode)                  

        if (cmd[offset + 10] != 0xFF):
            g_sleep_mode = cmd[offset + 10] 
            print('Recieved sleep mode =',g_sleep_mode) 
            
        if (cmd[offset + 11] != 0xFF):
            econavi_or_msensor_ctrl = cmd[offset + 11] 
            print('Recieved econavi_or_msensor_ctrl mode =',econavi_or_msensor_ctrl)

        if (cmd[offset + 12] != 0xFF):
            gen_mode = cmd[offset + 12] 
            print('Recieved gen_mode =',gen_mode)                                    

        if (cmd[offset + 13] != 0xFF):
            user_prgrmd_timer[0] = cmd[offset + 13]
            user_prgrmd_timer[1] = cmd[offset + 14] 
            user_prgrmd_timer[2] = cmd[offset + 15]
            user_prgrmd_timer[3] = cmd[offset + 16]
            print('Recieved timer1 info')  
            
        if (cmd[offset + 17] != 0xFF):    
            user_prgrmd_timer[4] = cmd[offset + 17]
            user_prgrmd_timer[5] = cmd[offset + 18] 
            user_prgrmd_timer[6] = cmd[offset + 19]
            user_prgrmd_timer[7] = cmd[offset + 20]      
            print('Recieved timer2 info')    
            
        if (cmd[offset + 24] != 0xFF):    
            start_stop_filter_calib = cmd[offset + 24]
            print('Recieved start_stop_filter_calib =',start_stop_filter_calib)  

        if (cmd[offset + 26] != 0xFF):    
            disp_ctrl = cmd[offset + 26]
            print('Recieved disp_ctrl =',disp_ctrl) 
                                 
        if (cmd[offset + 27] != 0xFF):    
            evap_clean_mode = cmd[offset + 27]
            print('Recieved evap_clean_mode =',evap_clean_mode)

        if (cmd[offset + 36] != 0xFF):    
            g_convert_mode = cmd[offset + 36]
            print('Recieved convert_mode =',g_convert_mode)      
                                  
        print('len txdata{}',len(tx_data))
        
        y = 0
        for i in tx_data:
            y = (y + i)&0xFF     
        tx_data.append(256-y)  
        print('property set all resp created')

        print(list(map(hex, tx_data)))
        update_ac_ui_status()
        ser.write(tx_data)                                              
    elif((msg[2] == 0xa1) and (msg[3] == 0x04)):  #Get all properties
        print('in get all prop data', cmd[1])
        tx_data = [msg[0],msg[1],msg[2],msg[3]+128]  
        for i in range(76 - len(tx_data)):
            tx_data.append(0)

        tx_data[0] = g_pkt_version 
        tx_data[5] = 45
        
        n = 6 + tx_data[5]
        for i in range(6, n):
            tx_data[i] = 0xff
        
        offset = 6   
        tx_data[offset+0]  = g_power_on    # power status
        tx_data[offset+1]  = g_ac_temp 	     # AC temp byte1
        tx_data[offset+2]  = 0             # AC temp byte2
        tx_data[offset+3]  = g_fan_speed  
        tx_data[offset+4]  = vertical_swing_ctrl                                 
        tx_data[offset+5]  = horizonatal_swing_ctrl  
        tx_data[offset+6]  = g_ac_mode                                          
        tx_data[offset+7]  = g_nano_eg
        tx_data[offset+8]  = eco_mode
        tx_data[offset+9]  = g_powerful_mode
        tx_data[offset+10] = g_sleep_mode  #sleep mode status
        tx_data[offset+11] = econavi_or_msensor_ctrl
        tx_data[offset+12] = 1             # motion control enable
        tx_data[offset+13] = 0             # motion detect values                                
        tx_data[offset+14] = gen_mode      # gen mode
        
        tx_data[offset+15] = 30            # Room temp byte1
        tx_data[offset+16] = 0             # Room temp byte2 
                                       
        tx_data[offset+17] = user_prgrmd_timer[0]      # Timer info
        tx_data[offset+18] = user_prgrmd_timer[1]
        tx_data[offset+19] = user_prgrmd_timer[2]
        tx_data[offset+20] = user_prgrmd_timer[3]
        tx_data[offset+21] = user_prgrmd_timer[4]
        tx_data[offset+22] = user_prgrmd_timer[5]
        tx_data[offset+23] = user_prgrmd_timer[6]
        tx_data[offset+24] = user_prgrmd_timer[7]                                                                       
        
        tx_data[offset+25] = 1                       #Buzzer enabled
        tx_data[offset+26] = 1                       #lockdown enabled
        tx_data[offset+27] = 1                       #lockdown ctrl                  
        tx_data[offset+28] = 1                       #filter dust level
        tx_data[offset+29] = start_stop_filter_calib  #start/stop filt calib                 
        tx_data[offset+30] = 3                       #filter calib status                                  
        tx_data[offset+31] = 0                       #device power mode
        tx_data[offset+32] = disp_ctrl               #disp ctrl
        tx_data[offset+33] = evap_clean_mode         #Evap clean mode
        tx_data[offset+34] = 35                      #outdoor temp byte1
        tx_data[offset+35] = 0                       #outdoor temp byte2
        
        tx_data[offset+36] = 0                       #New on timer 4 bytes
        tx_data[offset+37] = 0
        tx_data[offset+38] = 0
        tx_data[offset+39] = 0
        tx_data[offset+40] = 0                       #New off timer 4 bytes
        tx_data[offset+41] = 0
        tx_data[offset+42] = 0
        tx_data[offset+43] = 0
        tx_data[offset+44] = g_convert_mode          #Convertible mode

        print('len txdata{}',len(tx_data))
        y = 0
        for i in tx_data: 
            y = (y + i)&0xFF     
        tx_data.append(256-y)  
        print('property get all resp created')
        print(tx_data)
        update_ac_ui_status()
        ser.write(tx_data)
    elif((msg[2] == 0xa1) and (msg[3] == 0x02)):
        print('in get prop data', cmd[1])
        tx_data = [msg[0],msg[1],msg[2],msg[3]+128]  
        for i in range(76 - len(tx_data)):
            tx_data.append(0)
       
        tx_data[0] = g_pkt_version      
        print('I am here cmd1', cmd[1])

        if(cmd[1] == 0x00):
            print('Recieved power on/off command')
            tx_data[5] = 1
            tx_data[6] = g_power_on 
        elif(cmd[1] == 0x01):
            print('Recieved AC Temp')
            tx_data[5] = 2
            tx_data[6] = g_ac_temp
            tx_data[7] = 0
        elif(cmd[1] == 0x02):
            print('Recieved AC FAN Speed')
            tx_data[5] = 1
            tx_data[6] = g_fan_speed
        elif(cmd[1] == 0x03):
            print('I am here nana')
            print('Recieved NANO-EG status')                  
            tx_data[5] = 1
            tx_data[6] = g_nano_eg
        elif(cmd[1] == 0x04):
            print('Recieved AC Vertical Swing')
            tx_data[5] = 1
            tx_data[6] = vertical_swing_ctrl
        elif(cmd[1] == 0x05):
            print('Recieved AC Horizontal Swing')
            tx_data[5] = 1
            tx_data[6] = horizonatal_swing_ctrl
        elif(cmd[1] == 0x06):
            print('Recieved AC Mode Control')
            tx_data[5] = 1
            tx_data[6] = g_ac_mode
        elif(cmd[1] == 0x07):
            print('Recieved AC Sleep mode')
            tx_data[5] = 1
            tx_data[6] = g_sleep_mode
        elif(cmd[1] == 0x08):
            print('Recieved AC Power full Mode')
            tx_data[5] = 1
            tx_data[6] = g_powerful_mode
        elif(cmd[1] == 0x09):
            print('Recieved AC Display')
            tx_data[5] = 1
            tx_data[6] = disp_ctrl
        elif(cmd[1] == 0x0A):
            print('Recieved AC Evaporator Clean')
            tx_data[5] = 1
            tx_data[6] = evap_clean_mode
        elif(cmd[1] == 0x0B):
            print('Recieved Power Capping')
            tx_data[5] = 2
            tx_data[6] = 50
            tx_data[7] = 0    
        elif(cmd[1] == 0x0C):
            print('Recieved AC Eco Mode')
            tx_data[5] = 1
            tx_data[6] = eco_mode
        elif(cmd[1] == 0x0D):
            print('Recieved AC Filter Calibertion')
            tx_data[5] = 1
            tx_data[6] = start_stop_filter_calib
        elif(cmd[1] == 0x0E):
            print('Recieved user program timer')
            tx_data[5] = 8
            tx_data[6] = 0
            tx_data[7] = 0
            tx_data[8] = 0
            tx_data[9] = 0
            tx_data[10] = 0
            tx_data[11] = 0
            tx_data[12] = 0
            tx_data[13] = 0
        elif(cmd[1] == 0x0F):
            print('Recieved filter dust level')
            tx_data[5] = 1
            tx_data[6] = 1
        elif(cmd[1] == 0x10):
            print('Recieved filter calib status')
            tx_data[5] = 1
            tx_data[6] = 3
        elif(cmd[1] == 0x11):
            print('Recieved room temp')
            tx_data[5] = 2
            tx_data[6] = 28
            tx_data[7] = 5
        elif(cmd[1] == 0x12):
            print('Recieved Motion Sens on/off')
            tx_data[5] = 1
            tx_data[6] = 1
        elif(cmd[1] == 0x13):
            print('Recieved Motion Sens value')
            tx_data[5] = 1
            tx_data[6] = 0x07 
        elif(cmd[1] == 0x14):
            print('Recieved Gen mode status')
            tx_data[5] = 1
            tx_data[6] = 0x03
        elif(cmd[1] == 0x15):
            print('Recieved Device input power mode')
            tx_data[5] = 1
            tx_data[6] = 0   # Grid mode
        elif(cmd[1] == 0x16):
            print('Recieved Outdoor temp')
            tx_data[5] = 2
            tx_data[6] = 0   # 0.00
            tx_data[7] = 0
        elif(cmd[1] == 0x17):
            print('Recieved new on timer')
            tx_data[5] = 4
            tx_data[6] = 0
            tx_data[7] = 0
            tx_data[8] = 0
        elif(cmd[1] == 0x18):
            print('Recieved new off timer')
            tx_data[5] = 4
            tx_data[6] = 0
            tx_data[7] = 0
            tx_data[8] = 0
        elif(cmd[1] == 0x19):
            print('Recieved convertible mode')
            tx_data[5] = 1
            tx_data[6] = g_convert_mode

        print('len txdata{}',len(tx_data))
        y = 0
        for i in tx_data:
            y = (y + i)&0xFF     
        #   send_sum = (send_sum + j)
        tx_data.append(256-y)  
        print('property get resp created')
        print(list(map(hex, tx_data)))
        update_ac_ui_status()
        ser.write(tx_data)
    elif((msg[2] == 0xa1) and (msg[3] == 0x01)):
            print('change prop data')
            tx_data = [msg[0],msg[1],msg[2],msg[3]+128]  
            for i in range(76 - len(tx_data)):
                tx_data.append(0)

            tx_data[0] = g_pkt_version
            if(cmd[1] == 0x00):
                print('Recieved power on/off command =', cmd[2])
                g_power_on = cmd[2]
            elif(cmd[1] == 0x01):
                print('Recieved AC Temp =',cmd[2], cmd[3] )                        
                g_temp_dec = cmd[2]
                g_temp_float = cmd[3]
                g_ac_temp = g_temp_dec           
            elif(cmd[1] == 0x02):
                print('Recieved AC FAN Speed = ', cmd[2])                        
                g_fan_speed = cmd[2]
            elif(cmd[1] == 0x03):
                print('Recieved NANO-EG =', cmd[2])                        
                g_nano_eg = cmd[2]
            elif(cmd[1] == 0x04):
                print('Recieved AC Vertical Swing =', cmd[2])                        
                g_vert_swing = cmd[2]
            elif(cmd[1] == 0x05):
                print('Recieved AC Horizontal Swing =', cmd[2])
                g_hor_swing = cmd[2]
            elif(cmd[1] == 0x06):
                print('Recieved AC Mode Control =', cmd[2])
                g_ac_mode = cmd[2]
            elif(cmd[1] == 0x07):
                print('Recieved AC Sleep mode =', cmd[2])                        
                g_sleep_mode = cmd[2]
            elif(cmd[1] == 0x08):
                print('Recieved AC Power full Mode =',cmd[2])                        
                g_powerful_mode = cmd[2]
            elif(cmd[1] == 0x09):
                print('Recieved AC Display =', cmd[2])                        
                disp_ctrl = cmd[2]
            elif(cmd[1] == 0x0A):
                print('Recieved AC Evaporator Clean =', cmd[2])                      
                g_evap_clean = cmd[2]
            elif(cmd[1] == 0x0C):
                print('Recieved AC Eco Mode = ', cmd[2])                        
                g_eco_mode = cmd[2]
            elif(cmd[1] == 0x0D):
                print('Recieved AC Filter Calibertion')
                tx_data[5] = 1
                tx_data[6] = 1
            elif(cmd[1] == 0x12):
                print('Recieved Motion Sens on/off = ', cmd[2])                        
                g_modtion_sens = cmd[2]  
            elif(cmd[1] == 0x14): 
                print('Recieved Gen Mode =', cmd[2])
                g_gen_mode = cmd[2]
            elif(cmd[1] == 0x19):
                print('Recieved Convertible Mode =', cmd[2])
                g_convert_mode = cmd[2]
            print('len txdata{}',len(tx_data))
            y = 0
            for i in tx_data:
                y = (y + i)&0xFF     
            #   send_sum = (send_sum + j)
            tx_data.append(256-y)  

            update_ac_ui_status()
            print('property set resp created')
            print(tx_data)
            ser.write(tx_data)
    elif((msg[2] == 0xa2) and (msg[3] == 0x02)):
        print('Get Diagnostics ')
        #tx_data = [msg[0],msg[1],msg[2],msg[3]+128,0x00,60,177,28,178,0x0,179,0x0E,180,0x1,181,0x00,0x00,182,0x00,0x01,183,0x01,193,0x00,194,0x05,195,0x04,196,0x01,197,0x01,0x00,198,0x1D,199,0x01,0x10,200,0x02,201,0x01,0x10,202,0x20,225,0x0, 226,0x19,227,0x10,241,70,65,70,65, 242,66,67,68,69, 243, 71,72,73,74]
        tx_data = [msg[0],msg[1],msg[2],msg[3]+128,0x00,61,177,28,178,0x0,179,0x0E,180,0x1,181,0x00,0x00,182,0x00,0x01,183,0x01,193,0x00,194,0x05,195,0x04,196,0x01,197,0x01,0x00,198,0x1D,199,0x01,0x10,200,0x02,0x21,201,0x01,0x10,202,0x20,225,0x0, 226,0x19,227,0x10,241,70,65,70,65, 242,66,67,68,69, 243, 71,72,73,74]
        print('property set resp created={}', tx_data)    
        print('len of txdata = {}',len(tx_data))                
        for i in range(76 - len(tx_data)):
            tx_data.append(0)             
        z = 0
        tx_data[0] = g_pkt_version 
        print('tx_data final = {}', tx_data)
        for i in tx_data: 
            try:                   
                z = (z + i)&0xFF                     
            except:
                print('Invalid opertion')
        print('I am here1={}',tx_data)                                       
        tx_data.append(256-z) 
        update_ac_ui_status()
        print('property set resp created1={}', list(map(hex, tx_data)))
        ser.write(tx_data)  
        print("property response sent")                           
    elif((msg[2] == 0xa3) and (msg[3] == 0x02)):
        print('Recieved self diag notification, test status') 
        hamcu_resp = [msg[0], msg[1], msg[2], msg[3]+128]
        for i in range(76 - len(hamcu_resp)):
            hamcu_resp.append(0)                        
        chk_sum = 0
        hamcu_resp[0] = g_pkt_version 
        for i in hamcu_resp:
            chk_sum += i
        chk_sum = chk_sum & 0xFF
        hamcu_resp.append(256 - chk_sum) 
        update_ac_ui_status()
        ser.write(hamcu_resp) 
        print('Sent Self diag notification response...')

def serial_init(Port):
    ser.port = Port
    ser.baudrate = 9600
    ser.timeout=15
    ser.parity = serial.PARITY_EVEN
    ser.stopbits = serial.STOPBITS_ONE
    ser.bytesize = serial.EIGHTBITS 
    ser.open()           
    time.sleep(3)
    ser.reset_input_buffer()
    if ser.is_open:
        print('Serial Port Is open')

def rx_task(): 
    global g_port_val 
    serial_init(g_port_val)
    data = [0, 0]
    send_cmd(0, 1, data, False)
    msg = ser.read(77)        
    #print('recieved resp for Query ADP Version', msg)
    print('recieved resp for Query ADP Version', list(map(hex, msg)))
    #ser.reset_input_buffer()
    while(1): 
        # event.wait() 
        print('Inside rx_task')
        print('Waiting to read')
        #ser.reset_input_buffer()
        time.sleep(0.1)
        try:
            rx_msg = ser.read(4)
            print('rx_msg')
            print(list(map(hex, rx_msg)))
            if(rx_msg[0] == 1):
                process_input(rx_msg)
            else:
                print('reset_input buffer')
                ser.reset_input_buffer()
        except:
            print('No ICM DATA')                                  
       
                 
        #read_input_rx = input()  
        #print('read_rx_task', read_input_rx) 

def tx_task(): 
    while(1):
        print('Inside tx_task')                 
        time.sleep(10)

        

root = tk.Tk()

icon=PhotoImage(height=32, width=48)
icon.blank()

root.wm_iconphoto('True', icon)
#miraie_logo = PhotoImage(file='miraie.ico')

# Setting icon of master window
#root.iconphoto(False, miraie_logo)

root.option_add("*Font", "aerial 12")
g_hamcu_psn
info_text=f"Panasonic AC Simulator v{g_simulator_ver}"
root.title(info_text)

#COMPORT Configuration
port1_label = tk.Label(root, text="Comp Port")

# Create entry fields
port1 = tk.Entry(root)
port1.insert(0,"/dev/ttyUSB0")

g_power_on = 0x00
disp_ctrl = 0x00

# Create submit buttons
port1_button = tk.Button(root, text="Start", command=port1_entry)
port1_label.grid(row=comport_row, column=0, sticky="w",padx=5, pady=5)

port1_label.grid(row=comport_row, column=0,sticky="w", padx=2, pady=5)
port1.grid(row=comport_row, column=1, sticky="w",padx=2, pady=5)
port1_button.grid(row=comport_row, sticky="w", column=2, padx=2, pady=5)

# Create buttons
button1 = tk.Button(root, text="ON-BOARD", command=button1_clicked)
button2 = tk.Button(root, text="Power ON/OFF", command=button2_clicked)
button3 = tk.Button(root, text="Room Temp Simulate", command=button3_clicked)
button4 = tk.Button(root, text="Factory Reset", command=button4_clicked)

# Create entry labels
entry1_label = tk.Label(root, text="AC Temp (16 - 30)")
entry2_label = tk.Label(root, text="Fan Speed (0 - 6)")
entry3_label = tk.Label(root, text="Raw Command,Value")
entry4_label = tk.Label(root, text="Line Test PSN (Non-Matter)")
entry5_label = tk.Label(root, text="Line Test QRCode (Matter)")
entry6_label = tk.Label(root, text="PSN")

# Create entry fields
entry1 = tk.Entry(root)
entry1.delete(0, tk.END)
#entry1.insert(0,"24")
entry2 = tk.Entry(root)
#entry2.insert(0,"0")
entry2.delete(0, tk.END)
entry3 = tk.Entry(root)
entry3.insert(0,"0x12,0x01")
entry4 = tk.Entry(root)
entry4.insert(0,"ABCDEFGH123456789")
entry5 = tk.Entry(root)
entry5.insert(0,"MT:WI7U7Z6E00-ME34CW4P0OUYH0AO4T1S2QC25G8S2KGSK1WQ5T1O0")

#entry6 = tk.Entry(root)
#entry6.insert(0,"ABCDEFGH123456789")

# Create submit buttons
submit_button1 = tk.Button(root, text="Send", command=submit_entry1)
submit_button2 = tk.Button(root, text="Send", command=submit_entry2)
submit_button3 = tk.Button(root, text="Send", command=submit_entry3)
submit_button4 = tk.Button(root, text="Send", command=submit_entry4)
submit_button5 = tk.Button(root, text="Send", command=submit_entry5)
#submit_button6 = tk.Button(root, text="Send", command=submit_entry6)

# Create radio buttons
radio_var = tk.StringVar()

radio_button1 = tk.Radiobutton(root, text="Auto", variable=radio_var, value="Auto", command=on_radio_button_change)
radio_button2 = tk.Radiobutton(root, text="Cool", variable=radio_var, value="Cool", command=on_radio_button_change)
radio_button3 = tk.Radiobutton(root, text="Dry",  variable=radio_var, value="Dry",  command=on_radio_button_change)
radio_button4 = tk.Radiobutton(root, text="Fan",  variable=radio_var, value="Fan",  command=on_radio_button_change)
radio_button5 = tk.Radiobutton(root, text="Heat", variable=radio_var, value="Heat", command=on_radio_button_change)
radio_var.set("Auto")


# Grid layout
button1.grid(row=button_row, column=0, sticky="w",  padx=5, pady=5)
button2.grid(row=button_row, column=1, sticky="w",  padx=5, pady=5)
button3.grid(row=button_row, column=2, sticky="w",  padx=5, pady=5)
button4.grid(row=button_row, column=3, sticky="w",  padx=5, pady=5)

nanoe_var    = IntVar()
powerful_var = IntVar()
multicmd_var = IntVar()

Checkbutton(root, text="Nano-e/g",      command=nanoeg_checked,   variable=nanoe_var).grid(row=button_row+1, column=0, sticky="w")
Checkbutton(root, text="Powerful Mode", command=powerful_checked, variable=powerful_var).grid(row=button_row+1, column=1, sticky="w")
Checkbutton(root, text="Multi CMD",    command=multicmd_checked, variable=multicmd_var).grid(row=button_row+1, column=2, sticky="w")


entry1_label.grid(row=temp_row,   column=0, sticky="w", padx=5, pady=5)
entry2_label.grid(row=temp_row+1, column=0, sticky="w", padx=5, pady=5)
entry3_label.grid(row=temp_row+2, column=0, sticky="w", padx=5, pady=5)
entry4_label.grid(row=temp_row+3, column=0, sticky="w", padx=5, pady=5)
entry5_label.grid(row=temp_row+4, column=0, sticky="w", padx=5, pady=5)
#entry6_label.grid(row=temp_row+5, column=0, sticky="w", padx=5, pady=5)

entry1.grid(row=temp_row,   column=1, sticky="w", padx=5, pady=5)
entry2.grid(row=temp_row+1, column=1, sticky="w", padx=5, pady=5)
entry3.grid(row=temp_row+2, column=1, sticky="w", padx=5, pady=5)
entry4.grid(row=temp_row+3, column=1, sticky="w", padx=5, pady=5)
entry5.grid(row=temp_row+4, column=1, sticky="w", padx=5, pady=5)
#entry6.grid(row=temp_row+5, column=1, sticky="w", padx=5, pady=5)

submit_button1.grid(row=temp_row,   column=2, sticky="w", padx=5, pady=5)
submit_button2.grid(row=temp_row+1, column=2, sticky="w", padx=5, pady=5)
submit_button3.grid(row=temp_row+2, column=2, sticky="w", padx=5, pady=5)
submit_button4.grid(row=temp_row+3, column=2, sticky="w", padx=5, pady=5)
submit_button5.grid(row=temp_row+4, column=2, sticky="w", padx=5, pady=5)
#submit_button6.grid(row=temp_row+5, column=2, sticky="w", padx=5, pady=5)

# AC Mode label
label1 = tk.Label(root, text="AC Mode:")

# Place the labels on the window using grid layout
label1.grid(row=mode_row, sticky="w", column=0, padx=2, pady=5)

radio_button1.grid(row=mode_row, column=1, sticky="w", padx=2, pady=5)
radio_button2.grid(row=mode_row, column=2, sticky="w", padx=2, pady=5)
radio_button3.grid(row=mode_row, column=3, sticky="w", padx=2, pady=5)
radio_button4.grid(row=mode_row, column=4, sticky="w", padx=2, pady=5)
radio_button5.grid(row=mode_row, column=5, sticky="w", padx=2, pady=5)

txt_bg_color = "lightskyblue1"

# AC Status label
label2 = tk.Label(root, 
                  text="***************************************** AC STATUS *****************************************",
                  background = txt_bg_color
                )

label2.grid(row=status_row, column=0, columnspan = 6, sticky="w", padx=5, pady=5)

power_label = tk.Label(root, text="Power Status")
power_label.grid(row=status_row+1, column=0, sticky="w", padx=5, pady=5)
power_status = tk.Label(root, text="  ", background = txt_bg_color)
power_status.grid(row=status_row+1, column=1, sticky="w", padx=5, pady=5)

display_label = tk.Label(root, text="Display")
display_label.grid(row=status_row+1, column=2, sticky="w", padx=5, pady=5)
display_status = tk.Label(root, text="  ", background = txt_bg_color)
display_status.grid(row=status_row+1, column=3, sticky="w", padx=5, pady=5)

temp_label = tk.Label(root, text="AC Temp")
temp_label.grid(row=status_row+2, column=0, sticky="w", padx=5, pady=5)
temp_status = tk.Label(root, text="  " , background = txt_bg_color)
temp_status.grid(row=status_row+2, column=1, sticky="w", padx=5, pady=5)

roomtemp_label = tk.Label(root, text="Room Temp")
roomtemp_label.grid(row=status_row+2, column=2, sticky="w", padx=5, pady=5)
roomtemp_status = tk.Label(root, text="  " , background = txt_bg_color)
roomtemp_status.grid(row=status_row+2, column=3, sticky="w", padx=5, pady=5)

mode_label = tk.Label(root, text="Mode")
mode_label.grid(row=status_row+3, column=0, sticky="w", padx=5, pady=5)
mode_status = tk.Label(root, text="  ",  background = txt_bg_color)
mode_status.grid(row=status_row+3, column=1, sticky="w", padx=5, pady=5)

fan_label = tk.Label(root, text="Fan Speed")
fan_label.grid(row=status_row+3, column=2, sticky="w", padx=5, pady=5)
fan_status = tk.Label(root, text="  ", background = txt_bg_color)
fan_status.grid(row=status_row+3, column=3, sticky="w", padx=5, pady=5)

nanoeg1_label = tk.Label(root, text="Nano E/G")
nanoeg1_label.grid(row=status_row+4, column=0, sticky="w", padx=5, pady=5)
nanoeg1_status = tk.Label(root, text="  ", background = txt_bg_color)
nanoeg1_status.grid(row=status_row+4, column=1, sticky="w", padx=5, pady=5)

pwrful_label = tk.Label(root, text="Powerful Mode")
pwrful_label.grid(row=status_row+4, column=2, sticky="w", padx=5, pady=5)
pwrful_status = tk.Label(root, text="  " , background = txt_bg_color)
pwrful_status.grid(row=status_row+4, column=3, sticky="w", padx=5, pady=5)

psn_label = tk.Label(root, text="PSN")
psn_label.grid(row=status_row+5, column=0, sticky="w", padx=5, pady=5)
psn_status = tk.Label(root, text="  " , background = txt_bg_color)
psn_status.grid(row=status_row+5, column=1, sticky="w", padx=5, pady=5)

update_ac_ui_status()

root.mainloop()
