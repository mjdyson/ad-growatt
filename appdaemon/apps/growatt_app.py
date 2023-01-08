import hassapi as hass
import growattServer
import time

class AD_Growatt(hass.Hass):

    def initialize(self):
        self.listen_state(self.get_charge_settings, "input_button.adgw_get_charge_settings_button")
        self.listen_state(self.set_charge_settings, "input_button.adgw_set_charge_settings_button")
        self.listen_state(self.reset_time, "input_button.adgw_reset_sensors")
        self.listen_state(self.get_device_ids, "input_button.adgw_get_device_ids_button")

    def get_device_ids(self, entity, attribute, old, new, kwargs):
        un = self.args["growatt_username"]
        pwd = self.args["growatt_password"]

        api = growattServer.GrowattApi(True) #get an instance of the api, using a random string as the ID
        session = api.login(un, pwd) #login and return a session

        plant_list = api.plant_list(session['user']['id'])
        plant = plant_list['data'][0] #This is an array - we just take the first - would need a for-loop for more systems
        plant_id = plant['plantId']
        plant_info = api.plant_info(plant_id)

        self.entity_list = []

        i = 0
        while i < len(plant_info['deviceList']):
            device = plant_info['deviceList'][i]
            device_sn = device['deviceSn']
            self.entity_list.append(device_sn)
            i += 1

        #device = plant_info['deviceList'][0] #This is an array - we just take the first - would need a for-loop for more systems
        #device_sn = device['deviceSn']
        self.call_service("input_select/set_options", entity_id="input_select.adgw_devices", options= self.entity_list)

    def get_charge_settings(self, entity, attribute, old, new, kwargs):
        #Args are pulled in from the apps.yaml file.
        #It's good practice to have those values stored in the secrets file
        un = self.args["growatt_username"]
        pwd = self.args["growatt_password"]

        api = growattServer.GrowattApi(True) #get an instance of the api, using a random string as the ID
        session = api.login(un, pwd) #login and return a session

        #Device ID from the input_select
        device_sn = self.get_state("input_select.adgw_devices")

        #If device_sn has not been created, get the first device in the plant
        #I dont like that this is repeated code, it works though will refactor later
        if device_sn == "---":
            plant_list = api.plant_list(session['user']['id'])
            plant = plant_list['data'][0] #This is an array - we just take the first - would need a for-loop for more systems
            plant_id = plant['plantId']
            plant_info = api.plant_info(plant_id)
            device = plant_info['deviceList'][0]
            device_sn = device['deviceSn']
        
        #Query the server using the api
        response = api.get_mix_inverter_settings(device_sn)

        #Create new sensors in HA and populate them with the values we've just received from the server.
        self.set_state("sensor.template_adgw_battery_first_time_slot_1_start", state = response['obj']['mixBean']['forcedChargeTimeStart1'])
        self.set_state("sensor.template_adgw_battery_first_time_slot_1_end", state = response['obj']['mixBean']['forcedChargeTimeStop1'])
        self.set_state("sensor.template_adgw_battery_first_time_slot_1_enabled", state = response['obj']['mixBean']['forcedChargeStopSwitch1'])
        self.set_state("sensor.template_adgw_battery_first_charge_stopped_soc", state = response['obj']['mixBean']['wchargeSOCLowLimit2'])
        self.set_state("sensor.template_adgw_battery_first_ac_charge_enabled", state = response['obj']['mixBean']['acChargeEnable'])

    def set_charge_settings(self, entity, attribute, old, new, kwargs):
        un = self.args["growatt_username"]
        pwd = self.args["growatt_password"]

        api = growattServer.GrowattApi(True) #get an instance of the api
        session = api.login(un, pwd) #login and return a session

        #Device ID from the input_select
        device_sn = self.get_state("input_select.adgw_devices")

        #If device_sn has not been created, get the first device in the plant
        #I dont like that this is repeated code, it works though will refactor later
        if device_sn == "---":
            plant_list = api.plant_list(session['user']['id'])
            plant = plant_list['data'][0] #This is an array - we just take the first - would need a for-loop for more systems
            plant_id = plant['plantId']
            plant_info = api.plant_info(plant_id)
            device = plant_info['deviceList'][0]
            device_sn = device['deviceSn']

        # Read the values required from HA and put them into variables
        start_timestamp = self.parse_time(self.get_state("input_datetime.adgw_battery_first_time_slot_1_start"))
        end_timestamp = self.parse_time(self.get_state("input_datetime.adgw_battery_first_time_slot_1_end"))
        charge_final_soc = self.get_state("input_select.adgw_battery_charge_max_soc")

        # Convert on/off to 1/0
        ac_charge_on = convert_on_off(self.get_state("input_boolean.adgw_ac_charge_on"))
        battery_first_time_slot_1_enabled = convert_on_off(self.get_state("input_boolean.adgw_battery_first_time_slot_1_enabled"))
        #self.log(battery_first_time_slot_1_enabled)
        #self.log(ac_charge_on)

        # Create dictionary of settings to apply through the api call. The order of these elements is important.
        schedule_settings = ["100", #Charging power %
                                charge_final_soc.replace("%", ""), #Stop charging SoC %
                                ac_charge_on,   #Allow AC charging (1 = Enabled)
                                start_timestamp.hour, start_timestamp.minute, #Schedule 1 - Start time
                                end_timestamp.hour, end_timestamp.minute, #Schedule 1 - End time
                                battery_first_time_slot_1_enabled,        #Schedule 1 - Enabled/Disabled (1 = Enabled)
                                "00", "00", #Schedule 2 - Start time
                                "00", "00", #Schedule 2 - End time
                                "0",        #Schedule 2 - Enabled/Disabled (0 = Disabled)
                                "00", "00", #Schedule 3 - Start time
                                "00", "00", #Schedule 3 - End time
                                "0"]        #Schedule 3 - Enabled/Disabled (0 = Disabled)

        # The api call - specifically for the mix inverter. Some other op will need to be applied if you dont have a mix inverter (replace 'mix_ac_charge_time_period')
        response = api.update_mix_inverter_setting(device_sn, 'mix_ac_charge_time_period', schedule_settings)

    def reset_time(self, entity, attribute, old, new, kwargs):
        #This section is just for testing and can be deleted if required. 
        #It is a script that clears the values stored inside the sensors we create
        #It allows us to test whether new data is properly being pulled from the server.
        self.set_state("sensor.template_adgw_battery_first_time_slot_1_start", state = "0")
        self.set_state("sensor.template_adgw_battery_first_time_slot_1_end", state = "0")
        self.set_state("sensor.template_adgw_battery_first_charge_stopped_soc", state = "0")
        self.set_state("sensor.template_adgw_battery_first_ac_charge_enabled", state = "0")
        self.set_state("sensor.template_adgw_battery_first_time_slot_1_enabled", state = "0")

def convert_on_off(value):
    # Function to convert on/off to 1/0
    if value == "on":
        return "1"
    else:
        return "0"