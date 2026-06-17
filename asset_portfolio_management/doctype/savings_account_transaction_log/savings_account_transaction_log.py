# -*- coding: utf-8 -*-
# Copyright (c) 2026, Antigravity and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.utils import flt

class SavingsAccountTransactionLog(Document):
	def on_submit(self):
		update_parent_savings_asset(self.asset)

	def on_cancel(self):
		update_parent_savings_asset(self.asset)


def update_parent_savings_asset(asset_name):
	asset = frappe.get_doc("Asset Portfolio", asset_name)

	# Fetch all submitted transaction logs
	txs = frappe.get_all("Savings Account Transaction Log",
		filters={"asset": asset_name, "docstatus": 1},
		fields=["transaction_type", "amount"]
	)

	deposits = 0.0
	withdrawals = 0.0
	interest_credits = 0.0

	for tx in txs:
		amt = flt(tx.amount)
		if tx.transaction_type == "Deposit":
			deposits += amt
		elif tx.transaction_type == "Withdrawal":
			withdrawals += amt
		elif tx.transaction_type == "Interest Credit":
			interest_credits += amt

	asset.current_value = (deposits + interest_credits) - withdrawals
	# Net cash investment in the account
	asset.investment_value = max(0.0, deposits - withdrawals)
	asset.save()
