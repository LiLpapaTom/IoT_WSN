#Thomas Papaloukas, ICSD14155
import paho.mqtt.client as mqtt
import ssl
import os
import sys
import time
#For the plot/buttons/widgets
import matplotlib.pyplot as plt
from matplotlib.widgets import Button
from threading import Timer
from datetime import datetime

class IoTExample:
    def __init__(self):
        self.ax = None
        self._establish_mqtt_connection()
        self._prepare_graph_window()

    def _establish_mqtt_connection(self):
        print("Trying to connect to MQTT server...")

        self.client = mqtt.Client()
        self.client.on_connect = self._on_connect
        self.client.on_log = self._on_log
        self.client.on_message = self._on_message

        self.client.tls_set_context(ssl.SSLContext(ssl.PROTOCOL_TLSv1_2))
        self.client.username_pw_set('username','pwd') #Set name/password
        self.client.connect('domain', 8080) #Set domain, port
        #Smart plug 1
        self.client.subscribe('hscnl/hscnl02/state/ZWaveNode005_ElectricMeterWatts/state')
        self.client.subscribe('hscnl/hscnl02/command/ZWaveNode005_Switch/command')
        self.client.subscribe('hscnl/hscnl02/state/ZWaveNode005_Switch/state')
        #Smart plug 2
        self.client.subscribe('hscnl/hscnl02/state/ZWaveNode006_ElectricMeterWatts/state')
        self.client.subscribe('hscnl/hscnl02/command/ZWaveNode006_Switch/command')
        self.client.subscribe('hscnl/hscnl02/state/ZWaveNode006_Switch/state')

    def _prepare_graph_window(self):
        plt.rcParams['toolbar'] = 'None'
        self.ax = plt.subplot(111)
        #For smartplug 1
        self.dataX = []
        self.dataY = []
        #For smartplug 2
        self.dataX_2 = []
        self.dataY_2 = []

        self.first_ts = datetime.now()
        self.lineplot = self.ax.plot(self.dataX, self.dataY, linestyle='--', marker='o', color='b')
        self.lineplot_2 = self.ax.plot(self.dataX_2, self.dataY_2, linestyle='--', marker='o', color='g')
        self.ax.figure.canvas.mpl_connect('close_event', self.disconnect)
        self.finishing = False
        #smartplug 1 buttons
        axcut = plt.axes([0.0, 0.0, 0.1, 0.06])
        self.bcut = Button(axcut,'ON(S1)')
        axcut2 = plt.axes([0.1, 0.0, 0.1, 0.06])
        self.bcut2 = Button(axcut2, 'OFF(S1)')
        self.state_field = plt.text(3.5, 0.3, 'STATE (S1): -')
        self.bcut.on_clicked(self._button_on_clicked)
        self.bcut2.on_clicked(self._button_off_clicked)
        #smartplug 2 buttons
        axcut = plt.axes([0.2, 0.0, 0.1, 0.06])
        self.bcut_1 = Button(axcut,'ON(S2)')
        axcut2 = plt.axes([0.3, 0.0, 0.1, 0.06])
        self.bcut2_2 = Button(axcut2, 'OFF(S2)')
        self.state_field_2 = plt.text(3.5, 0.3, 'STATE (S2): -')
        self.bcut_1.on_clicked(self._button_on_clicked_2)
        self.bcut2_2.on_clicked(self._button_off_clicked_2)

        self._my_timer()

    def _refresh_plot(self):
        if len(self.dataX) > 0:
            self.ax.set_xlim(min(self.first_ts, min(self.dataX)), max(max(self.dataX), datetime.now()))
            self.ax.set_ylim(min(self.dataY) * 0.8, max(self.dataY) * 1.2)
        else:
            self.ax.set_xlim(self.first_ts, datetime.now())
        self.ax.relim()
        plt.draw()

    def _add_value_to_plot(self, value, smartplug):
        if smartplug == 1:
            self.dataX.append(datetime.now())
            self.dataY.append(value)
            self.lineplot = self.ax.plot(self.dataX, self.dataY, linestyle='--', marker='o', color='b')
            self.state_field.set_text('STATE (S1): ' + str(value))
        else:
            self.dataX_2.append(datetime.now())
            self.dataY_2.append(value)
            self.lineplot_2 = self.ax.plot(self.dataX_2, self.dataY_2, linestyle='--', marker='o', color='g')
            self.state_field_2.set_text('STATE: (S2)' + str(value))
        self._refresh_plot()

    def _my_timer(self):
        self._refresh_plot()
        if not self.finishing:
            Timer(1.0, self._my_timer).start()

    def start(self):
        if self.ax:
            self.client.loop_start()
            plt.show()
        else:
            self.client.loop_forever()

    #Call this method to disconnect from the broker
    def disconnect(self, args=None):
        self.client.disconnect() #disconnected

    def _on_connect(self, client, userdata, flags, rc):
        if rc == 0:
            print("Connected OK, returned code = ", rc)
        else:
            print("Bad connection returned code = ", rc)

    #This is the callback that will be called whenever a new msg is received
    def _on_message(self, client, userdata, msg):
        print(msg.topic+''+str(msg.payload))
        if msg.topic == 'hscnl/hscnl02/state/ZWaveNode005_ElectricMeterWatts/state':
            #print('Float payload for the plot:',float(msg.payload))
            self._add_value_to_plot(float(msg.payload), 1)
        elif msg.topic =='hscnl/hscnl02/state/ZWaveNode006_ElectricMeterWatts/state':
            self._add_value_to_plot(float(msg.payload), 2)

    def _on_log(self, client, userdata, level, buf):
        print('log: ', buf)

    def _button_on_clicked(self, event):
        self.client.publish('hscnl/hscnl02/sendcommand/ZWaveNode005_Switch','ON')

    def _button_off_clicked(self, event):
        self.client.publish('hscnl/hscnl02/sendcommand/ZWaveNode005_Switch','OFF')

    def _button_on_clicked_2(self, event):
        self.client.publish('hscnl/hscnl02/sendcommand/ZWaveNode006_Switch','ON')

    def _button_off_clicked_2(self, event):
        self.client.publish('hscnl/hscnl02/sendcommand/ZWaveNode006_Switch','OFF')

try:
    iot_example = IoTExample()
    iot_example.start()
except KeyboardInterrupt:
    print("Interrupted")
    try:
        iot_example.disconnect()
        sys.exit(0)
    except SystemExit:
        os._exit(0)
