-- -------------------------------------------------
-- DROP Statements
-- -------------------------------------------------
DROP TABLE IF EXISTS financial;
DROP TABLE IF EXISTS locker;
DROP TABLE IF EXISTS accessory;
DROP TABLE IF EXISTS books;
DROP TABLE IF EXISTS instrument;
DROP TABLE IF EXISTS user;
DROP TABLE IF EXISTS keys_locks;
DROP TABLE IF EXISTS method;
DROP TABLE IF EXISTS rental;

-- -----------------------------------------------------
-- Table Financial
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS financial (
    financial_id SERIAL
    , financial_date TIMESTAMP NOT NULL
    , financial_amount REAL NOT NULL
    , financial_type CHARACTER VARYING NOT NULL
    , CONSTRAINT financial_pkey PRIMARY KEY (financial_id)
);

-- -----------------------------------------------------
-- Table Locker
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS locker (
    locker_id SERIAL
    , locker_type CHARACTER VARYING NOT NULL
    , locker_priority CHARACTER VARYING NULL
    , locker_room CHARACTER VARYING NOT NULL
    , locks CHARACTER VARYING NOT NULL
    , locker_code INTEGER NOT NULL
    , CONSTRAINT locker_pkey PRIMARY KEY (locker_id)
);

-- -----------------------------------------------------
-- Table Accessory
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS accessory (
    accessory_id SERIAL
    , accessory_type CHARACTER VARYING NOT NULL
    , barcode INTEGER NOT NULL
    , location CHARACTER VARYING NOT NULL
    , brand CHARACTER VARYING NOT NULL
    , condition CHARACTER VARYING NOT NULL
    , CONSTRAINT accessory_pkey PRIMARY KEY (accessory_id)
);

-- -----------------------------------------------------
-- Table Books
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS books (
    books_id SERIAL
    , book_type CHARACTER VARYING NOT NULL
    , barcode INTEGER NOT NULL
    , location CHARACTER VARYING NOT NULL
    , bookscol CHARACTER VARYING NOT NULL
    , quantity INTEGER NOT NULL
    , condition CHARACTER VARYING NOT NULL
    , book_name CHARACTER VARYING NOT NULL
    , author CHARACTER VARYING NOT NULL
    , last_inventoried TIMESTAMP NULL
    , CONSTRAINT books_pkey PRIMARY KEY (books_id)
);

-- -----------------------------------------------------
-- Table Instrument
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS instrument (
    instrument_id SERIAL
    , instrument_type CHARACTER VARYING NOT NULL
    , instrument_section CHARACTER VARYING NOT NULL
    , instrument_barcode INTEGER NOT NULL
    , instrument_call_number CHARACTER VARYING NOT NULL
    , instrument_serial_number CHARACTER VARYING NOT NULL
    , instrumnet_asset_tag CHARACTER VARYING NOT NULL
    , instrument_make CHARACTER VARYING NOT NULL
    , instrument_model CHARACTER VARYING NOT NULL
    , instrument_location CHARACTER VARYING NOT NULL
    , instrument_condition CHARACTER VARYING NOT NULL
    , instrument_last_inventoried TIMESTAMP NULL
    , instrument_last_cleaned TIMESTAMP NULL
    , instrument_notes CHARACTER VARYING NULL
    , CONSTRAINT instrument_pkey PRIMARY KEY (instrument_id)
);

-- -----------------------------------------------------
-- Table User
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS public.user (
    user_id SERIAL
    , user_first_name CHARACTER VARYING NOT NULL
    , user_last_name CHARACTER VARYING NOT NULL
    , user_i_number INTEGER NOT NULL
    , user_role CHARACTER VARYING NOT NULL
    , CONSTRAINT user_pkey PRIMARY KEY (user_id)
);

-- -----------------------------------------------------
-- Table Keys_Locks
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS keys_locks (
    keys_locks_id SERIAL
    , keys_locks_new_number INTEGER NOT NULL
    , keys_locks_old_number INTEGER NOT NULL
    , keys_locks_combination CHARACTER VARYING NOT NULL
    , keys_locks_barcode INTEGER NOT NULL
    , locker_id INTEGER NOT NULL
    , CONSTRAINT keys_locks_pkey PRIMARY KEY (keys_locks_id)
    , CONSTRAINT keys_locks_fk1
        FOREIGN KEY (locker_id)
        REFERENCES locker (locker_id)
        ON DELETE CASCADE
        ON UPDATE CASCADE
);

-- -----------------------------------------------------
-- Table Method
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS method (
    method_id SERIAL
    , accessory_id INTEGER NOT NULL
    , books_id INTEGER NOT NULL
    , instrument_id INTEGER NOT NULL
    , user_id INTEGER NOT NULL
    , keys_locks_id INTEGER NOT NULL
    , CONSTRAINT method_pkey PRIMARY KEY (method_id)
    , CONSTRAINT method_fk1
        FOREIGN KEY (accessory_id)
        REFERENCES accessory (accessory_id)
        ON DELETE CASCADE
        ON UPDATE CASCADE
    , CONSTRAINT method_fk2
        FOREIGN KEY (books_id)
        REFERENCES books (books_id)
        ON DELETE CASCADE
        ON UPDATE CASCADE
    , CONSTRAINT method_fk3
        FOREIGN KEY (instrument_id)
        REFERENCES instrument (instrument_id)
        ON DELETE CASCADE
        ON UPDATE CASCADE
    , CONSTRAINT method_fk4
        FOREIGN KEY (user_id)
        REFERENCES public.user (user_id)
        ON DELETE CASCADE
        ON UPDATE CASCADE
    , CONSTRAINT method_fk5
        FOREIGN KEY (keys_locks_id)
        REFERENCES keys_locks (keys_locks_id)
        ON DELETE CASCADE
        ON UPDATE CASCADE
);

-- -----------------------------------------------------
-- Table Rental
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS rental (
    rental_id SERIAL
    , financial_id INTEGER NOT NULL
    , user_id INTEGER NOT NULL
    , accessory_id INTEGER NOT NULL
    , locker_id INTEGER NOT NULL
    , books_id INTEGER NOT NULL
    , instrument_id INTEGER NOT NULL
    , rental_date TIMESTAMP NOT NULL
    , return_date TIMESTAMP NULL
    , CONSTRAINT rental_pkey PRIMARY KEY (rental_id)
    , CONSTRAINT rental_fk1
        FOREIGN KEY (financial_id)
        REFERENCES financial (financial_id)
        ON DELETE CASCADE
        ON UPDATE CASCADE
    , CONSTRAINT rental_fk2
        FOREIGN KEY (user_id)
        REFERENCES public.user (user_id)
        ON DELETE CASCADE
        ON UPDATE CASCADE
    , CONSTRAINT rental_fk3
        FOREIGN KEY (accessory_id)
        REFERENCES accessory (accessory_id)
        ON DELETE CASCADE
        ON UPDATE CASCADE
    , CONSTRAINT rental_fk4
        FOREIGN KEY (locker_id)
        REFERENCES locker (locker_id)
        ON DELETE CASCADE
        ON UPDATE CASCADE
    , CONSTRAINT rental_fk5
        FOREIGN KEY (books_id)
        REFERENCES books (books_id)
        ON DELETE CASCADE
        ON UPDATE CASCADE
    , CONSTRAINT rental_fk6
        FOREIGN KEY (instrument_id)
        REFERENCES instrument (instrument_id)
        ON DELETE CASCADE
        ON UPDATE CASCADE
);