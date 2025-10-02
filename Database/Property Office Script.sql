-- MySQL Workbench Forward Engineering

SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0;
SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0;
SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='ONLY_FULL_GROUP_BY,STRICT_TRANS_TABLES,NO_ZERO_IN_DATE,NO_ZERO_DATE,ERROR_FOR_DIVISION_BY_ZERO,NO_ENGINE_SUBSTITUTION';

-- -----------------------------------------------------
-- Schema mydb
-- -----------------------------------------------------
DROP SCHEMA IF EXISTS `mydb` ;

-- -----------------------------------------------------
-- Schema mydb
-- -----------------------------------------------------
CREATE SCHEMA IF NOT EXISTS `mydb` DEFAULT CHARACTER SET utf8 ;
USE `mydb` ;

-- -----------------------------------------------------
-- Table `mydb`.`financial`
-- -----------------------------------------------------
DROP TABLE IF EXISTS `mydb`.`financial` ;

CREATE TABLE IF NOT EXISTS `mydb`.`financial` (
  `id_financial` INT UNSIGNED NOT NULL AUTO_INCREMENT,
  `financial_date` DATETIME NOT NULL,
  `financial_amount` DECIMAL NOT NULL,
  `financial_type` VARCHAR(45) NOT NULL,
  PRIMARY KEY (`id_financial`))
ENGINE = InnoDB;


-- -----------------------------------------------------
-- Table `mydb`.`locker`
-- -----------------------------------------------------
DROP TABLE IF EXISTS `mydb`.`locker` ;

CREATE TABLE IF NOT EXISTS `mydb`.`locker` (
  `id_locker` INT UNSIGNED NOT NULL AUTO_INCREMENT,
  `locker_type` VARCHAR(45) NOT NULL,
  `locker_priority` VARCHAR(45) NULL,
  `locker_room` VARCHAR(45) NOT NULL,
  `locks` VARCHAR(45) NOT NULL,
  `locker_code` INT NOT NULL,
  PRIMARY KEY (`id_locker`))
ENGINE = InnoDB;


-- -----------------------------------------------------
-- Table `mydb`.`accessory`
-- -----------------------------------------------------
DROP TABLE IF EXISTS `mydb`.`accessory` ;

CREATE TABLE IF NOT EXISTS `mydb`.`accessory` (
  `id_accessory` INT UNSIGNED NOT NULL AUTO_INCREMENT,
  `accessory_type` VARCHAR(45) NOT NULL,
  `barcode` INT NOT NULL,
  `location` VARCHAR(60) NOT NULL,
  `brand` VARCHAR(45) NOT NULL,
  `condition` VARCHAR(45) NOT NULL,
  PRIMARY KEY (`id_accessory`))
ENGINE = InnoDB;


-- -----------------------------------------------------
-- Table `mydb`.`books`
-- -----------------------------------------------------
DROP TABLE IF EXISTS `mydb`.`books` ;

CREATE TABLE IF NOT EXISTS `mydb`.`books` (
  `id_books` INT UNSIGNED NOT NULL AUTO_INCREMENT,
  `book_type` VARCHAR(45) NOT NULL,
  `barcode` INT NOT NULL,
  `location` VARCHAR(45) NOT NULL,
  `bookscol` VARCHAR(45) NOT NULL,
  `quantity` INT UNSIGNED NOT NULL,
  `condition` VARCHAR(60) NOT NULL,
  `book_name` VARCHAR(45) NOT NULL,
  `author` VARCHAR(45) NOT NULL,
  `last_inventoried` DATETIME NULL,
  PRIMARY KEY (`id_books`))
ENGINE = InnoDB;


-- -----------------------------------------------------
-- Table `mydb`.`instrument`
-- -----------------------------------------------------
DROP TABLE IF EXISTS `mydb`.`instrument` ;

CREATE TABLE IF NOT EXISTS `mydb`.`instrument` (
  `id_instrument` INT UNSIGNED NOT NULL AUTO_INCREMENT,
  `instrument_type` VARCHAR(45) NOT NULL,
  `instrument_section` VARCHAR(45) NOT NULL,
  `instrument_barcode` INT NOT NULL,
  `instrument_call_number` VARCHAR(45) NOT NULL,
  `instrument_serial_number` VARCHAR(45) NOT NULL,
  `instrument_asset_tag` VARCHAR(45) NOT NULL,
  `instrument_make` VARCHAR(45) NOT NULL,
  `instrument_model` VARCHAR(45) NOT NULL,
  `instrument_location` VARCHAR(60) NOT NULL,
  `instrument_condition` VARCHAR(60) NULL,
  `last_inventory` DATETIME NULL,
  `last_cleaned` DATETIME NULL,
  `instrument_notes` VARCHAR(60) NULL,
  PRIMARY KEY (`id_instrument`))
ENGINE = InnoDB;


-- -----------------------------------------------------
-- Table `mydb`.`user`
-- -----------------------------------------------------
DROP TABLE IF EXISTS `mydb`.`user` ;

CREATE TABLE IF NOT EXISTS `mydb`.`user` (
  `id_user` INT UNSIGNED NOT NULL AUTO_INCREMENT,
  `f_name` VARCHAR(60) NOT NULL,
  `l_name` VARCHAR(60) NOT NULL,
  `I_num` INT NOT NULL,
  `Role` VARCHAR(60) NOT NULL,
  `usercol` VARCHAR(45) NOT NULL,
  PRIMARY KEY (`id_user`))
ENGINE = InnoDB;


-- -----------------------------------------------------
-- Table `mydb`.`keys_locks`
-- -----------------------------------------------------
DROP TABLE IF EXISTS `mydb`.`keys_locks` ;

CREATE TABLE IF NOT EXISTS `mydb`.`keys_locks` (
  `id_keys_locks` INT UNSIGNED NOT NULL AUTO_INCREMENT,
  `locks_new_number` INT NOT NULL,
  `locks_old_number` INT NULL,
  `combination` VARCHAR(45) NOT NULL,
  `barcode` INT NOT NULL,
  `locker_id_locker` INT UNSIGNED NOT NULL,
  PRIMARY KEY (`id_keys_locks`),
  INDEX `fk_keys_locks_locker1_idx` (`locker_id_locker` ASC) VISIBLE,
  CONSTRAINT `fk_keys_locks_locker1`
    FOREIGN KEY (`locker_id_locker`)
    REFERENCES `mydb`.`locker` (`id_locker`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION)
ENGINE = InnoDB;


-- -----------------------------------------------------
-- Table `mydb`.`method`
-- -----------------------------------------------------
DROP TABLE IF EXISTS `mydb`.`method` ;

CREATE TABLE IF NOT EXISTS `mydb`.`method` (
  `id_method` INT UNSIGNED NOT NULL AUTO_INCREMENT,
  `accessory_id_accessory` INT UNSIGNED NOT NULL,
  `books_id_books` INT UNSIGNED NOT NULL,
  `instrument_id_instrument` INT UNSIGNED NOT NULL,
  `user_id_user` INT UNSIGNED NOT NULL,
  `keys_locks_id_keys_locks` INT UNSIGNED NOT NULL,
  PRIMARY KEY (`id_method`),
  INDEX `fk_method_accessory1_idx` (`accessory_id_accessory` ASC) VISIBLE,
  INDEX `fk_method_books1_idx` (`books_id_books` ASC) VISIBLE,
  INDEX `fk_method_instrument1_idx` (`instrument_id_instrument` ASC) VISIBLE,
  INDEX `fk_method_user1_idx` (`user_id_user` ASC) VISIBLE,
  INDEX `fk_method_keys_locks1_idx` (`keys_locks_id_keys_locks` ASC) VISIBLE,
  CONSTRAINT `fk_method_accessory1`
    FOREIGN KEY (`accessory_id_accessory`)
    REFERENCES `mydb`.`accessory` (`id_accessory`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION,
  CONSTRAINT `fk_method_books1`
    FOREIGN KEY (`books_id_books`)
    REFERENCES `mydb`.`books` (`id_books`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION,
  CONSTRAINT `fk_method_instrument1`
    FOREIGN KEY (`instrument_id_instrument`)
    REFERENCES `mydb`.`instrument` (`id_instrument`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION,
  CONSTRAINT `fk_method_user1`
    FOREIGN KEY (`user_id_user`)
    REFERENCES `mydb`.`user` (`id_user`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION,
  CONSTRAINT `fk_method_keys_locks1`
    FOREIGN KEY (`keys_locks_id_keys_locks`)
    REFERENCES `mydb`.`keys_locks` (`id_keys_locks`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION)
ENGINE = InnoDB;


-- -----------------------------------------------------
-- Table `mydb`.`financial_books_instrument_user_accessory_locker`
-- -----------------------------------------------------
DROP TABLE IF EXISTS `mydb`.`financial_books_instrument_user_accessory_locker` ;

CREATE TABLE IF NOT EXISTS `mydb`.`financial_books_instrument_user_accessory_locker` (
  `id_method_books` INT UNSIGNED NOT NULL AUTO_INCREMENT,
  `financial_id_financial` INT UNSIGNED NOT NULL,
  `user_id_user` INT UNSIGNED NOT NULL,
  `accessory_id_accessory` INT UNSIGNED NOT NULL,
  `locker_id_locker` INT UNSIGNED NOT NULL,
  `books_id_books` INT UNSIGNED NOT NULL,
  `instrument_id_instrument` INT UNSIGNED NOT NULL,
  PRIMARY KEY (`id_method_books`),
  INDEX `fk_financial_method_book_instrument_user_accessory_locker_f_idx` (`financial_id_financial` ASC) VISIBLE,
  INDEX `fk_financial_method_book_instrument_user_accessory_locker_u_idx` (`user_id_user` ASC) VISIBLE,
  INDEX `fk_financial_method_book_instrument_user_accessory_locker_a_idx` (`accessory_id_accessory` ASC) VISIBLE,
  INDEX `fk_financial_method_book_instrument_user_accessory_locker_l_idx` (`locker_id_locker` ASC) VISIBLE,
  INDEX `fk_financial_method_book_instrument_user_accessory_locker_b_idx` (`books_id_books` ASC) VISIBLE,
  INDEX `fk_financial_method_books_instrument_user_accessory_locker__idx` (`instrument_id_instrument` ASC) VISIBLE,
  CONSTRAINT `fk_financial_method_book_instrument_user_accessory_locker_fin`
    FOREIGN KEY (`financial_id_financial`)
    REFERENCES `mydb`.`financial` (`id_financial`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION,
  CONSTRAINT `fk_financial_method_book_instrument_user_accessory_locker_user1`
    FOREIGN KEY (`user_id_user`)
    REFERENCES `mydb`.`user` (`id_user`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION,
  CONSTRAINT `fk_financial_method_book_instrument_user_accessory_locker_acc1`
    FOREIGN KEY (`accessory_id_accessory`)
    REFERENCES `mydb`.`accessory` (`id_accessory`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION,
  CONSTRAINT `fk_financial_method_book_instrument_user_accessory_locker_loc1`
    FOREIGN KEY (`locker_id_locker`)
    REFERENCES `mydb`.`locker` (`id_locker`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION,
  CONSTRAINT `fk_financial_method_book_instrument_user_accessory_locker_boo1`
    FOREIGN KEY (`books_id_books`)
    REFERENCES `mydb`.`books` (`id_books`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION,
  CONSTRAINT `fk_financial_method_books_instrument_user_accessory_locker_in1`
    FOREIGN KEY (`instrument_id_instrument`)
    REFERENCES `mydb`.`instrument` (`id_instrument`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION)
ENGINE = InnoDB;


SET SQL_MODE=@OLD_SQL_MODE;
SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS;
SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS;
