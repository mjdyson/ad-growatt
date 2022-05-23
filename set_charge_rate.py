import growattServer
import hassapi as hass

class HouseBatteryCharge(hass.Hass):

  def initialize(self):

    self.listen_state(self.set_charge_rate, "input_button.house_battery_set_charge_rate_button")

  def set_charge_rate(self, entity, attribute, old, new, kwargs):

    self.username = "your_username"
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
    ## input_datetime... are helpers in HA that the code reads from
    self.start_timestamp = self.parse_time(self.get_state("input_datetime.growatt_start_time"))
    self.end_timestamp = self.parse_time(self.get_state("input_datetime.growatt_end_time"))
    self.charge_final_soc = self.get_state("input_select.growatt_charge_final_soc")

    ## input_boolean... is another helper that is set on an HA dashboard
    if self.get_state("input_boolean.growatt_force_charge_on") == "on":
      self.force_charge_on = 1
    else:
      self.force_charge_on = 0

    self.schedule_settings = ["100", #Charging power %
                              self.charge_final_soc.replace("%", ""), #Stop charging SoC %
                              self.force_charge_on,   #Allow AC charging (1 = Enabled)
                              self.start_timestamp.hour, self.start_timestamp.minute, #Schedule 1 - Start time
                              self.end_timestamp.hour, self.end_timestamp.minute, #Schedule 1 - End time
                              self.force_charge_on,        #Schedule 1 - Enabled/Disabled (1 = Enabled)
                              "00", "00", #Schedule 2 - Start time
                              "00", "00", #Schedule 2 - End time
                              "0",        #Schedule 2 - Enabled/Disabled (0 = Disabled)
                              "00", "00", #Schedule 3 - Start time
                              "00", "00", #Schedule 3 - End time
                              "0"]        #Schedule 3 - Enabled/Disabled (0 = Disabled)

    print(self.schedule_settings)
    self.response = self.api.update_mix_inverter_setting(self.device_sn, 'mix_ac_charge_time_period', self.schedule_settings)
    
    lighting = self.get_app("get_discharge_rate")
    lighting.get_inverter_settings