// Copyright (c) 2026, Antigravity and contributors
// For license information, please see license.txt

frappe.query_reports["Portfolio Allocation"] = {
	"filters": [
		{
			"fieldname": "owner",
			"label": __("Owner"),
			"fieldtype": "Link",
			"options": "Portfolio Owner"
		},
		{
			"fieldname": "group_by",
			"label": __("Group By"),
			"fieldtype": "Select",
			"options": [
				"Asset Type",
				"Provider",
				"Owner",
				"Industry",
				"Stock Category",
				"Bond Rating"
			],
			"default": "Asset Type",
			"reqd": 1
		}
	]
};
