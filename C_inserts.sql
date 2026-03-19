USE mydb;
INSERT INTO instrument VALUES(instrument_type, instrument_section, instrument_barcode, instrument_call_number, instrument_serial_number, instrument_asset_tag, instrument_make, instrument_model, instrument_model, instrument_model, instrument_location, instrument_condition, last_inventory, last_cleaned, instrument_notes);


INSERT INTO books VALUES(book_type, barcode, location, bookscol, quantity, `condition`, book_name, author, last_inventory);


INSERT INTO financial VALUES(financial_date, financial_amount, financial_type);


INSERT INTO accessory VALUES(accessory_type, barcode, location, brand, `condition`);


INSERT INTO locker VALUES(locker_type, locker_priority, llocker_room, `locks`, locker_code);


INSERT INTO `user` VALUES(f_name, l_name, I_num, `Role`, usercol);


INSERT INTO keys_locks VALUES(locks_new_number, locks_old_number, combination, barcode)