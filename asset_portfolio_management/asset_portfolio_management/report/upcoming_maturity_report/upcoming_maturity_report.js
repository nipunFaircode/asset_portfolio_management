// Copyright (c) 2026, Antigravity and contributors
// For license information, please see license.txt

frappe.query_reports["Upcoming Maturity Report"] = {
	"filters": [
		{
			"fieldname": "owner",
			"label": __("Owner"),
			"fieldtype": "Link",
			"options": "Portfolio Owner"
		},
		{
			"fieldname": "days_horizon",
			"label": __("Maturity Within (Days)"),
			"fieldtype": "Int",
			"default": 90
		}
	]
};
