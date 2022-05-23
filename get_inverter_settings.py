import growattServer
#import datetime
import hassapi as hass

class InverterSettings(hass.Hass):

  def initialize(self):

    self.listen_state(self.get_inverter_settings, "input_button.house_battery_get_discharge_rate_button")

  def get_inverter_settings(self, entity, attribute, old, new, kwargs):

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

    self.response = self.api.get_mix_inverter_settings(self.device_sn)

    ## The following lines write to HA. If memory serves me correctly, these are created new from within AD.
    self.set_state("sensor.battery_charge_time1_start", state = self.response['obj']['mixBean']['forcedChargeTimeStart1'], attributes = {"friendly_name": "Charge Time 1 Start"})
    self.set_state("sensor.battery_charge_time1_stop", state = self.response['obj']['mixBean']['forcedChargeTimeStop1'], attributes = {"friendly_name": "Charge Time 1 Stop"})
    self.set_state("sensor.battery_charge_time1_enabled", state = self.response['obj']['mixBean']['forcedChargeStopSwitch1'], attributes = {"friendly_name": "Charge Time 1 Enabled"})
    self.set_state("sensor.battery_charge_time2_start", state = self.response['obj']['mixBean']['forcedChargeTimeStart2'], attributes = {"friendly_name": "Charge Time 2 Start"})
    self.set_state("sensor.battery_charge_time2_stop", state = self.response['obj']['mixBean']['forcedChargeTimeStop2'], attributes = {"friendly_name": "Charge Time 2 Stop"})
    self.set_state("sensor.battery_charge_time2_enabled", state = self.response['obj']['mixBean']['forcedChargeStopSwitch2'], attributes = {"friendly_name": "Charge Time 2 Enabled"})
    self.set_state("sensor.battery_charge_soc_max", state = self.response['obj']['mixBean']['wchargeSOCLowLimit2'], attributes = {"friendly_name": "Charge SoC Max"})
    self.set_state("sensor.battery_charge_grid_enabled", state = self.response['obj']['mixBean']['acChargeEnable'], attributes = {"friendly_name": "Grid Charge Enabled"})