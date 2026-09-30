# -*- coding: utf-8 -*-
# Copyright (c) 2026, Antigravity and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.utils import flt, getdate, today
from asset_portfolio_management.utils.xirr import calculate_asset_xirr

class AssetPortfolio(Document):
	def validate(self):
		self.calculate_totals()
		self.calculate_xirr_value()

	def calculate_totals(self):
		if self.asset_type == "Bond":
			self.interest_paid = sum(flt(d.interest_amount) for d in self.bond_interest_schedule if d.status == "Paid")
			self.interest_unpaid = sum(flt(d.interest_amount) for d in self.bond_interest_schedule if d.status == "Pending")
			self.principal_paid = sum(flt(d.amount) for d in self.bond_principal_schedule)
			self.principal_unpaid = flt(self.investment_value) - self.principal_paid
			self.current_value = self.principal_unpaid
			self.total_gain_loss = (self.current_value + self.interest_paid + self.principal_paid) - flt(self.investment_value)
		
		elif self.asset_type == "Fixed Deposit":
			self.fd_interest_paid = sum(flt(d.interest_amount) for d in self.fd_interest_schedule)
			self.fd_principal_paid = sum(flt(d.amount) for d in self.fd_principal_schedule)
			self.fd_principal_unpaid = flt(self.investment_value) - self.fd_principal_paid
			self.current_value = self.fd_principal_unpaid
			self.total_gain_loss = (self.current_value + self.fd_interest_paid + self.fd_principal_paid) - flt(self.investment_value)

		elif self.asset_type == "Stock":
			# Calculations are driven by Stock Transaction Logs, but let's sync fields here
			self.total_gain_loss = flt(self.current_value) - flt(self.investment_value)

		elif self.asset_type == "Mutual Fund":
			# Calculations are driven by Mutual Fund Transaction Logs, but let's sync fields here
			self.current_value = flt(self.units_held) * flt(self.current_nav)
			self.total_gain_loss = flt(self.current_value) - flt(self.investment_value)

		elif self.asset_type == "Savings Account":
			# Calculations are driven by Savings Account Transaction Logs
			self.total_gain_loss = flt(self.current_value) - flt(self.investment_value)

		else:
			# Generic fallback for PF, PPF, NPS or other assets
			self.total_gain_loss = flt(self.current_value) - flt(self.investment_value)

		if flt(self.investment_value) > 0:
			self.total_return_pct = (self.total_gain_loss / flt(self.investment_value)) * 100.0
		else:
			self.total_return_pct = 0.0

	def calculate_xirr_value(self):
		self.xirr = calculate_asset_xirr(self)
