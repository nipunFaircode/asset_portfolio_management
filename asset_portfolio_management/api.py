# -*- coding: utf-8 -*-
# Copyright (c) 2026, Antigravity and contributors
# For license information, please see license.txt

import frappe
from frappe.utils import flt

@frappe.whitelist()
def get_dashboard_data():
	"""
	Calculates and returns portfolio summaries for the Custom Dashboard UI.
	"""
	assets = frappe.get_all("Asset Portfolio",
		fields=["asset_type", "provider", "owner", "investment_value", "current_value", "total_gain_loss"]
	)

	total_investment = 0.0
	total_current = 0.0

	asset_types = {}
	providers = {}
	owners = {}

	for asset in assets:
		inv = flt(asset.investment_value)
		curr = flt(asset.current_value)

		total_investment += inv
		total_current += curr

		# Asset Type Breakdown
		a_type = asset.asset_type or "Unspecified"
		asset_types[a_type] = asset_types.get(a_type, 0.0) + curr

		# Provider Breakdown
		prov = asset.provider or "Unspecified"
		providers[prov] = providers.get(prov, 0.0) + curr

		# Owner Breakdown
		own = asset.owner or "Unspecified"
		owners[own] = owners.get(own, 0.0) + curr

	net_gain = total_current - total_investment
	overall_return = (net_gain / total_investment * 100.0) if total_investment > 0 else 0.0

	return {
		"total_investment": total_investment,
		"total_current": total_current,
		"net_gain": net_gain,
		"overall_return": round(overall_return, 2),
		"asset_types": [{"label": k, "value": v} for k, v in asset_types.items()],
		"providers": [{"label": k, "value": v} for k, v in providers.items()],
		"owners": [{"label": k, "value": v} for k, v in owners.items()]
	}
