"""
Seed a realistic universe of Indian equities (Reliance, TCS, HDFC Bank, Infosys, etc.)
along with sectors, industries, exchange listings, and initial prices.
Idempotent and safe to run multiple times.
"""

import uuid
from datetime import date, datetime, timedelta
from sqlalchemy.orm import Session

try:
    from backend.database import SessionLocal
    from backend.models import (
        Exchange,
        Sector,
        Industry,
        Company,
        CompanyIndustry,
        Security,
        InstrumentListing,
        DataSource,
        MarketPrice,
    )
    from backend.market_data.adapter import SimulatedMarketProvider
    from backend.market_data.ingestion import MarketDataIngestionService
except ImportError:
    from database import SessionLocal
    from models import (
        Exchange,
        Sector,
        Industry,
        Company,
        CompanyIndustry,
        Security,
        InstrumentListing,
        DataSource,
        MarketPrice,
    )
    from market_data.adapter import SimulatedMarketProvider
    from market_data.ingestion import MarketDataIngestionService

NSE_EXCHANGE_ID = uuid.UUID("30000000-0000-4000-8000-000000000002")

UNIVERSE_DATA = [
    {
        "symbol": "RELIANCE",
        "company_name": "Reliance Industries Limited",
        "isin": "INE002A01018",
        "sector_code": "ENERGY",
        "sector_name": "Energy & Petrochemicals",
        "industry_code": "OIL_GAS_REFINING",
        "industry_name": "Oil & Gas Refining & Marketing",
        "base_price": 2850.0,
    },
    {
        "symbol": "TCS",
        "company_name": "Tata Consultancy Services Limited",
        "isin": "INE467B01029",
        "sector_code": "TECH",
        "sector_name": "Information Technology",
        "industry_code": "IT_SERVICES",
        "industry_name": "IT Services & Consulting",
        "base_price": 3950.0,
    },
    {
        "symbol": "HDFCBANK",
        "company_name": "HDFC Bank Limited",
        "isin": "INE040A01034",
        "sector_code": "FINANCIALS",
        "sector_name": "Banking & Financial Services",
        "industry_code": "PRIVATE_BANKS",
        "industry_name": "Private Sector Banks",
        "base_price": 1680.0,
    },
    {
        "symbol": "INFY",
        "company_name": "Infosys Limited",
        "isin": "INE009A01021",
        "sector_code": "TECH",
        "sector_name": "Information Technology",
        "industry_code": "IT_SERVICES",
        "industry_name": "IT Services & Consulting",
        "base_price": 1820.0,
    },
    {
        "symbol": "ICICIBANK",
        "company_name": "ICICI Bank Limited",
        "isin": "INE090A01021",
        "sector_code": "FINANCIALS",
        "sector_name": "Banking & Financial Services",
        "industry_code": "PRIVATE_BANKS",
        "industry_name": "Private Sector Banks",
        "base_price": 1240.0,
    },
    {
        "symbol": "TATAMOTORS",
        "company_name": "Tata Motors Limited",
        "isin": "INE155A01022",
        "sector_code": "AUTO",
        "sector_name": "Automotive",
        "industry_code": "COMMERCIAL_VEHICLES",
        "industry_name": "Automobiles & Commercial Vehicles",
        "base_price": 940.0,
    },
    {
        "symbol": "SUNPHARMA",
        "company_name": "Sun Pharmaceutical Industries Limited",
        "isin": "INE044A01036",
        "sector_code": "HEALTH",
        "sector_name": "Healthcare & Pharmaceuticals",
        "industry_code": "PHARMACEUTICALS",
        "industry_name": "Pharmaceuticals",
        "base_price": 1720.0,
    },
    {
        "symbol": "HINDUNILVR",
        "company_name": "Hindustan Unilever Limited",
        "isin": "INE030A01027",
        "sector_code": "FMCG",
        "sector_name": "Fast Moving Consumer Goods",
        "industry_code": "PACKAGED_FOODS",
        "industry_name": "Diversified FMCG",
        "base_price": 2480.0,
    },
    {
        "symbol": "LT",
        "company_name": "Larsen & Toubro Limited",
        "isin": "INE018A01030",
        "sector_code": "INFRA",
        "sector_name": "Infrastructure & Capital Goods",
        "industry_code": "ENGINEERING_CONSTRUCTION",
        "industry_name": "Engineering & Construction",
        "base_price": 3580.0,
    },
    {
        "symbol": "SBIN",
        "company_name": "State Bank of India",
        "isin": "INE062A01020",
        "sector_code": "FINANCIALS",
        "sector_name": "Banking & Financial Services",
        "industry_code": "PUBLIC_BANKS",
        "industry_name": "Public Sector Banks",
        "base_price": 810.0,
    },
    {
        "symbol": "KOTAKBANK",
        "company_name": "Kotak Mahindra Bank Limited",
        "isin": "INE237A01028",
        "sector_code": "FINANCIALS",
        "sector_name": "Banking & Financial Services",
        "industry_code": "PRIVATE_BANKS",
        "industry_name": "Private Sector Banks",
        "base_price": 1790.0,
    },
    {
        "symbol": "AXISBANK",
        "company_name": "Axis Bank Limited",
        "isin": "INE238A01034",
        "sector_code": "FINANCIALS",
        "sector_name": "Banking & Financial Services",
        "industry_code": "PRIVATE_BANKS",
        "industry_name": "Private Sector Banks",
        "base_price": 1180.0,
    },
    {
        "symbol": "BAJFINANCE",
        "company_name": "Bajaj Finance Limited",
        "isin": "INE296A01024",
        "sector_code": "FINANCIALS",
        "sector_name": "Banking & Financial Services",
        "industry_code": "NBFC",
        "industry_name": "Non-Banking Financial Companies",
        "base_price": 6950.0,
    },
    {
        "symbol": "BAJAJFINSV",
        "company_name": "Bajaj Finserv Limited",
        "isin": "INE918I01026",
        "sector_code": "FINANCIALS",
        "sector_name": "Banking & Financial Services",
        "industry_code": "NBFC",
        "industry_name": "Financial Services & Insurance",
        "base_price": 1620.0,
    },
    {
        "symbol": "BHARTIARTL",
        "company_name": "Bharti Airtel Limited",
        "isin": "INE397D01024",
        "sector_code": "TELECOM",
        "sector_name": "Telecommunications",
        "industry_code": "TELECOM_SERVICES",
        "industry_name": "Wireless & Enterprise Telecom",
        "base_price": 1580.0,
    },
    {
        "symbol": "ITC",
        "company_name": "ITC Limited",
        "isin": "INE154A01025",
        "sector_code": "FMCG",
        "sector_name": "Fast Moving Consumer Goods",
        "industry_code": "TOBACCO_FMCG",
        "industry_name": "Diversified FMCG & Cigarettes",
        "base_price": 485.0,
    },
    {
        "symbol": "NESTLEIND",
        "company_name": "Nestle India Limited",
        "isin": "INE239A01024",
        "sector_code": "FMCG",
        "sector_name": "Fast Moving Consumer Goods",
        "industry_code": "PACKAGED_FOODS",
        "industry_name": "Packaged Foods & Dairy",
        "base_price": 2340.0,
    },
    {
        "symbol": "TITAN",
        "company_name": "Titan Company Limited",
        "isin": "INE280A01028",
        "sector_code": "CONSUMER",
        "sector_name": "Consumer Discretionary",
        "industry_code": "RETAIL_JEWELLERY",
        "industry_name": "Jewellery & Lifestyle Retail",
        "base_price": 3320.0,
    },
    {
        "symbol": "ASIANPAINT",
        "company_name": "Asian Paints Limited",
        "isin": "INE021A01026",
        "sector_code": "CONSUMER",
        "sector_name": "Consumer Discretionary",
        "industry_code": "PAINTS",
        "industry_name": "Decorative Paints & Coatings",
        "base_price": 2890.0,
    },
    {
        "symbol": "MARUTI",
        "company_name": "Maruti Suzuki India Limited",
        "isin": "INE585B01010",
        "sector_code": "AUTO",
        "sector_name": "Automotive",
        "industry_code": "PASSENGER_VEHICLES",
        "industry_name": "Passenger Cars & Utility Vehicles",
        "base_price": 11850.0,
    },
    {
        "symbol": "MNM",
        "company_name": "Mahindra & Mahindra Limited",
        "isin": "INE774D01024",
        "sector_code": "AUTO",
        "sector_name": "Automotive",
        "industry_code": "PASSENGER_VEHICLES",
        "industry_name": "SUVs & Farm Equipment",
        "base_price": 2780.0,
    },
    {
        "symbol": "WIPRO",
        "company_name": "Wipro Limited",
        "isin": "INE075A01022",
        "sector_code": "TECH",
        "sector_name": "Information Technology",
        "industry_code": "IT_SERVICES",
        "industry_name": "IT Services & Consulting",
        "base_price": 540.0,
    },
    {
        "symbol": "HCLTECH",
        "company_name": "HCL Technologies Limited",
        "isin": "INE860A01027",
        "sector_code": "TECH",
        "sector_name": "Information Technology",
        "industry_code": "IT_SERVICES",
        "industry_name": "IT Services & Digital Engineering",
        "base_price": 1760.0,
    },
    {
        "symbol": "TECHM",
        "company_name": "Tech Mahindra Limited",
        "isin": "INE669C01036",
        "sector_code": "TECH",
        "sector_name": "Information Technology",
        "industry_code": "IT_SERVICES",
        "industry_name": "Telecom & Enterprise IT Services",
        "base_price": 1620.0,
    },
    {
        "symbol": "CIPLA",
        "company_name": "Cipla Limited",
        "isin": "INE059A01026",
        "sector_code": "HEALTH",
        "sector_name": "Healthcare & Pharmaceuticals",
        "industry_code": "PHARMACEUTICALS",
        "industry_name": "Respiratory & Generic Pharmaceuticals",
        "base_price": 1520.0,
    },
    {
        "symbol": "DRREDDY",
        "company_name": "Dr. Reddy's Laboratories Limited",
        "isin": "INE089A01023",
        "sector_code": "HEALTH",
        "sector_name": "Healthcare & Pharmaceuticals",
        "industry_code": "PHARMACEUTICALS",
        "industry_name": "Global Generics & Active Ingredients",
        "base_price": 6450.0,
    },
    {
        "symbol": "APOLLOHOSP",
        "company_name": "Apollo Hospitals Enterprise Limited",
        "isin": "INE437A01024",
        "sector_code": "HEALTH",
        "sector_name": "Healthcare & Pharmaceuticals",
        "industry_code": "HOSPITALS",
        "industry_name": "Tertiary Hospitals & Omnichannel Pharmacies",
        "base_price": 6850.0,
    },
    {
        "symbol": "TATASTEEL",
        "company_name": "Tata Steel Limited",
        "isin": "INE081A01020",
        "sector_code": "METALS",
        "sector_name": "Metals & Mining",
        "industry_code": "STEEL",
        "industry_name": "Integrated Primary Steel",
        "base_price": 155.0,
    },
    {
        "symbol": "JSWSTEEL",
        "company_name": "JSW Steel Limited",
        "isin": "INE019A01038",
        "sector_code": "METALS",
        "sector_name": "Metals & Mining",
        "industry_code": "STEEL",
        "industry_name": "Primary & Value-Added Steel",
        "base_price": 960.0,
    },
    {
        "symbol": "NTPC",
        "company_name": "NTPC Limited",
        "isin": "INE733E01010",
        "sector_code": "POWER",
        "sector_name": "Power & Utilities",
        "industry_code": "POWER_GENERATION",
        "industry_name": "Thermal & Green Energy Generation",
        "base_price": 395.0,
    },
    {
        "symbol": "POWERGRID",
        "company_name": "Power Grid Corporation of India Limited",
        "isin": "INE752E01010",
        "sector_code": "POWER",
        "sector_name": "Power & Utilities",
        "industry_code": "POWER_TRANSMISSION",
        "industry_name": "National Inter-State Power Transmission",
        "base_price": 325.0,
    },
    {
        "symbol": "ONGC",
        "company_name": "Oil & Natural Gas Corporation Limited",
        "isin": "INE213A01029",
        "sector_code": "ENERGY",
        "sector_name": "Energy & Petrochemicals",
        "industry_code": "OIL_EXPLORATION",
        "industry_name": "Upstream Oil & Gas Exploration",
        "base_price": 285.0,
    },
    {
        "symbol": "COALINDIA",
        "company_name": "Coal India Limited",
        "isin": "INE522F01014",
        "sector_code": "METALS",
        "sector_name": "Metals & Mining",
        "industry_code": "MINING",
        "industry_name": "Primary Energy Minerals & Mining",
        "base_price": 460.0,
    },
    {
        "symbol": "ULTRACEMCO",
        "company_name": "UltraTech Cement Limited",
        "isin": "INE481G01011",
        "sector_code": "INFRA",
        "sector_name": "Infrastructure & Capital Goods",
        "industry_code": "CEMENT",
        "industry_name": "Grey Cement & Ready-Mix Concrete",
        "base_price": 11200.0,
    },
    {
        "symbol": "ADANIPORTS",
        "company_name": "Adani Ports and Special Economic Zone Limited",
        "isin": "INE742F01042",
        "sector_code": "INFRA",
        "sector_name": "Infrastructure & Capital Goods",
        "industry_code": "PORTS_LOGISTICS",
        "industry_name": "Commercial Marine Ports & Multi-Modal Logistics",
        "base_price": 1360.0,
    },
    {
        "symbol": "BRITANNIA",
        "company_name": "Britannia Industries Limited",
        "isin": "INE216A01030",
        "sector_code": "FMCG",
        "sector_name": "Fast Moving Consumer Goods",
        "industry_code": "PACKAGED_FOODS",
        "industry_name": "Bakery & Packaged Foods",
        "base_price": 5450.0,
    },
    {
        "symbol": "TRENT",
        "company_name": "Trent Limited",
        "isin": "INE849A01020",
        "sector_code": "CONSUMER",
        "sector_name": "Consumer Discretionary",
        "industry_code": "RETAIL_APPAREL",
        "industry_name": "Apparel & Lifestyle Retail (Westside & Zudio)",
        "base_price": 6480.0,
    },
    {
        "symbol": "DMART",
        "company_name": "Avenue Supermarts Limited",
        "isin": "INE192R01011",
        "sector_code": "CONSUMER",
        "sector_name": "Consumer Discretionary",
        "industry_code": "HYPERMARKETS",
        "industry_name": "Organized Value Grocery & Supermarkets",
        "base_price": 4120.0,
    },
    {
        "symbol": "ZOMATO",
        "company_name": "Zomato Limited",
        "isin": "INE758T01015",
        "sector_code": "CONSUMER",
        "sector_name": "Consumer Discretionary",
        "industry_code": "QUICK_COMMERCE",
        "industry_name": "Food Delivery & Quick Commerce (Blinkit)",
        "base_price": 265.0,
    },
    {
        "symbol": "LTIM",
        "company_name": "LTIMindtree Limited",
        "isin": "INE214T01019",
        "sector_code": "TECH",
        "sector_name": "Information Technology",
        "industry_code": "IT_SERVICES",
        "industry_name": "Enterprise Digital Transformation & AI",
        "base_price": 5850.0,
    },
    {
        "symbol": "PERSISTENT",
        "company_name": "Persistent Systems Limited",
        "isin": "INE262H01013",
        "sector_code": "TECH",
        "sector_name": "Information Technology",
        "industry_code": "DIGITAL_ENGINEERING",
        "industry_name": "Digital Product Engineering & Cloud Solutions",
        "base_price": 5280.0,
    },
    {
        "symbol": "INDUSINDBK",
        "company_name": "IndusInd Bank Limited",
        "isin": "INE095A01012",
        "sector_code": "FINANCIALS",
        "sector_name": "Banking & Financial Services",
        "industry_code": "PRIVATE_BANKS",
        "industry_name": "Vehicle Finance & Private Banking",
        "base_price": 1320.0,
    },
    {
        "symbol": "BANKBARODA",
        "company_name": "Bank of Baroda",
        "isin": "INE028A01039",
        "sector_code": "FINANCIALS",
        "sector_name": "Banking & Financial Services",
        "industry_code": "PUBLIC_BANKS",
        "industry_name": "Public Sector Banking & Corporate Lending",
        "base_price": 245.0,
    },
    {
        "symbol": "HDFCLIFE",
        "company_name": "HDFC Life Insurance Company Limited",
        "isin": "INE795G01014",
        "sector_code": "FINANCIALS",
        "sector_name": "Banking & Financial Services",
        "industry_code": "LIFE_INSURANCE",
        "industry_name": "Life Insurance & Long-Term Annuities",
        "base_price": 710.0,
    },
    {
        "symbol": "SBILIFE",
        "company_name": "SBI Life Insurance Company Limited",
        "isin": "INE123W01016",
        "sector_code": "FINANCIALS",
        "sector_name": "Banking & Financial Services",
        "industry_code": "LIFE_INSURANCE",
        "industry_name": "Bancassurance & Term Life Protection",
        "base_price": 1540.0,
    },
    {
        "symbol": "BAJAJ-AUTO",
        "company_name": "Bajaj Auto Limited",
        "isin": "INE917I01010",
        "sector_code": "AUTO",
        "sector_name": "Automotive",
        "industry_code": "TWO_THREE_WHEELERS",
        "industry_name": "Motorcycles, Three-Wheelers & EV Chetak",
        "base_price": 9850.0,
    },
    {
        "symbol": "EICHERMOT",
        "company_name": "Eicher Motors Limited",
        "isin": "INE066A01021",
        "sector_code": "AUTO",
        "sector_name": "Automotive",
        "industry_code": "PREMIUM_MOTORCYCLES",
        "industry_name": "Royal Enfield Premium Motorcycles & Commercial Trucks",
        "base_price": 4750.0,
    },
    {
        "symbol": "HEROMOTOCO",
        "company_name": "Hero MotoCorp Limited",
        "isin": "INE158A01026",
        "sector_code": "AUTO",
        "sector_name": "Automotive",
        "industry_code": "TWO_WHEELERS",
        "industry_name": "Mass Market Motorcycles & Scooters",
        "base_price": 4920.0,
    },
    {
        "symbol": "TATACONSUM",
        "company_name": "Tata Consumer Products Limited",
        "isin": "INE192A01025",
        "sector_code": "FMCG",
        "sector_name": "Fast Moving Consumer Goods",
        "industry_code": "PACKAGED_BEVERAGES_FOODS",
        "industry_name": "Tata Tea, Tata Salt, Sampann & NourishCo",
        "base_price": 1080.0,
    },
    {
        "symbol": "DABUR",
        "company_name": "Dabur India Limited",
        "isin": "INE016A01026",
        "sector_code": "FMCG",
        "sector_name": "Fast Moving Consumer Goods",
        "industry_code": "AYURVEDIC_HEALTHCARE",
        "industry_name": "Ayurvedic Healthcare, Personal Care & Fruit Juices",
        "base_price": 540.0,
    },
    {
        "symbol": "MARICO",
        "company_name": "Marico Limited",
        "isin": "INE196A01026",
        "sector_code": "FMCG",
        "sector_name": "Fast Moving Consumer Goods",
        "industry_code": "HAIR_EDIBLE_OILS",
        "industry_name": "Parachute Coconut Oil, Saffola & Premium Personal Care",
        "base_price": 625.0,
    },
    {
        "symbol": "DIVISLAB",
        "company_name": "Divi's Laboratories Limited",
        "isin": "INE361B01024",
        "sector_code": "HEALTH",
        "sector_name": "Healthcare & Pharmaceuticals",
        "industry_code": "ACTIVE_PHARMA_INGREDIENTS",
        "industry_name": "Custom Synthesis & Active Pharmaceutical Ingredients (APIs)",
        "base_price": 5980.0,
    },
    {
        "symbol": "LUPIN",
        "company_name": "Lupin Limited",
        "isin": "INE326A01037",
        "sector_code": "HEALTH",
        "sector_name": "Healthcare & Pharmaceuticals",
        "industry_code": "PHARMACEUTICALS",
        "industry_name": "Inhalation, Generic & Branded Formulations",
        "base_price": 2180.0,
    },
    {
        "symbol": "MANKIND",
        "company_name": "Mankind Pharma Limited",
        "isin": "INE634S01028",
        "sector_code": "HEALTH",
        "sector_name": "Healthcare & Pharmaceuticals",
        "industry_code": "DOMESTIC_FORMULATIONS",
        "industry_name": "Domestic Prescription Formulations & Consumer Healthcare",
        "base_price": 2540.0,
    },
    {
        "symbol": "BPCL",
        "company_name": "Bharat Petroleum Corporation Limited",
        "isin": "INE029A01011",
        "sector_code": "ENERGY",
        "sector_name": "Energy & Petrochemicals",
        "industry_code": "REFINING_MARKETING",
        "industry_name": "Fuel Retailing, Downstream Refining & Petrochemicals",
        "base_price": 310.0,
    },
    {
        "symbol": "IOC",
        "company_name": "Indian Oil Corporation Limited",
        "isin": "INE242A01010",
        "sector_code": "ENERGY",
        "sector_name": "Energy & Petrochemicals",
        "industry_code": "REFINING_MARKETING",
        "industry_name": "National Fuel Pipelines & Refining Network",
        "base_price": 145.0,
    },
    {
        "symbol": "TATAPOWER",
        "company_name": "The Tata Power Company Limited",
        "isin": "INE245A01021",
        "sector_code": "POWER",
        "sector_name": "Power & Utilities",
        "industry_code": "GREEN_ENERGY_UTILITIES",
        "industry_name": "Renewable Solar, Wind, EV Charging & Power Distribution",
        "base_price": 415.0,
    },
    {
        "symbol": "ADANIGREEN",
        "company_name": "Adani Green Energy Limited",
        "isin": "INE364U01010",
        "sector_code": "POWER",
        "sector_name": "Power & Utilities",
        "industry_code": "RENEWABLE_ENERGY",
        "industry_name": "Utility-Scale Solar & Wind Power Generation",
        "base_price": 1620.0,
    },
    {
        "symbol": "SIEMENS",
        "company_name": "Siemens Limited",
        "isin": "INE003A01024",
        "sector_code": "INFRA",
        "sector_name": "Infrastructure & Capital Goods",
        "industry_code": "INDUSTRIAL_AUTOMATION",
        "industry_name": "Smart Infrastructure, Power Grids & Digital Industry",
        "base_price": 7450.0,
    },
    {
        "symbol": "ABB",
        "company_name": "ABB India Limited",
        "isin": "INE117A01022",
        "sector_code": "INFRA",
        "sector_name": "Infrastructure & Capital Goods",
        "industry_code": "ROBOTICS_AUTOMATION",
        "industry_name": "Electrification, Industrial Motion & Robotics",
        "base_price": 7920.0,
    },
    {
        "symbol": "BEL",
        "company_name": "Bharat Electronics Limited",
        "isin": "INE263A01024",
        "sector_code": "INFRA",
        "sector_name": "Infrastructure & Capital Goods",
        "industry_code": "DEFENSE_ELECTRONICS",
        "industry_name": "Radar, Naval Sonar, Avionics & Electronic Warfare",
        "base_price": 295.0,
    },
    {
        "symbol": "HAL",
        "company_name": "Hindustan Aeronautics Limited",
        "isin": "INE066F01012",
        "sector_code": "INFRA",
        "sector_name": "Infrastructure & Capital Goods",
        "industry_code": "DEFENSE_AEROSPACE",
        "industry_name": "Tejas Fighter Aircraft, Helicopters & Aerospace Engineering",
        "base_price": 4450.0,
    },
    {
        "symbol": "HINDALCO",
        "company_name": "Hindalco Industries Limited",
        "isin": "INE038A01020",
        "sector_code": "METALS",
        "sector_name": "Metals & Mining",
        "industry_code": "ALUMINIUM_COPPER",
        "industry_name": "Aluminium Flat Rolled Products (Novelis) & Refined Copper",
        "base_price": 680.0,
    },
    {
        "symbol": "VEDL",
        "company_name": "Vedanta Limited",
        "isin": "INE205A01025",
        "sector_code": "METALS",
        "sector_name": "Metals & Mining",
        "industry_code": "DIVERSIFIED_MINERALS",
        "industry_name": "Zinc (Hindustan Zinc), Oil & Gas, Aluminium & Iron Ore",
        "base_price": 470.0,
    },
    {
        "symbol": "PIDILITIND",
        "company_name": "Pidilite Industries Limited",
        "isin": "INE318A01026",
        "sector_code": "CHEMICALS",
        "sector_name": "Specialty Chemicals",
        "industry_code": "ADHESIVES_SEALANTS",
        "industry_name": "Fevicol Consumer Adhesives, Sealants & Construction Chemicals",
        "base_price": 3120.0,
    },
    {
        "symbol": "SRF",
        "company_name": "SRF Limited",
        "isin": "INE647A01010",
        "sector_code": "CHEMICALS",
        "sector_name": "Specialty Chemicals",
        "industry_code": "FLUOROCHEMICALS",
        "industry_name": "Fluorochemicals, Specialty Agrochemical Intermediates & Packaging",
        "base_price": 2290.0,
    },
    {
        "symbol": "POLYCAB",
        "company_name": "Polycab India Limited",
        "isin": "INE455K01017",
        "sector_code": "INFRA",
        "sector_name": "Infrastructure & Capital Goods",
        "industry_code": "WIRES_CABLES",
        "industry_name": "Power Wires, Industrial Cables & Fast Moving Electrical Goods",
        "base_price": 6650.0,
    },
    {
        "symbol": "HAVELLS",
        "company_name": "Havells India Limited",
        "isin": "INE176B01034",
        "sector_code": "INFRA",
        "sector_name": "Infrastructure & Capital Goods",
        "industry_code": "CONSUMER_ELECTRICALS",
        "industry_name": "Switchgear, Lighting, Lloyd Air Conditioning & Home Appliances",
        "base_price": 1780.0,
    },
]


def seed_market_universe(db: Session) -> int:
    """Seeds Indian equities universe and populates price history."""
    # Ensure NSE Exchange exists
    exchange = db.query(Exchange).filter(Exchange.exchange_code == "NSE").first()
    if not exchange:
        exchange = Exchange(
            exchange_id=NSE_EXCHANGE_ID,
            exchange_code="NSE",
            exchange_name="National Stock Exchange of India",
            country_code="IN",
            currency_code="INR",
        )
        db.add(exchange)
        db.flush()

    source = db.query(DataSource).filter(DataSource.source_code == "demo_source").first()
    if not source:
        source = DataSource(
            data_source_id=uuid.uuid4(),
            source_code="demo_source",
            display_name="Illustrative Indian Equities Data",
            source_type="market_data",
            is_active=True,
        )
        db.add(source)
        db.flush()

    created_securities = 0
    sim_provider = SimulatedMarketProvider()

    for item in UNIVERSE_DATA:
        # 1. Sector
        sector = db.query(Sector).filter(Sector.sector_code == item["sector_code"]).first()
        if not sector:
            sector = Sector(
                sector_id=uuid.uuid4(),
                sector_code=item["sector_code"],
                sector_name=item["sector_name"],
            )
            db.add(sector)
            db.flush()

        # 2. Industry
        industry = db.query(Industry).filter(Industry.industry_code == item["industry_code"]).first()
        if not industry:
            industry = Industry(
                industry_id=uuid.uuid4(),
                sector_id=sector.sector_id,
                industry_code=item["industry_code"],
                industry_name=item["industry_name"],
            )
            db.add(industry)
            db.flush()

        # 3. Company
        company = db.query(Company).filter(Company.legal_name == item["company_name"]).first()
        if not company:
            company = Company(
                company_id=uuid.uuid4(),
                legal_name=item["company_name"],
                common_name=item["company_name"].replace(" Limited", ""),
                country_code="IN",
            )
            db.add(company)
            db.flush()

            comp_ind = CompanyIndustry(
                company_id=company.company_id,
                industry_id=industry.industry_id,
                effective_from=date(2020, 1, 1),
            )
            db.add(comp_ind)
            db.flush()

        # 4. Security
        security = db.query(Security).filter(Security.isin == item["isin"]).first()
        if not security:
            security = Security(
                security_id=uuid.uuid4(),
                company_id=company.company_id,
                security_name=item["company_name"].replace(" Limited", " Equity"),
                isin=item["isin"],
                security_type="stock",
                currency_code="INR",
                security_status="active",
            )
            db.add(security)
            db.flush()
            created_securities += 1

        # 5. Instrument Listing
        listing = db.query(InstrumentListing).filter(InstrumentListing.symbol == item["symbol"]).first()
        if not listing:
            listing = InstrumentListing(
                listing_id=uuid.uuid4(),
                security_id=security.security_id,
                exchange_id=exchange.exchange_id,
                symbol=item["symbol"],
                trading_status="active",
            )
            db.add(listing)
            db.flush()

        # 6. Seed recent daily prices (last 30 days)
        today = date.today()
        start_date = today - timedelta(days=30)
        curr = start_date
        while curr <= today:
            if curr.weekday() < 5:
                existing_price = (
                    db.query(MarketPrice)
                    .filter(
                        MarketPrice.listing_id == listing.listing_id,
                        MarketPrice.price_date == curr,
                        MarketPrice.data_source_id == source.data_source_id,
                    )
                    .first()
                )
                if not existing_price:
                    seed_val = (hash(item["symbol"]) + curr.toordinal()) % 1000
                    delta_pct = (seed_val - 500) / 10000.0
                    close_p = round(item["base_price"] * (1.0 + delta_pct), 2)
                    high_p = round(close_p * 1.015, 2)
                    low_p = round(close_p * 0.985, 2)
                    open_p = round((high_p + low_p) / 2.0, 2)

                    p_rec = MarketPrice(
                        market_price_id=uuid.uuid4(),
                        listing_id=listing.listing_id,
                        data_source_id=source.data_source_id,
                        price_date=curr,
                        open_price=open_p,
                        high_price=high_p,
                        low_price=low_p,
                        close_price=close_p,
                        adjusted_close_price=close_p,
                        volume=25000 + (seed_val * 10),
                        currency_code="INR",
                        retrieved_at=datetime.now(),
                    )
                    db.add(p_rec)
            curr += timedelta(days=1)

    db.commit()
    return created_securities


if __name__ == "__main__":
    db = SessionLocal()
    try:
        cnt = seed_market_universe(db)
        print(f"[OK] Successfully seeded market universe ({cnt} new securities added).")
    finally:
        db.close()
