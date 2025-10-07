# bcource
Training Scheduling

## Testing

Run the test suite:

```bash
# Run all tests
cd test
../.venv/bin/python -m unittest discover -v

# Run specific test module
cd test
../.venv/bin/python -m unittest test_automation -v

# Run specific test class
cd test
../.venv/bin/python -m unittest test_automation.TestAutomationRegistry -v

# Run specific test method
cd test
../.venv/bin/python -m unittest test_automation.TestAutomationRegistry.test_register_automation_basic -v
```

### Test Coverage

- **test_automation.py** - Tests for the automation system (21 tests)
  - Automation registration and retrieval
  - BaseAutomationTask functionality
  - Job creation and scheduling
  - Task execution

## Database Setup

### Postal Code Database

https://github.com/LJPc-solutions/Nederlandse-adressen-en-postcodes/blob/main/adressen.tar.xz

```bash
mysql --local-infile=1  -p -u root postalcodes
```

```sql
SET GLOBAL local_infile=1;
```

To load the NL postalcode database:

```sql
LOAD DATA LOCAL INFILE 'var/www/PersonalUtils/storage/repos/postcodes/data/adressen.csv' INTO TABLE postalcodes.postalcodes FIELDS TERMINATED BY ',' ENCLOSED BY '"' LINES TERMINATED BY '\n' IGNORE 1 LINES;

CREATE TABLE postalcodes (
	postcode VARCHAR(32) NOT NULL,
	huisnummer VARCHAR(32) NOT NULL,
	straat VARCHAR(256) NOT NULL,
	buurt VARCHAR(256) NOT NULL,
	wijk VARCHAR(256) NOT NULL,
	woonplaats VARCHAR(256) NOT NULL,
	gemeente VARCHAR(256) NOT NULL,
	provincie VARCHAR(256) NOT NULL,
	latitude DOUBLE NOT NULL,
	longitude DOUBLE NOT NULL,
	PRIMARY KEY (postcode, huisnummer)
);
```

### Database Migrations

Upgrade databases:

```bash
flask db init --multidb
flask db migrate -m "postalcodes.v2"
flask db upgrade
```

## Known Issues

- Pagination
