# -*- coding: utf-8 -*-
# Copyright (c) 2026, Antigravity and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.utils import flt

class MutualFundTransactionLog(Document):
	def validate(self):
		self.calculate_total_amount()
		self.calculate_realized_gain_loss()

	def on_submit(self):
		update_parent_asset(self.asset)
		je_name = create_draft_journal_entry(self, frappe.get_doc("Asset Portfolio", self.asset))
		if je_name:
			self.db_set("journal_entry", je_name, update_modified=False)

	def on_cancel(self):
		update_parent_asset(self.asset)
		cancel_draft_journal_entry(self)

	def calculate_total_amount(self):
		units = flt(self.units)
		nav = flt(self.nav)
		stamp_duty = flt(self.stamp_duty)
		exit_load = flt(self.exit_load)

		if self.transaction_type == "Buy":
			self.total_amount = (units * nav) + stamp_duty
		else:
			self.total_amount = (units * nav) - exit_load

	def calculate_realized_gain_loss(self):
		if self.transaction_type != "Sell":
			self.avg_nav_at_transaction = 0.0
			self.gain_loss_per_unit = 0.0
			self.realized_gain_loss = 0.0
			return

		avg_nav = get_weighted_avg_nav(self.asset, exclude=self.name)

		# Per-NAV (per-unit) gain/loss booked for tracking, plus the total realized gain/loss
		self.avg_nav_at_transaction = avg_nav
		self.gain_loss_per_unit = flt(self.nav) - avg_nav
		self.realized_gain_loss = (self.gain_loss_per_unit * flt(self.units)) - flt(self.exit_load)


def get_weighted_avg_nav(asset_name, exclude=None):
	filters = {
		"asset": asset_name,
		"docstatus": 1,
	}
	if exclude:
		filters["name"] = ["!=", exclude]

	txs = frappe.get_all("Mutual Fund Transaction Log",
		filters=filters,
		fields=["transaction_type", "units", "total_amount"],
		order_by="transaction_date asc, creation asc"
	)

	total_units = 0.0
	total_cost = 0.0
	avg_nav = 0.0

	for tx in txs:
		if tx.transaction_type == "Buy":
			total_units += flt(tx.units)
			total_cost += flt(tx.total_amount)
			avg_nav = total_cost / total_units if total_units > 0 else 0.0
		elif tx.transaction_type == "Sell":
			total_units -= flt(tx.units)
			total_cost = total_units * avg_nav

	return avg_nav


def update_parent_asset(asset_name):
	asset = frappe.get_doc("Asset Portfolio", asset_name)

	txs = frappe.get_all("Mutual Fund Transaction Log",
		filters={"asset": asset_name, "docstatus": 1},
		fields=["transaction_type", "units", "total_amount"],
		order_by="transaction_date asc, creation asc"
	)

	total_units = 0.0
	total_cost = 0.0
	avg_nav = 0.0

	for tx in txs:
		if tx.transaction_type == "Buy":
			total_units += flt(tx.units)
			total_cost += flt(tx.total_amount)
			avg_nav = total_cost / total_units if total_units > 0 else 0.0
		elif tx.transaction_type == "Sell":
			total_units -= flt(tx.units)
			total_cost = total_units * avg_nav

	asset.units_held = total_units
	asset.avg_nav = avg_nav
	asset.investment_value = total_units * avg_nav
	asset.current_value = total_units * flt(asset.current_nav)
	asset.save()


def create_draft_journal_entry(tx, asset):
	"""Create (but do not submit) a Journal Entry mirroring this Buy/Sell in the
	Chart of Accounts. Requires Company, Investment Account and Settlement
	Account to be set on the Mutual Fund asset; silently skips (with a
	notification) otherwise so bookkeeping setup doesn't block the transaction.
	"""
	if not (asset.mf_company and asset.mf_investment_account and asset.mf_settlement_account):
		frappe.msgprint(
			"Journal Entry not created: set Company, Investment Account and Settlement Account "
			"on the Mutual Fund asset ({0}) to enable accounting postings.".format(asset.name),
			alert=True,
			indicator="orange",
		)
		return None

	units = flt(tx.units)
	total_amount = flt(tx.total_amount)
	remark_base = "{0} {1} units of {2} ({3}) @ NAV {4} - auto-created from Mutual Fund Transaction Log {5}".format(
		tx.transaction_type, units, asset.asset_name, asset.folio_number or asset.name, tx.nav, tx.name
	)

	accounts = []

	if tx.transaction_type == "Buy":
		accounts.append({
			"account": asset.mf_investment_account,
			"debit_in_account_currency": total_amount,
			"credit_in_account_currency": 0,
		})
		accounts.append({
			"account": asset.mf_settlement_account,
			"debit_in_account_currency": 0,
			"credit_in_account_currency": total_amount,
		})
	else:
		cost_basis = flt(tx.avg_nav_at_transaction) * units
		gain_loss = flt(tx.realized_gain_loss)

		if gain_loss and not asset.mf_gain_loss_account:
			frappe.msgprint(
				"Journal Entry not created: set a Realized Gain / Loss Account on the Mutual "
				"Fund asset ({0}) so this sell's P&L of {1} can be booked.".format(asset.name, gain_loss),
				alert=True,
				indicator="orange",
			)
			return None

		accounts.append({
			"account": asset.mf_settlement_account,
			"debit_in_account_currency": total_amount,
			"credit_in_account_currency": 0,
		})
		accounts.append({
			"account": asset.mf_investment_account,
			"debit_in_account_currency": 0,
			"credit_in_account_currency": cost_basis,
		})
		if gain_loss > 0:
			accounts.append({
				"account": asset.mf_gain_loss_account,
				"debit_in_account_currency": 0,
				"credit_in_account_currency": gain_loss,
			})
		elif gain_loss < 0:
			accounts.append({
				"account": asset.mf_gain_loss_account,
				"debit_in_account_currency": abs(gain_loss),
				"credit_in_account_currency": 0,
			})

	je = frappe.get_doc({
		"doctype": "Journal Entry",
		"voucher_type": "Journal Entry",
		"company": asset.mf_company,
		"posting_date": tx.transaction_date,
		"user_remark": remark_base,
		"accounts": accounts,
	}).insert(ignore_permissions=True)

	return je.name


def cancel_draft_journal_entry(tx):
	if not tx.journal_entry or not frappe.db.exists("Journal Entry", tx.journal_entry):
		return

	je_docstatus = frappe.db.get_value("Journal Entry", tx.journal_entry, "docstatus")
	if je_docstatus == 0:
		frappe.delete_doc("Journal Entry", tx.journal_entry, ignore_permissions=True, force=1)
		tx.db_set("journal_entry", None, update_modified=False)
	else:
		frappe.msgprint(
			"Linked Journal Entry {0} has already been submitted/cancelled in Accounts; "
			"please reverse it manually if needed.".format(tx.journal_entry),
			alert=True,
			indicator="orange",
		)
