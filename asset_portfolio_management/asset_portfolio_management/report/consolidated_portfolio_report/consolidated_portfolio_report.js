// Copyright (c) 2026, Antigravity and contributors
// For license information, please see license.txt

frappe.query_reports["Consolidated Portfolio Report"] = {
	"filters": [
		{
			"fieldname": "owner",
			"label": __("Owner"),
			"fieldtype": "Link",
			"options": "Portfolio Owner"
		},
		{
			"fieldname": "asset_type",
			"label": __("Asset Type"),
			"fieldtype": "Select",
			"options": [
				"",
				"Stock",
				"Bond",
				"Fixed Deposit",
				"Savings Account",
				"PF",
				"PPF",
				"NPS"
			]
		},
		{
			"fieldname": "status",
			"label": __("Status"),
			"fieldtype": "Select",
			"options": [
				"",
				"Active",
				"Matured",
				"Closed"
			],
			"default": "Active"
		}
	]
};
