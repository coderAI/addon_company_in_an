# -*- coding: utf-8 -*-
# -------------------------------Design by Hai--------------------------------#
from odoo import api, fields, models, SUPERUSER_ID

class ExternalCountryState(models.AbstractModel):
    _description = 'Get Country and State API'
    _name = 'external.country.state'

    @api.model
    def get_country(self):
        res = {'"code"': 0, '"msg"': '', '"data"': []}
        ResCountry = self.env['res.country']
        country_ids = ResCountry.search([])
        data = []
        for country in country_ids:
            if country.code:
                data.append({'\"' + country.code + '\"': '\"' + country.name + '\"'})
        res.update({'"code"': 1, '"msg"': '"Successfully"', '"data"': data})
        return res

    @api.model
    def get_state(self, code):
        res = {'"code"': 0, '"msg"': '', '"data"': []}
        ResCountry = self.env['res.country']
        ResCountryState = self.env['res.country.state']
        data = []
        # Check data
        if not code:
            res.update({'"msg"': '"Country Code could be not empty"'})
            return res
        country_id = ResCountry.search([('code', '=', code)], limit=1)
        if not country_id:
            res.update({'"msg"': '"Country not found."'})
            return res
        state_ids = ResCountryState.search([('country_id', '=', country_id.id)])
        for state in state_ids:
            if state.code:
                data.append({'\"' + state.code + '\"': '\"' + state.name + '\"'})
        res.update({'"code"': 1, '"msg"': '"Successfully"', '"data"': data})
        return res


