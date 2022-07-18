import asyncio
import logging
from homeassistant.const import CONF_ICON, CONF_SERVICE_DATA
from homeassistant.components.switch import SwitchEntity
from .const import DOMAIN, ENL_OP_CODES, DATA_STATE_ON, DATA_STATE_OFF, SWITCH_POWER, CONF_ENSURE_ON, TYPE_SWITCH
from pychonet.lib.epc import EPC_CODE
from pychonet.lib.eojx import EOJX_CLASS

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass, config, async_add_entities, discovery_info=None):
    entities = []
    for entity in hass.data[DOMAIN][config.entry_id]:
        eojgc = entity['instance']['eojgc']
        eojcc = entity['instance']['eojcc']
        # configure switch entities by looking up full ENL_OP_CODE dict
        for op_code in list(entity['echonetlite']._update_flags_full_list):
            if eojgc in ENL_OP_CODES.keys():
                if eojcc in ENL_OP_CODES[eojgc].keys():
                    if op_code in ENL_OP_CODES[eojgc][eojcc].keys():
                        if TYPE_SWITCH in ENL_OP_CODES[eojgc][eojcc][op_code].keys():
                            entities.append(
                                EchonetSwitch(
                                   hass,
                                   entity['echonetlite'],
                                   config,
                                   op_code,
                                   ENL_OP_CODES[eojgc][eojcc][op_code],
                                   config.title
                                )
                            )
    async_add_entities(entities, True)

class EchonetSwitch(SwitchEntity):
    def __init__(self, hass, connector, config, code, options, name=None):
        """Initialize the switch."""
        self._connector = connector
        self._config = config
        self._code = code
        self._options = options
        self._attr_is_on = self._connector._update_data[self._code] == DATA_STATE_ON
        self._attr_name = f"{config.title} {EPC_CODE[self._connector._eojgc][self._connector._eojcc][self._code]}"
        self._attr_icon = options[CONF_ICON]
        self._uid = f'{self._connector._uid}-{self._code}'
        self._device_name = name

    @property
    def unique_id(self):
        """Return a unique ID."""
        return self._uid

    @property
    def icon(self):
        """Icon to use in the frontend, if any."""
        return self._attr_icon

    @property
    def device_info(self):
        return {
            "identifiers": {(
                DOMAIN,
                self._connector._uid,
                self._connector._instance._eojgc,
                self._connector._instance._eojcc,
                self._connector._instance._eojci
            )},
            "name": self._device_name,
            "manufacturer": self._connector._manufacturer,
            "model": EOJX_CLASS[self._connector._instance._eojgc][self._connector._instance._eojcc]
        }

    async def async_turn_on(self, **kwargs) -> None:
        """Turn switch on."""
        main_sw_code = None
        # Check ensure turn on switch.
        # For some devices this ensures the main switch is switched on firs
        if (CONF_ENSURE_ON in self._options):
            main_sw_code = self._options[CONF_ENSURE_ON]
        # Turn on the specified switch
        if main_sw_code is not None and self._connector._update_data[main_sw_code] != DATA_STATE_ON:
            if await self._connector._instance.setMessage(main_sw_code, SWITCH_POWER[DATA_STATE_ON]):
                self._connector._update_data[main_sw_code] = DATA_STATE_ON
                # Wait for it to be reflected on the device
                await asyncio.sleep(3)

        if main_sw_code is None or self._connector._update_data[main_sw_code] == DATA_STATE_ON:
            if await self._connector._instance.setMessage(self._code, self._options[CONF_SERVICE_DATA][DATA_STATE_ON]):
                self._connector._update_data[self._code] = DATA_STATE_ON
                self._attr_is_on = True
                self.async_write_ha_state()

    async def async_turn_off(self, **kwargs) -> None:
        """Turn switch off."""
        if await self._connector._instance.setMessage(self._code, self._options[CONF_SERVICE_DATA][DATA_STATE_OFF]):
            self._connector._update_data[self._code] = DATA_STATE_OFF
            self._attr_is_on = False
            self.async_write_ha_state()

    async def async_update(self):
        """Retrieve latest state."""
        await self._connector.async_update()
        self._attr_is_on = self._connector._update_data[self._code] == DATA_STATE_ON
