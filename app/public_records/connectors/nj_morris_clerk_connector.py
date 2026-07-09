# ============================================================
# AUSSEM1
# PHASE 2.30 PART 1.00
# ENTERPRISE NJ MORRIS COUNTY CLERK CONNECTOR
# FILE: app/public_records/connectors/nj_morris_clerk_connector.py
# PURPOSE:
# Provide the official-source connector scaffold for Morris County,
# New Jersey Clerk / recorded-property-document public records.
#
# This connector is designed to support:
# - deed references
# - mortgage references
# - lien references
# - release/satisfaction references
# - recorded-document references
# - sale-history references where source-supported
# - owner/grantor/grantee references where source-supported
# - public-record source attribution
# - explicit unavailable/manual-review states
#
# This file does not create mock property records.
# This file does not fabricate deeds.
# This file does not fabricate mortgages.
# This file does not fabricate liens.
# This file does not fabricate sale history.
# This file does not fabricate owner conclusions.
# This file does not claim MLS active status.
# This file does not claim under-contract status.
#
# AUTHOR:
# Ryan Schuren
#
# ASSISTANT:
# Alfred
#
# STATUS:
# REAL COUNTY CLERK PUBLIC RECORD CONNECTOR FOUNDATION ACTIVE
# ============================================================


# ============================================================
# SECTION 01 - ENTERPRISE IMPORTS
# ============================================================

from __future__ import annotations

import re
from dataclasses import dataclass
from dataclasses import field
from typing import Any
from urllib.parse import quote_plus

from app.public_records.connectors.base_connector import BasePublicRecordConnector
from app.public_records.connectors.base_connector import collapse_whitespace
from app.public_records.connectors.base_connector import infer_query_mode
from app.public_records.connectors.base_connector import normalize_html_text
from app.public_records.connectors.base_connector import normalize_public_record_key
from app.public_records.connectors.base_connector import utc_now
from app.public_records.models import DeedRecord
from app.public_records.models import LienRecord
from app.public_records.models import MortgageRecord
from app.public_records.models import OwnerReferenceRecord
from app.public_records.models import ParcelIdentifier
from app.public_records.models import PublicRecordAddress
from app.public_records.models import PublicRecordConnectorResult
from app.public_records.models import PublicRecordConnectorStatus
from app.public_records.models import PublicRecordSearchRequest
from app.public_records.models import PublicRecordStatus
from app.public_records.models import RecordedDocumentReference
from app.public_records.models import RecordedDocumentType
from app.public_records.models import SaleHistoryRecord
from app.public