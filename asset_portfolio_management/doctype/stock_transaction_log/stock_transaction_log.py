# -*- coding: utf-8 -*-
# Copyright (c) 2026, Antigravity and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.utils import flt

class StockTransactionLog(Document):
	def validate(self):
		self.calculate_total_amount()
		self.calculate_realized_gain_loss()

	def on_submit(self):
		update_parent_asset(self.asset)

	def on_cancel(self):
		update_parent_asset(self.asset)

	def calculate_total_amount(self):
		qty = flt(self.quantity)
		price = flt(self.price)
		brokerage = flt(self.brokerage)
		taxes = flt(self.taxes_fees)

		if self.transaction_type == "Buy":
			self.total_amount = (qty * price) + brokerage + taxes
		else:
			self.total_amount = (qty * price) - brokerage - taxes

	def calculate_realized_gain_loss(self):
		if self.transaction_type != "Sell":
			self.realized_gain_loss = 0.0
			return

		# Fetch all submitted transactions prior to this one for this stock
		# We exclude the current record since it's not submitted/committed yet
		txs = frappe.get_all("Stock Transaction Log",
			filters={
				"asset": self.asset,
				"docstatus": 1,
				"name": ["!=", self.name]
			},
			fields=["transaction_type", "quantity", "total_amount"],
			order_by="transaction_date asc, creation asc"
		)

		total_qty = 0
		total_cost = 0.0
		avg_price = 0.0

		for tx in txs:
			if tx.transaction_type == "Buy":
				total_qty += flt(tx.quantity)
				total_cost += flt(tx.total_amount)
				avg_price = total_cost / total_qty if total_qty > 0 else 0.0
			elif tx.transaction_type == "Sell":
				total_qty -= flt(tx.quantity)
				total_cost = total_qty * avg_price

		# Net realized gain/loss = Net Sale Value - Cost Basis of Sold Shares
		self.realized_gain_loss = flt(self.total_amount) - (flt(self.quantity) * avg_price)


def update_parent_asset(asset_name):
	asset = frappe.get_doc("Asset Portfolio", asset_name)

	# Fetch all submitted transactions
	txs = frappe.get_all("Stock Transaction Log",
		filters={"asset": asset_name, "docstatus": 1},
		fields=["transaction_type", "quantity", "total_amount"],
		order_by="transaction_date asc, creation asc"
	)

	total_qty = 0
	total_cost = 0.0
	avg_price = 0.0

	for tx in txs:
		if tx.transaction_type == "Buy":
			total_qty += flt(tx.quantity)
			total_cost += flt(tx.total_amount)
			avg_price = total_cost / total_qty if total_qty > 0 else 0.0
		elif tx.transaction_type == "Sell":
			total_qty -= flt(tx.quantity)
			total_cost = total_qty * avg_price

	asset.quantity_held = total_qty
	asset.avg_purchase_price = avg_price
	asset.investment_value = total_qty * avg_price
	asset.current_value = total_qty * flt(asset.current_market_price)
	asset.save()
