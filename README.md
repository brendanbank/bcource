# bcource
Training Scheduling


https://github.com/LJPc-solutions/Nederlandse-adressen-en-postcodes/blob/main/adressen.tar.xz

To load the NL postalcode database

	LOAD DATA LOCAL INFILE '/Users/brendan/Downloads/var/www/PersonalUtils/storage/repos/postcodes/data/a' INTO TABLE bcourse.postalcodes FIELDS TERMINATED BY ',' ENCLOSED BY '"' LINES TERMINATED BY '\n' IGNORE 1 LINES;

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
	)

# issues
- Pagination
