// Copyright (c) 2026, Antigravity and contributors
// For license information, please see license.txt

frappe.pages['portfolio-dashboard'].on_page_load = function(wrapper) {
	var page = frappe.ui.make_app_page({
		parent: wrapper,
		title: 'Portfolio Dashboard',
		single_column: true
	});

	// Direct HTML injection ensures reliability across different Frappe versions
	var html = `
	<div class="portfolio-dashboard-wrapper">
		<div class="dashboard-header">
			<h2>Investment Portfolio Overview</h2>
			<p class="text-muted">Consolidated real-time asset tracking and performance metrics</p>
		</div>
		
		<!-- KPI Cards -->
		<div class="kpi-grid">
			<div class="kpi-card glassmorphic shadow-sm" id="kpi-total-investment">
				<div class="kpi-icon icon-investment">💵</div>
				<div class="kpi-details">
					<div class="kpi-label">Total Investment</div>
					<div class="kpi-value" id="val-total-investment">0.00</div>
				</div>
			</div>
			<div class="kpi-card glassmorphic shadow-sm" id="kpi-total-current">
				<div class="kpi-icon icon-current">📈</div>
				<div class="kpi-details">
					<div class="kpi-label">Current Value</div>
					<div class="kpi-value" id="val-total-current">0.00</div>
				</div>
			</div>
			<div class="kpi-card glassmorphic shadow-sm" id="kpi-net-gain">
				<div class="kpi-icon icon-gain">💰</div>
				<div class="kpi-details">
					<div class="kpi-label">Total Gain / Loss</div>
					<div class="kpi-value" id="val-net-gain">0.00</div>
				</div>
			</div>
			<div class="kpi-card glassmorphic shadow-sm" id="kpi-overall-return">
				<div class="kpi-icon icon-return">⚡</div>
				<div class="kpi-details">
					<div class="kpi-label">Overall Return</div>
					<div class="kpi-value" id="val-overall-return">0.00%</div>
				</div>
			</div>
		</div>

		<!-- Charts Grid -->
		<div class="charts-grid">
			<div class="chart-container glassmorphic card-padding shadow-sm">
				<h4 style="margin-top:0px;margin-bottom:15px;font-weight:600;color:#334155;">Asset Allocation (By Current Value)</h4>
				<div class="chart-area" id="chart-asset-type"></div>
			</div>
			<div class="chart-container glassmorphic card-padding shadow-sm">
				<h4 style="margin-top:0px;margin-bottom:15px;font-weight:600;color:#334155;">Provider Allocation (By Current Value)</h4>
				<div class="chart-area" id="chart-provider"></div>
			</div>
		</div>
	</div>
	`;

	$(page.body).empty().append(html);

	// Fetch portfolio statistics
	frappe.call({
		method: 'asset_portfolio_management.api.get_dashboard_data',
		callback: function(r) {
			if (r.message) {
				update_kpis(r.message);
				render_charts(r.message);
			}
		}
	});

	function update_kpis(data) {
		$('#val-total-investment').text(format_currency(data.total_investment));
		$('#val-total-current').text(format_currency(data.total_current));

		var net_gain_el = $('#val-net-gain');
		net_gain_el.text(format_currency(data.net_gain));
		if (data.net_gain >= 0) {
			net_gain_el.addClass('gain-positive').removeClass('gain-negative');
		} else {
			net_gain_el.addClass('gain-negative').removeClass('gain-positive');
		}

		var return_el = $('#val-overall-return');
		return_el.text(data.overall_return.toFixed(2) + '%');
		if (data.overall_return >= 0) {
			return_el.addClass('gain-positive').removeClass('gain-negative');
		} else {
			return_el.addClass('gain-negative').removeClass('gain-positive');
		}
	}

	function format_currency(value) {
		return frappe.format(value, { fieldtype: 'Currency' });
	}

	function render_charts(data) {
		// Render Asset Type Donut Chart
		if (data.asset_types && data.asset_types.length > 0) {
			new frappe.Chart("#chart-asset-type", {
				data: {
					labels: data.asset_types.map(d => d.label),
					datasets: [{ values: data.asset_types.map(d => d.value) }]
				},
				type: 'donut',
				height: 250,
				colors: ['#3498db', '#2ecc71', '#9b59b6', '#f1c40f', '#e67e22', '#e74c3c']
			});
		} else {
			$("#chart-asset-type").html("<div class='text-muted text-center' style='padding-top:80px;'>No asset data available</div>");
		}

		// Render Provider Donut Chart
		if (data.providers && data.providers.length > 0) {
			new frappe.Chart("#chart-provider", {
				data: {
					labels: data.providers.map(d => d.label),
					datasets: [{ values: data.providers.map(d => d.value) }]
				},
				type: 'donut',
				height: 250,
				colors: ['#1abc9c', '#34495e', '#d35400', '#27ae60', '#2980b9', '#8e44ad']
			});
		} else {
			$("#chart-provider").html("<div class='text-muted text-center' style='padding-top:80px;'>No provider data available</div>");
		}
	}
};
