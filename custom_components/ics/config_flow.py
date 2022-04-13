"""Provide the config flow."""
from homeassistant.core import callback
from homeassistant import config_entries
import voluptuous as vol
import logging
from .const import *

_LOGGER = logging.getLogger(__name__)


@config_entries.HANDLERS.register(DOMAIN)
class IcsFlowHandler(config_entries.ConfigFlow):
	"""Provide the initial setup."""

	CONNECTION_CLASS = config_entries.CONN_CLASS_LOCAL_POLL
	VERSION = 1

	def __init__(self):
		"""Provide the init function of the config flow."""
		# Called once the flow is started by the user
		self._errors = {}

	# will be called by sending the form, until configuration is done
	async def async_step_user(self, user_input=None):   # pylint: disable=unused-argument
		"""Provide the first page of the config flow."""
		self._errors = {}
		if user_input is not None:
			# there is user input, check and save if valid (see const.py)
			self._errors = await check_data(user_input, self.hass)
			if self._errors == {}:
				self.data = user_input
				return await self.async_step_finish()
		# no user input, or error. Show form
		return self.async_show_form(step_id="user", data_schema=vol.Schema(create_form(1, user_input, self.hass)), errors=self._errors)

	# will be called by sending the form, until configuration is done
	async def async_step_finish(self, user_input=None):   # pylint: disable=unused-argument
		"""Provide the second page of the config flow."""
		self._errors = {}
		if user_input is not None:
			# there is user input, check and save if valid (see const.py)
			self._errors = await check_data(user_input, self.hass)
			if self._errors == {}:
				user_input.update(self.data)
				return self.async_create_entry(title=user_input[CONF_NAME], data=user_input)
		# no user input, or error. Show form
		return self.async_show_form(step_id="finish", data_schema=vol.Schema(create_form(2, user_input, self.hass)), errors=self._errors)

	# TODO .. what is this good for?
	async def async_step_import(self, user_input):  # pylint: disable=unused-argument
		"""Import a config entry.

		Special type of import, we're not actually going to store any data.
		Instead, we're going to rely on the values that are in config file.
		"""
		if self._async_current_entries():
			return self.async_abort(reason="single_instance_allowed")

		return self.async_create_entry(title="configuration.yaml", data={})

	@staticmethod
	@callback
	def async_get_options_flow(config_entry):
		"""Call back to start the change flow."""
		return OptionsFlowHandler(config_entry)


class OptionsFlowHandler(config_entries.OptionsFlow):
	"""Change an entity via GUI."""

	def __init__(self, config_entry):
		"""Set initial parameter to grab them later on."""
		# store old entry for later
		self.data = {}
		self.data.update(config_entry.data.items())
		self.own_id = config_entry.data[CONF_ID]

	# will be called by sending the form, until configuration is done
	async def async_step_init(self, user_input=None):   # pylint: disable=unused-argument
		"""Call this as first page."""
		self._errors = {}
		if user_input is not None:
			# there is user input, check and save if valid (see const.py)
			self._errors = await check_data(user_input, self.hass, self.own_id)
			if self._errors == {}:
				self.data.update(user_input)
				return await self.async_step_finish()
		elif self.data is not None:
			# if we came straight from init
			user_input = self.data
		# no user input, or error. Show form
		return self.async_show_form(step_id="init", data_schema=vol.Schema(create_form(1, user_input, self.hass)), errors=self._errors)

	# will be called by sending the form, until configuration is done
	async def async_step_finish(self, user_input=None):   # pylint: disable=unused-argument
		"""Call this as second page."""
		self._errors = {}
		if user_input is not None:
			self.data.update(user_input)
			# there is user input, check and save if valid (see const.py)
			self._errors = await check_data(user_input, self.hass, self.own_id)
			if self._errors == {}:
				return self.async_create_entry(title=self.data[CONF_NAME], data=self.data)
		# no user input, or error. Show form
		return self.async_show_form(step_id="finish", data_schema=vol.Schema(create_form(2, self.data, self.hass)), errors=self._errors)
