import growattServer
import hassapi as hass

class HouseBatteryDischarge(hass.Hass):

  def initialize(self):

    self.listen_state(self.set_discharge_rate, "input_button.house_battery_set_discharge_rate_button")
    #self.listen_state(self.GetDischargeRate, input_button.house_battery_get_discharge_rate_button)

  def set_discharge_rate(self, entity, attribute, old, new, kwargs):

    #pp = pprint.PrettyPrinter(indent=4)
    #Prompt user for username
    self.username = "your_username"
    #Prompt user to input password
    self.user_pass = "your_password"
    self.api = growattServer.GrowattApi()
    self.login_response = self.api.login(self.username, self.user_pass)
    self.plant_list = self.api.plant_list(self.login_response['user']['id'])

    #Simple logic to just get the first inverter from the first plant
    #Expand this using a for-loop to perform for more systems (see mix_example for more detail)
    self.plant = self.plant_list['data'][0] #This is an array - we just take the first - would need a for-loop for more systems
    self.plant_id = self.plant['plantId']
    self.plant_name = self.plant['plantName']
    self.plant_info = self.api.plant_info(self.plant_id)

    self.device = self.plant_info['deviceList'][0] #This is an array - we just take the first - would need a for-loop for more systems
    self.device_sn = self.device['deviceSn']
    self.device_type = self.device['deviceType']

    #Set inverter schedule (Uses the 'array' method which assumes all parameters are named param1....paramN)
    self.schedule_settings = ["100", #Discharging power %
                        "5", #Stop discharging SoC %
                        "00", "00", #Schedule 1 - Start time
                        "00", "00", #Schedule 1 - End time
                        "0",        #Schedule 1 - Enabled/Disabled (1 = Enabled)
                        "00", "00", #Schedule 2 - Start time
                        "00", "00", #Schedule 2 - End time
                        "0",        #Schedule 2 - Enabled/Disabled (0 = Disabled)
                        "00", "00", #Schedule 3 - Start time
                        "00", "00", #Schedule 3 - End time
                        "0"]        #Schedule 3 - Enabled/Disabled (0 = Disabled)
    self.response = self.api.update_mix_inverter_setting(self.device_sn, 'mix_ac_discharge_time_period', self.schedule_settings)