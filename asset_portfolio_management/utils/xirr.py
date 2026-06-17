# -*- coding: utf-8 -*-
# Copyright (c) 2026, Antigravity and contributors
# For license information, please see license.txt

import datetime

def xirr(cash_flows):
	"""
	Calculates the Extended Internal Rate of Return (XIRR) using the Newton-Raphson method.
	cash_flows: List of tuples (date, amount), where:
		- date is a datetime.date object
		- amount is a float (negative for outflows/investments, positive for inflows/returns)
	Returns the XIRR rate as a percentage (e.g., 12.5 for 12.5%).
	"""
	# Group cash flows by date to avoid multiple flows on the same day
	grouped = {}
	for date, amount in cash_flows:
		if isinstance(date, str):
			try:
				date = datetime.datetime.strptime(date[:10], "%Y-%m-%d").date()
			except ValueError:
				continue
		elif isinstance(date, datetime.datetime):
			date = date.date()
		
		grouped[date] = grouped.get(date, 0.0) + float(amount)

	flows = sorted([(d, amt) for d, amt in grouped.items() if amt != 0.0], key=lambda x: x[0])

	if len(flows) < 2:
		return 0.0

	# Check signs: must have at least one positive and one negative cash flow
	has_positive = any(amt > 0 for _, amt in flows)
	has_negative = any(amt < 0 for _, amt in flows)
	if not (has_positive and has_negative):
		return 0.0

	d0 = flows[0][0]

	# Helper function to compute residual value at rate r
	def f(r):
		val = 0.0
		for date, amount in flows:
			t = (date - d0).days / 365.0
			if 1.0 + r <= 0.0:
				return float('inf')
			val += amount / ((1.0 + r) ** t)
		return val

	# Helper function to compute the derivative of the residual value
	def df(r):
		val = 0.0
		for date, amount in flows:
			t = (date - d0).days / 365.0
			if 1.0 + r <= 0.0:
				return float('inf')
			val += -t * amount / ((1.0 + r) ** (t + 1.0))
		return val

	# Newton-Raphson solver loop
	r = 0.1  # Initial guess (10%)
	for _ in range(100):
		f_val = f(r)
		df_val = df(r)
		
		if df_val == 0.0 or f_val == float('inf') or df_val == float('inf'):
			break
			
		new_r = r - f_val / df_val
		
		# Convergence check
		if abs(new_r - r) < 1e-6:
			# Prevent extreme unreasonable returns
			if new_r > 100.0 or new_r < -0.999:
				return 0.0
			return round(new_r * 100.0, 2)
		r = new_r

	return 0.0


def calculate_asset_xirr(doc):
	"""
	Compiles cash flows for a specific Asset Portfolio document and returns its XIRR.
	"""
	import frappe
	from frappe.utils import flt, getdate, today

	raw_flows = []

	# Initial investment (outflow)
	if doc.date_of_investment and flt(doc.investment_value) > 0:
		raw_flows.append((getdate(doc.date_of_investment), -flt(doc.investment_value)))

	if doc.asset_type == "Stock":
		# Read transaction logs instead of the single date of investment (to be precise)
		# Clear raw_flows and rebuild solely from transactions + current value
		raw_flows = []
		txs = frappe.get_all("Stock Transaction Log",
			filters={"asset": doc.name, "docstatus": 1},
			fields=["transaction_date", "transaction_type", "total_amount"],
			order_by="transaction_date asc"
		)
		for tx in txs:
			amt = flt(tx.total_amount)
			if tx.transaction_type == "Buy":
				raw_flows.append((getdate(tx.transaction_date), -amt))
			elif tx.transaction_type == "Sell":
				raw_flows.append((getdate(tx.transaction_date), amt))
		
		# Add terminal value if active
		if doc.status == "Active" and flt(doc.current_value) > 0:
			raw_flows.append((getdate(today()), flt(doc.current_value)))

	elif doc.asset_type == "Savings Account":
		raw_flows = []
		txs = frappe.get_all("Savings Account Transaction Log",
			filters={"asset": doc.name, "docstatus": 1},
			fields=["transaction_date", "transaction_type", "amount"],
			order_by="transaction_date asc"
		)
		for tx in txs:
			amt = flt(tx.amount)
			if tx.transaction_type == "Deposit":
				raw_flows.append((getdate(tx.transaction_date), -amt))
			elif tx.transaction_type == "Withdrawal":
				raw_flows.append((getdate(tx.transaction_date), amt))

		# Add terminal value if active
		if doc.status == "Active" and flt(doc.current_value) > 0:
			raw_flows.append((getdate(today()), flt(doc.current_value)))

	elif doc.asset_type == "Bond":
		# Interest repayments (inflows)
		for entry in doc.bond_interest_schedule:
			if entry.status == "Paid" and flt(entry.interest_amount) > 0:
				raw_flows.append((getdate(entry.payment_date), flt(entry.interest_amount)))
		
		# Principal repayments (inflows)
		for entry in doc.bond_principal_schedule:
			if flt(entry.amount) > 0:
				raw_flows.append((getdate(entry.repayment_date), flt(entry.amount)))

		# Add remaining terminal value
		if doc.status == "Active" and flt(doc.current_value) > 0:
			raw_flows.append((getdate(today()), flt(doc.current_value)))

	elif doc.asset_type == "Fixed Deposit":
		# Interest repayments (inflows)
		for entry in doc.fd_interest_schedule:
			if flt(entry.interest_amount) > 0:
				raw_flows.append((getdate(entry.payment_date), flt(entry.interest_amount)))
		
		# Principal repayments (inflows)
		for entry in doc.fd_principal_schedule:
			if flt(entry.amount) > 0:
				raw_flows.append((getdate(entry.repayment_date), flt(entry.amount)))

		# Add remaining terminal value
		if doc.status == "Active" and flt(doc.current_value) > 0:
			raw_flows.append((getdate(today()), flt(doc.current_value)))

	else:
		# Generic asset types (PF, PPF, NPS etc.)
		if doc.status == "Active" and flt(doc.current_value) > 0:
			raw_flows.append((getdate(today()), flt(doc.current_value)))

	return xirr(raw_flows)
