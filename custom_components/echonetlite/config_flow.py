"""Config flow for echonetlite integration."""
from __future__ import annotations

import logging
import asyncio
from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import HomeAssistant, callback
from homeassistant.data_entry_flow import FlowResult
from homeassistant.exceptions import HomeAssistantError
from homeassistant.data_entry_flow import AbortFlow
from homeassistant.util import Throttle
import homeassistant.helpers.config_validation as cv
from pychonet.HomeAirConditioner import ENL_FANSPEED, ENL_AIR_VERT, ENL_AIR_HORZ
from pychonet.lib.const import GET, SETC, ENL_SETMAP, ENL_GETMAP, ENL_UID, ENL_MANUFACTURER
from aioudp import UDPServer
from pychonet import Factory
from pychonet import ECHONETAPIClient
from pychonet import HomeAirConditioner
from pychonet import EchonetInstance
from .const import DOMAIN, USER_OPTIONS


_LOGGER = logging.getLogger(__name__)

# TODO adjust the data schema to the data that you need
STEP_USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Required("host"): str,
        vol.Required("title"): str,
    }
)

async def validate_input(hass: HomeAssistant,  user_input: dict[str, Any]) -> dict[str, Any]:
    """Validate the user input allows us to connect."""
    _LOGGER.debug(f"IP address is {user_input['host']}")
    host = user_input['host']
    server = None
    if DOMAIN in hass.data: # maybe set up by config entry?
        _LOGGER.debug(f"{hass.data[DOMAIN]} has already been setup..")
        server = hass.data[DOMAIN]['api']
    else:
        udp = UDPServer()
        loop = asyncio.get_event_loop()
        udp.run("0.0.0.0",3610, loop=loop)
        server = ECHONETAPIClient(server=udp,loop=loop)
    
    instance_list = []
    _LOGGER.debug(f"Beginning ECHONET node discovery")
    await server.discover(host)
    
    # Timeout after 3 seconds
    for x in range(0,300):
        await asyncio.sleep(0.01)
        if 'discovered' in list(server._state[host]):
             _LOGGER.debug(f"ECHONET Node Discovery Successful!")
             break
    state = server._state[host]
    for eojgc in list(state['instances'].keys()):
        for eojcc in list(state['instances'][eojgc].keys()):
            for instance in list(state['instances'][eojgc][eojcc].keys()):
                  _LOGGER.debug(f"instance is {instance}")
                  await server.getAllPropertyMaps(host, eojgc, eojcc, instance)
                  _LOGGER.debug(f"{host} - ECHONET Instance {eojgc}-{eojcc}-{instance} map attributes discovered!")
                  getmap = state['instances'][eojgc][eojcc][instance][ENL_GETMAP]
                  setmap = state['instances'][eojgc][eojcc][instance][ENL_SETMAP]
                  
                  await server.getIdentificationInformation(host, eojgc, eojcc, instance)
                  uid = state['instances'][eojgc][eojcc][instance][ENL_UID]
                  manufacturer = 'Mitsubishi' #state['instances'][eojgc][eojcc][instance][ENL_MANUFACTURER]
                  _LOGGER.debug(f"{host} - ECHONET Instance {eojgc}-{eojcc}-{instance} Identification number discovered!")
                  instance_list.append({"host":host,"eojgc":eojgc,"eojcc":eojcc,"eojci":instance,"getmap":getmap,"setmap":setmap,"uid":uid,"manufacturer":manufacturer})
    return instance_list

class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for echonetlite."""
    host = None
    title = None
    discover_task = None
    instance_list = None
    instances = None
    VERSION = 1
            
    async def async_step_user(self, user_input: dict[str, Any] | None = None) -> FlowResult:
        errors = {}
        """Handle the initial step."""
        if user_input is None:
            return self.async_show_form(
                step_id="user", data_schema=STEP_USER_DATA_SCHEMA
            )
        try:
            self.instance_list = await validate_input(self.hass, user_input)
            _LOGGER.debug("Node detected")
        except CannotConnect:
            errors["base"] = "cannot_connect"
        except Exception:  # pylint: disable=broad-except
            _LOGGER.exception("Unexpected exception")
            errors["base"] = "unknown"
        else:
            self.host = user_input["host"]
            self.title = user_input["title"]
            return await self.async_step_finish(user_input)
            
        return self.async_show_form(
            step_id="user", data_schema=STEP_USER_DATA_SCHEMA, errors=errors
        )
    
    async def async_step_finish(self, user_input=None):
        return self.async_create_entry(title=self.title, data={"instances": self.instance_list})

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        return OptionsFlowHandler(config_entry)

class CannotConnect(HomeAssistantError):
    """Error to indicate we cannot connect."""

class OptionsFlowHandler(config_entries.OptionsFlow):
    def __init__(self, config):
        self._config_entry = config
        
    async def async_step_init(self, user_input=None):
        """Manage the options."""
        data_schema_structure = {}
        
        # Handle HVAC User configurable options
        for instance in self._config_entry.data["instances"]:
           if instance['eojgc'] == 0x01 and instance['eojcc'] == 0x30:
                for option in list(USER_OPTIONS.keys()):
                    if option in instance['setmap']:
                       data_schema_structure.update({vol.Optional(
                           USER_OPTIONS[option]['option'],
                           default=self._config_entry.options.get(USER_OPTIONS[option]['option']) if self._config_entry.options.get(USER_OPTIONS[option]['option']) is not None else [] ,
                        ):cv.multi_select(USER_OPTIONS[option]['option_list'])})
               
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)
        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(data_schema_structure),
        )
