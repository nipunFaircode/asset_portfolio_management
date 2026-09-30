# -*- coding: utf-8 -*-
# Copyright (c) 2026, Antigravity and contributors
# For license information, please see license.txt

import frappe
from frappe.utils import flt

def execute(filters=None):
	if not filters:
		filters = {}

	query_filters = {}
	if filters.get("owner"):
		query_filters["owner"] = filters["owner"]
	if filters.get("asset_type"):
		query_filters["asset_type"] = filters["asset_type"]
	if filters.get("status"):
		query_filters["status"] = filters["status"]

	assets = frappe.get_all("Asset Portfolio",
		filters=query_filters,
		fields=[
			"name", "asset_id", "asset_name", "asset_type", "owner", "provider",
			"date_of_investment", "investment_value", "current_value",
			"total_gain_loss", "total_return_pct", "xirr", "status"
		],
		order_by="date_of_investment desc"
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
			"fieldname": "owner",
			"label": "Owner",
			"fieldtype": "Link",
			"options": "Portfolio Owner",
			"width": 120
		},
		{
			"fieldname": "provider",
			"label": "Provider / Bank",
			"fieldtype": "Data",
			"width": 140
		},
		{
			"fieldname": "date_of_investment",
			"label": "Date of Investment",
			"fieldtype": "Date",
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
			"label": "Current Value",
			"fieldtype": "Currency",
			"width": 130
		},
		{
			"fieldname": "total_gain_loss",
			"label": "Total Gain / Loss",
			"fieldtype": "Currency",
			"width": 130
		},
		{
			"fieldname": "total_return_pct",
			"label": "Total Return %",
			"fieldtype": "Percent",
			"width": 120
		},
		{
			"fieldname": "xirr",
			"label": "XIRR",
			"fieldtype": "Percent",
			"width": 100
		},
		{
			"fieldname": "status",
			"label": "Status",
			"fieldtype": "Select",
			"width": 100
		}
	]

	data = []
	for asset in assets:
		data.append({
			"asset_id": asset.name,  # link to the Asset Portfolio document name
			"asset_name": asset.asset_name,
			"asset_type": asset.asset_type,
			"owner": asset.owner,
			"provider": asset.provider,
			"date_of_investment": asset.date_of_investment,
			"investment_value": flt(asset.investment_value),
			"current_value": flt(asset.current_value),
			"total_gain_loss": flt(asset.total_gain_loss),
			"total_return_pct": flt(asset.total_return_pct),
			"xirr": flt(asset.xirr),
			"status": asset.status
		})

	# Summary values for dashboard panel in report
	total_investment = sum(d["investment_value"] for d in data)
	total_current = sum(d["current_value"] for d in data)
	total_gain = total_current - total_investment
	weighted_avg_return = 0.0
	if total_investment > 0:
		weighted_avg_return = (total_gain / total_investment) * 100.0

	report_summary = [
		{
			"value": total_investment,
			"indicator": "Blue",
			"label": "Total Investment Value",
			"datatype": "Currency"
		},
		{
			"value": total_current,
			"indicator": "Green",
			"label": "Total Current Value",
			"datatype": "Currency"
		},
		{
			"value": total_gain,
			"indicator": "Green" if total_gain >= 0 else "Red",
			"label": "Total Gain / Loss",
			"datatype": "Currency"
		},
		{
			"value": round(weighted_avg_return, 2),
			"indicator": "Green" if weighted_avg_return >= 0 else "Red",
			"label": "Weighted Return %",
			"datatype": "Percent"
		}
	]

	return columns, data, None, None, report_summary
