# UDIF Storage

API for storing and querying UDIF (Universal Data Interchange Format) files.

Originally built at Streamlytics, Inc. (2018). 
Open sourced under Apache 2.0.

---

## What This Does

Provides a backend storage layer for UDIF files with:

- PostgreSQL storage for UDIF data
- API key authentication
- UDIF converter integration
- Docker deployment support

---

## Stack

- Python / Flask
- PostgreSQL
- Docker

---

## Setup
```bash
docker build .
```

Configure environment variables referencing 
`configuration.development.py` and `configuration.production.py`

---

## Part of the UDIF Ecosystem

- [UDIF Specification](https://github.com/Universal-Data-Interchange-Format/udif) 
— the core standard
- [UDIF Python](https://github.com/Universal-Data-Interchange-Format/udif-python) 
— Python readers and writers
- [UDIF Data Converter](https://github.com/Universal-Data-Interchange-Format/udif-data-converter) 
— full converter application

---

## License

Apache License 2.0

---

## Inventor

UDIF was invented by [Angela Benton](https://angelabenton.com). 
Learn more at [angelabenton.com/universal-data-interchange-format-udif](https://angelabenton.com/universal-data-interchange-format-udif)
