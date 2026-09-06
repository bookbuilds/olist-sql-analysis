# Acquire the exact Olist inputs

Download **Brazilian E-Commerce Public Dataset by Olist** from [Olist on Kaggle](https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce). The original execution used the [official archive endpoint](https://www.kaggle.com/api/v1/datasets/download/olistbr/brazilian-ecommerce) anonymously. This package provides no downloader and stores no authenticated or signed URL.

Recorded acquisition: **2026-09-06**. Metadata: `currentVersionNumber=2`, `lastUpdated=2021-10-01T19:08:27.97Z`, notes `Data Update 2021/10/01`. The historical list also contains version 7 and an older version 2; do not assume a clean version sequence. [Selected source metadata](../evidence/source_metadata.json) preserves that ambiguity.

Expected archive: **44,717,580 bytes**, SHA-256 `967e41e04fc306fe604e2a693f488995a8b41e5047418f8a5c8e4abd6deca784`. Extract without modifying CSV bytes. Put the following nine files directly under `data/raw/` (ignored by Git), or use `--data /path/to/olist-data` with an external folder.

| Filename | Bytes | Data rows | SHA-256 |
|---|---:|---:|---|
| `olist_customers_dataset.csv` | 9,033,957 | 99,441 | `983a422239e1712ded753b3bf9ecf47dc73f144d306029dcfa99e70a226883d2` |
| `olist_geolocation_dataset.csv` | 61,273,883 | 1,000,163 | `b514f6fc991b9566aeba02aa5d67e2c3630f034b60a0e05aa0d082a3b66d88d6` |
| `olist_order_items_dataset.csv` | 15,438,671 | 112,650 | `0bc4d068c4fe38cbb01bd90e8746e3c613fe7b4baef75fab7b0e329701c3e279` |
| `olist_order_payments_dataset.csv` | 5,777,138 | 103,886 | `4f713964f2815dbbaa40b9488268c55aac3627bfce5aa96cf58d1f3616de3cc0` |
| `olist_order_reviews_dataset.csv` | 14,451,670 | 99,224 | `012b61c7593e34f51fa614efdf802b9c7056ce6aae5307ddb93236e7cfc797d7` |
| `olist_orders_dataset.csv` | 17,654,914 | 99,441 | `8df58ef3d2d7e9944010f7beecd9b75367f5588ec6e3c91cec19ae3345ef9ecf` |
| `olist_products_dataset.csv` | 2,379,446 | 32,951 | `3e6569628a17fbc75fd206ee357b59e20364b9afa90f5b6cd5b4d624c58aa9cc` |
| `olist_sellers_dataset.csv` | 174,703 | 3,095 | `1f643d2b950373b85735e7794b20986f528d7a000432e7c6f9bcbb44d0846a0e` |
| `product_category_name_translation.csv` | 2,613 | 71 | `a81f0d1f27b27e7293f761bc79e3ce8f348ee39c4b3ed3e49bde38f478586278` |

Row counts exclude CSV headers and count parsed records, including quoted multiline review text correctly. No raw records are stored in the [input manifest](../evidence/input_manifest.json).

The audit, import CLI and full pipeline verify all nine byte sizes and hashes before processing. A mismatch stops execution. If the source changes version, audit it again and deliberately record a new manifest before analysis; do not silently accept it or reuse the old narrative. The `--manifest` option in the audit/import CLIs is for an explicitly reviewed alternative extract; snapshot verification and the report remain locked to this package's original hashes.

No archive, raw CSV or database belongs in this repository. This is a size/duplication/license-maintenance packaging choice, not a claim that CC BY-NC-SA 4.0 prohibits redistribution. See [third-party data notice](../THIRD_PARTY_DATA.md) for attribution, noncommercial/share-alike conditions, uncertainty about portfolio use, and the separate undecided source-code license.
