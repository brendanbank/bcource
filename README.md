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

- **test_messages.py** - Tests for the messaging system (26 tests)
  - SystemMessage base functionality
  - SendEmail email delivery
  - HTML sanitization and rendering
  - iCalendar attachment generation
  - Attendee list email generation
  - Email templates for enrollment, waitlist, and cancellations

### Test Strategies

- **[WAITLIST_TEST_STRATEGY.md](test/WAITLIST_TEST_STRATEGY.md)** - Comprehensive functional test strategy for waitlist functionality
  - 15 functional test scenarios with detailed setup and assertions
  - 3 integration test scenarios
  - 6 edge cases and error scenarios
  - 3 performance test scenarios
  - Complete test data requirements and fixtures
  - Execution plan and success criteria

## Documentation

### Automation Guides

- **[WAITLIST_QUICK_START.md](docs/WAITLIST_QUICK_START.md)** - Quick start guide (setup in 5 minutes)
  - Essential setup commands
  - Common operations
  - Quick troubleshooting
  - Configuration examples
  - Reference table

- **[WAITLIST_AUTOMATION_GUIDE.md](docs/WAITLIST_AUTOMATION_GUIDE.md)** - Complete automation guide
  - How the AutomaticWaitList task works
  - Configuration via database and Flask-Admin
  - Testing and monitoring automation jobs
  - Troubleshooting common issues
  - Performance and scaling considerations
  - Security best practices

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
