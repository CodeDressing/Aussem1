# ============================================================
# AUSSEM1
# PHASE 1.00 PART 2.01
# ENTERPRISE DATA PACKAGE INITIALIZATION
# FILE: app/data/__init__.py
# PURPOSE:
# Initialize the local data package for chatbot memory,
# property knowledge, and supervised training records.
#
# AUTHOR:
# Ryan Schuren
#
# ASSISTANT:
# Alfred
#
# STATUS:
# FOUNDATION ACTIVE
# ============================================================


# ============================================================
# SECTION 01 - PACKAGE METADATA
# ============================================================

DATA_PACKAGE_NAME = "Aussem1 Data Layer"

DATA_PACKAGE_VERSION = "0.1.0"

DATA_PACKAGE_PHASE = "PHASE 1.00 PART 2.01"

DATA_PACKAGE_STATUS = "foundation_active"


# ============================================================
# SECTION 02 - DATA FILE REGISTRY
# ============================================================

DATA_FILES = {
    "property_knowledge": "app/data/property_knowledge.json",
    "training_log": "app/data/training_log.json",
    "chat_memory": "app/data/chat_memory.json",
}


# ============================================================
# SECTION 03 - PACKAGE EXPORTS
# ============================================================

__all__ = [
    "DATA_PACKAGE_NAME",
    "DATA_PACKAGE_VERSION",
    "DATA_PACKAGE_PHASE",
    "DATA_PACKAGE_STATUS",
    "DATA_FILES",
]


# ============================================================
# END OF FILE
# ============================================================