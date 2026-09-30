# -*- coding: utf-8 -*-
# Copyright (c) 2026, Antigravity and contributors
# For license information, please see license.txt

import frappe
from frappe.utils import flt

def execute(filters=None):
	if not filters:
		filters = {}

	group_by = filters.get("group_by") or "Asset Type"
	owner = filters.get("owner")

	# Map filter selection to database field names
	field_map = {
		"Asset Type": "asset_type",
		"Provider": "provider",
		"Owner": "owner",
		"Industry": "industry",
		"Stock Category": "stock_category",
		"Bond Rating": "bond_rating"
	}

	db_field = field_map.get(group_by, "asset_type")

	query_filters = {}
	if owner:
		query_filters["owner"] = owner

	assets = frappe.get_all("Asset Portfolio",
		filters=query_filters,
		fields=[db_field, "investment_value", "current_value", "total_gain_loss"]
	)

	aggregated = {}
	total_current_val = 0.0

	for asset in assets:
		val = asset.get(db_field) or "Not Specified"
		if val not in aggregated:
			aggregated[val] = {"investment": 0.0, "current": 0.0, "gain": 0.0}
		aggregated[val]["investment"] += flt(asset.investment_value)
		aggregated[val]["current"] += flt(asset.current_value)
		aggregated[val]["gain"] += flt(asset.total_gain_loss)
		total_current_val += flt(asset.current_value)

	columns = [
		{
			"fieldname": "grouping_value",
			"label": group_by,
			"fieldtype": "Data",
			"width": 180
		},
		{
			"fieldname": "investment_value",
			"label": "Investment Value",
			"fieldtype": "Currency",
			"width": 150
		},
		{
			"fieldname": "current_value",
			"label": "Current Value",
			"fieldtype": "Currency",
			"width": 150
		},
		{
			"fieldname": "gain_loss",
			"label": "Gain / Loss",
			"fieldtype": "Currency",
			"width": 150
		},
		{
			"fieldname": "allocation_pct",
			"label": "Allocation %",
			"fieldtype": "Percent",
			"width": 120
		}
	]

	data = []
	for val, stats in aggregated.items():
		pct = (stats["current"] / total_current_val * 100.0) if total_current_val > 0 else 0.0
		row = {
			"grouping_value": val,
			"investment_value": stats["investment"],
			"current_value": stats["current"],
			"gain_loss": stats["gain"],
			"allocation_pct": round(pct, 2)
		}
		data.append(row)

	# Build allocation chart
	chart = {
		"data": {
			"labels": [d["grouping_value"] for d in data],
			"datasets": [
				{
					"name": "Current Value Allocation",
					"values": [d["current_value"] for d in data]
				}
			]
		},
		"type": "percentage" if len(data) <= 6 else "bar",
		"colors": ["#1abc9c", "#2ecc71", "#3498db", "#9b59b6", "#f1c40f", "#e67e22", "#e74c3c"]
	}

	return columns, data, None, chart
