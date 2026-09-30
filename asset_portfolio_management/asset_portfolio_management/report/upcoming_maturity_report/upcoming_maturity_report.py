# -*- coding: utf-8 -*-
# Copyright (c) 2026, Antigravity and contributors
# For license information, please see license.txt

import frappe
from frappe.utils import flt, getdate, today, date_diff

def execute(filters=None):
	if not filters:
		filters = {}

	query_filters = {
		"asset_type": ["in", ["Bond", "Fixed Deposit"]],
		"status": "Active",
		"maturity_date": ["is", "set"]
	}

	if filters.get("owner"):
		query_filters["owner"] = filters["owner"]

	assets = frappe.get_all("Asset Portfolio",
		filters=query_filters,
		fields=[
			"name", "asset_id", "asset_name", "asset_type", "provider",
			"owner", "maturity_date", "investment_value", "current_value"
		],
		order_by="maturity_date asc"
	)

	columns = [
		{
			"fieldname": "asset_id",
			"label": "Asset ID",
			"fieldtype": "Link",
			"options": "Asset Portfolio",
			"width": 120
		},
		{
			"fieldname": "asset_name",
			"label": "Asset Name",
			"fieldtype": "Data",
			"width": 180
		},
		{
			"fieldname": "asset_type",
			"label": "Asset Type",
			"fieldtype": "Select",
			"width": 120
		},
		{
			"fieldname": "provider",
			"label": "Provider / Bank",
			"fieldtype": "Data",
			"width": 140
		},
		{
			"fieldname": "owner",
			"label": "Owner",
			"fieldtype": "Link",
			"options": "Portfolio Owner",
			"width": 120
		},
		{
			"fieldname": "maturity_date",
			"label": "Maturity Date",
			"fieldtype": "Date",
			"width": 120
		},
		{
			"fieldname": "days_remaining",
			"label": "Days Remaining",
			"fieldtype": "Int",
			"width": 120
		},
		{
			"fieldname": "investment_value",
			"label": "Investment Value",
			"fieldtype": "Currency",
			"width": 130
		},
		{
			"fieldname": "current_value",
			"label": "Current Value (Outstanding)",
			"fieldtype": "Currency",
			"width": 130
		}
	]

	current_date = getdate(today())
	days_horizon = filters.get("days_horizon")

	data = []
	for asset in assets:
		maturity_date = getdate(asset.maturity_date)
		days_remaining = (maturity_date - current_date).days

		# Only display upcoming maturities (in future or today) matching the days horizon filter
		if days_remaining >= 0:
			if days_horizon is None or days_remaining <= int(days_horizon):
				data.append({
					"asset_id": asset.name,
					"asset_name": asset.asset_name,
					"asset_type": asset.asset_type,
					"provider": asset.provider,
					"owner": asset.owner,
					"maturity_date": asset.maturity_date,
					"days_remaining": days_remaining,
					"investment_value": flt(asset.investment_value),
					"current_value": flt(asset.current_value)
				})

	return columns, data
