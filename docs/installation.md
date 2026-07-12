# Installation

## Prerequisites

- Python 3.10+
- Git

## Clone the Repository

```bash
git clone https://github.com/developer-hub/developer-hub.git
cd developer-hub
```

## Install Dependencies

```bash
pip install -r scripts/requirements.txt
```

## Validate the Repository

```bash
python scripts/validate.py
```

## Build the Search Index

```bash
python scripts/build_index.py
```

## Run AI Categorization

```bash
python scripts/ai_categorize.py --input new-entries/
```

## Verify Everything

```bash
python scripts/validate.py
python scripts/build_index.py
```
