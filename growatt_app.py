import hassapi as hass
import growattServer

class AD_Growatt(hass.Hass):

    def initialize(self):
        self.listen_state(self.get_charge_settings, "input_button.house_battery_get_charge_settings_button")
        self.listen_state(self.set_charge_settings, "input_button.house_battery_set_charge_settings_button")
        self.listen_state(self.reset_time, "input_button.reset_time")

    def get_charge_settings(self, entity, attribute, old, new, kwargs):
        #Args are pulled in from the apps.yaml file.
        #It's good practice to have those values stored in the secrets file
        un = self.args["growatt_username"]
        pwd = self.args["growatt_password"]

        api = growattServer.GrowattApi(True) #get an instance of the api, using a random string as the ID
        session = api.login(un, pwd) #login and return a session

        plant_list = api.plant_list(session['user']['id'])
        plant = plant_list['data'][0] #This is an array - we just take the first - would need a for-loop for more systems
        plant_id = plant['plantId']
        plant_info = api.plant_info(plant_id)
        device = plant_info['deviceList'][0] #This is an array - we just take the first - would need a for-loop for more systems
        device_sn = device['deviceSn']

        #Query the server using the api
        response = api.get_mix_inverter_settings(device_sn)

        #Create new sensors in HA and populate them with the values we've just received from the server.
        self.set_state("sensor.battery_first_time_slot_1_start", state = response['obj']['mixBean']['forcedChargeTimeStart1'], attributes = {"friendly_name": "Charge Time 1 Start"})
        self.set_state("sensor.battery_first_time_slot_1_stop", state = response['obj']['mixBean']['forcedChargeTimeStop1'], attributes = {"friendly_name": "Charge Time 1 Stop"})
        self.set_state("sensor.battery_first_time_slot_1_enabled", state = response['obj']['mixBean']['forcedChargeStopSwitch1'], attributes = {"friendly_name": "Charge Time 1 Enabled"})
        self.set_state("sensor.battery_first_charge_stopped_soc", state = response['obj']['mixBean']['wchargeSOCLowLimit2'], attributes = {"friendly_name": "Charge SoC Max"})
        self.set_state("sensor.battery_first_ac_charge_enabled", state = response['obj']['mixBean']['acChargeEnable'], attributes = {"friendly_name": "Grid Charge Enabled"})

    def set_charge_settings(self, entity, attribute, old, new, kwargs):
        un = self.args["growatt_username"]
        pwd = self.args["growatt_password"]

        api = growattServer.GrowattApi(True) #get an instance of the api
        session = api.login(un, pwd) #login and return a session

        plant_list = api.plant_list(session['user']['id'])
        plant = plant_list['data'][0] #This is an array - we just take the first - would need a for-loop for more systems
        plant_id = plant['plantId']
        plant_info = api.plant_info(plant_id)
        device = plant_info['deviceList'][0] #This is an array - we just take the first - would need a for-loop for more systems
        device_sn = device['deviceSn']

        # Read the values required from HA and put them into variables
        start_timestamp = self.parse_time(self.get_state("input_datetime.growatt_start_time"))
        end_timestamp = self.parse_time(self.get_state("input_datetime.growatt_end_time"))
        charge_final_soc = self.get_state("input_select.growatt_charge_final_soc")

        # Convert on/off to 1/0
        if self.get_state("input_boolean.growatt_force_charge_on") == "on":
            force_charge_on = 1
        else:
            force_charge_on = 0

        # Create dictionary of settings to apply through the api call. The order of these elements is important.
        schedule_settings = ["100", #Charging power %
                                charge_final_soc.replace("%", ""), #Stop charging SoC %
                                force_charge_on,   #Allow AC charging (1 = Enabled)
                                start_timestamp.hour, start_timestamp.minute, #Schedule 1 - Start time
                                end_timestamp.hour, end_timestamp.minute, #Schedule 1 - End time
                                force_charge_on,        #Schedule 1 - Enabled/Disabled (1 = Enabled)
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
        self.set_state("sensor.battery_first_time_slot_1_start", state = "0", attributes = {"friendly_name": "Charge Time 1 Start"})
        self.set_state("sensor.battery_first_time_slot_1_stop", state = "0", attributes = {"friendly_name": "Charge Time 2 Stop"})
        self.set_state("sensor.battery_first_charge_stopped_soc", state = "0", attributes = {"friendly_name": "Charge SoC Max"})
        self.set_state("sensor.battery_first_ac_charge_enabled", state = "0", attributes = {"friendly_name": "Grid Charge Enabled"})
