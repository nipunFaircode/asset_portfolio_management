from setuptools import setup, find_packages

with open("requirements.txt") as f:
	install_requires = f.read().strip().split("\n")

setup(
	name="asset_portfolio_management",
	version="0.0.1",
	description="Asset Portfolio Management custom app for tracking investments",
	author="Antigravity",
	author_email="antigravity@example.com",
	packages=find_packages(),
	zip_safe=False,
	include_package_data=True,
	install_requires=[r for r in install_requires if r and not r.startswith("#")]
)
