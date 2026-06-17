# -*- coding: utf-8 -*-
# Unit tests for Asset Portfolio Management calculations and XIRR engine

import sys
import os
import datetime
import unittest
from unittest.mock import MagicMock, patch

# Add workspace package root to python search path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# 1. Mock Frappe module before importing our custom controllers
class MockDocument(object):
	def __init__(self, **kwargs):
		for k, v in kwargs.items():
			setattr(self, k, v)
	def save(self):
		pass

mock_frappe = MagicMock()
mock_frappe.model.document.Document = MockDocument
mock_frappe.utils.flt = lambda val: float(val or 0.0)
mock_frappe.utils.getdate = lambda d: d if isinstance(d, datetime.date) else datetime.datetime.strptime(str(d)[:10], "%Y-%m-%d").date()
mock_frappe.utils.today = lambda: "2026-06-17"

sys.modules['frappe'] = mock_frappe
sys.modules['frappe.model.document'] = mock_frappe.model.document
sys.modules['frappe.utils'] = mock_frappe.utils

# 2. Now import our actual modules
from asset_portfolio_management.utils.xirr import xirr, calculate_asset_xirr
from asset_portfolio_management.doctype.asset_portfolio.asset_portfolio import AssetPortfolio
from asset_portfolio_management.doctype.stock_transaction_log.stock_transaction_log import StockTransactionLog
from asset_portfolio_management.doctype.savings_account_transaction_log.savings_account_transaction_log import SavingsAccountTransactionLog


class TestPortfolioCalculations(unittest.TestCase):
	
	def test_xirr_exact_values(self):
		"""Test standard XIRR calculations with known investments and inflows."""
		# Standard scenario: Invest $10,000, get $10,600 one year later -> 6.0% return
		flows = [
			(datetime.date(2025, 1, 1), -10000.0),
			(datetime.date(2026, 1, 1), 10600.0)
		]
		rate = xirr(flows)
		self.assertAlmostEqual(rate, 6.0, places=1)

		# Scenario with multiple flows:
		# Invest $1,000 on Jan 1, invest $2,000 on Jul 1, withdraw $3,200 on Dec 31
		flows2 = [
			(datetime.date(2025, 1, 1), -1000.0),
			(datetime.date(2025, 7, 1), -2000.0),
			(datetime.date(2025, 12, 31), 3200.0)
		]
		rate2 = xirr(flows2)
		# Correct XIRR should be around 10.12% annualized
		self.assertAlmostEqual(rate2, 10.12, places=1)

	def test_xirr_impossible_sign(self):
		"""XIRR is mathematically undefined if all cash flows are positive or negative."""
		flows = [
			(datetime.date(2025, 1, 1), -1000.0),
			(datetime.date(2026, 1, 1), -1050.0)
		]
		self.assertEqual(xirr(flows), 0.0)

	def test_bond_calculations(self):
		"""Verify bond interest, principal, and net return calculations."""
		# Create mock child logs
		interest_item1 = MockDocument(interest_amount=150.0, status="Paid", payment_date="2025-06-01")
		interest_item2 = MockDocument(interest_amount=150.0, status="Pending", payment_date="2025-12-01")
		principal_item = MockDocument(amount=500.0, repayment_date="2025-06-01")

		bond = AssetPortfolio(
			asset_type="Bond",
			investment_value=1000.0,
			bond_interest_schedule=[interest_item1, interest_item2],
			bond_principal_schedule=[principal_item]
		)

		bond.calculate_totals()

		# Verify total paid and unpaid interest
		self.assertEqual(bond.interest_paid, 150.0)
		self.assertEqual(bond.interest_unpaid, 150.0)
		
		# Verify outstanding principal
		self.assertEqual(bond.principal_paid, 500.0)
		self.assertEqual(bond.principal_unpaid, 500.0)
		self.assertEqual(bond.current_value, 500.0)
		
		# Verify total gain and return percentage
		# Gain = (Current Value [500] + Interest Paid [150] + Principal Paid [500]) - Investment Value [1000] = 150
		self.assertEqual(bond.total_gain_loss, 150.0)
		self.assertEqual(bond.total_return_pct, 15.0)

	def test_fixed_deposit_calculations(self):
		"""Verify fixed deposit calculations."""
		fd = AssetPortfolio(
			asset_type="Fixed Deposit",
			investment_value=5000.0,
			fd_interest_schedule=[
				MockDocument(interest_amount=200.0, payment_date="2025-06-01"),
				MockDocument(interest_amount=250.0, payment_date="2025-12-01")
			],
			fd_principal_schedule=[]
		)

		fd.calculate_totals()

		self.assertEqual(fd.fd_interest_paid, 450.0)
		self.assertEqual(fd.fd_principal_paid, 0.0)
		self.assertEqual(fd.fd_principal_unpaid, 5000.0)
		self.assertEqual(fd.current_value, 5000.0)
		self.assertEqual(fd.total_gain_loss, 450.0)
		self.assertEqual(fd.total_return_pct, 9.0)

	@patch('frappe.get_all')
	def test_stock_transaction_average_basis(self, mock_get_all):
		"""Verify stock buy/sell calculations and average purchase price basis."""
		# Simulate a history of two buy transactions
		mock_get_all.return_value = [
			StockTransactionLog(transaction_type="Buy", quantity=10, price=100.0, brokerage=10.0, taxes_fees=5.0, total_amount=1015.0),
			StockTransactionLog(transaction_type="Buy", quantity=10, price=120.0, brokerage=10.0, taxes_fees=5.0, total_amount=1215.0)
		]

		sell_tx = StockTransactionLog(
			asset="Stock Asset",
			transaction_type="Sell",
			quantity=5,
			price=130.0,
			brokerage=10.0,
			taxes_fees=5.0,
			name="Sell TX"
		)

		# Validate will trigger calculate_total_amount & calculate_realized_gain_loss
		sell_tx.validate()

		# Total amount = (5 * 130) - 10 - 5 = 635.0
		self.assertEqual(sell_tx.total_amount, 635.0)

		# Average purchase price up to this point = (1015 + 1215) / 20 = 111.5
		# Realized gain = 635.0 - (5 * 111.5) = 635.0 - 557.5 = 77.5
		self.assertEqual(sell_tx.realized_gain_loss, 77.5)


if __name__ == '__main__':
	unittest.main()
