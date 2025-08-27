---
title: "Synevyr Public Data API"
date: "2025-08-13"
slug: "synevyr-public-data"
excerpt: "Access Synevyr’s public datasets without authentication."
thumbnail: "/documentation/synevyr-open-data.jpeg"
---

---

### 🚀 TL;DR

These endpoints are **public** — no authentication or API keys required.

Example:  
```bash
curl "https://api.synevyr.org/public/user_customers?page=1&page_size=50"
```

---

## 🌐 What Is the Synevyr Public Data API?

The **Synevyr Public Data API** provides open datasets you can query directly without signing in or using API tokens.  
Data is paginated for efficient retrieval.

---

## 🛠️ Available Endpoints

### 1. `/public/user_customers`
Returns customer records for demonstration and analytics purposes.

```bash
GET /public/user_customers?page=1&page_size=50
```

**Example Response:**
```json
{
  "table": "user_customers",
  "page": 1,
  "page_size": 50,
  "total_pages": 4,
  "total_items": 200,
  "data": [
    { "id": 1, "name": "John Doe", "email": "john@example.com" }
  ]
}
```

---

### 2. `/public/meta_leads`
Contains marketing lead data from the Synevyr sample dataset.

```bash
GET /public/meta_leads?page=1&page_size=50
```

---

### 3. `/public/wc_orders`
Contains e-commerce order data for testing and sample reporting.

```bash
GET /public/wc_orders?page=1&page_size=50
```

---

## ⚠️ Empty Dataset Behavior

If a table has **no data**, the API returns a usage block with:

- Example queries
- Allowed parameters
- Message indicating no data is present

Example:
```json
{
  "message": "No data available in table 'meta_leads'.",
  "usage": {
    "endpoint": "/public/meta_leads",
    "method": "GET",
    "parameters": {
      "page": "Page number. Default 1.",
      "page_size": "Rows per page. Default 50. Max 500.",
      "table": ["meta_leads", "wc_orders"]
    },
    "examples": [
      "https://api.synevyr.org/public/analytics?table=meta_leads&page=1&page_size=50",
    ]
  }
}
```

---

## 🔗 Helpful Links

- [JSON Specification](https://www.json.org/json-en.html)
- [Pagination Best Practices](https://developer.mozilla.org/en-US/docs/Web/API/URLSearchParams)

---

## 📩 Need Help?

Email [info@carpathian.ai](mailto:info@carpathian.ai) with questions.  
For large-scale data exports, contact our support team.

---
