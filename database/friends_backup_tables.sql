SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0;
SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0;
SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='TRADITIONAL,ALLOW_INVALID_DATES';

set global innodb_file_format = BARRACUDA;
SET GLOBAL innodb_file_per_table=ON;
set global innodb_large_prefix = ON;

-- -----------------------------------------------------
-- Table `friendsdb`.`post`
-- -----------------------------------------------------
DROP TABLE IF EXISTS `friendsdb`.`postb` ;

CREATE TABLE IF NOT EXISTS `friendsdb`.`postb` (
  `local_id` INT NOT NULL AUTO_INCREMENT,
  `id` VARCHAR(256) NOT NULL,
  `user_idhash` DECIMAL(25,0) NOT NULL,
  `created_time` VARCHAR(128) NULL,
  `type` VARCHAR(128) NULL,
  `story` VARCHAR(256) NULL,
  `privacy` VARCHAR(128) NULL,
  `text_length` INT NULL,
  `link` VARCHAR(512) NULL,
  `nreactions` INT NULL,
  `ncomments` INT NULL,
  `application` VARCHAR(64) NULL,
  PRIMARY KEY (`local_id`))
ENGINE = InnoDB DEFAULT CHARSET=utf8 ROW_FORMAT=DYNAMIC;


-- -----------------------------------------------------
-- Table `friendsdb`.`comment`
-- -----------------------------------------------------
DROP TABLE IF EXISTS `friendsdb`.`commentb` ;

CREATE TABLE IF NOT EXISTS `friendsdb`.`commentb` (
  `local_id` INT NOT NULL AUTO_INCREMENT,
  `id` VARCHAR(256) NOT NULL,
  `post_id` VARCHAR(256) NOT NULL,
  `user_idhash` DECIMAL(25,0) NOT NULL,
  `created_time` VARCHAR(128) NULL,
  `has_picture` TINYINT(1) NULL,
  `has_link` TINYINT(1) NULL,
  `nreactions` INT NULL,
  `ncomments` INT NULL,
  `text_lenght` INT NULL,
  PRIMARY KEY (`local_id`))
ENGINE = InnoDB DEFAULT CHARSET=utf8 ROW_FORMAT=DYNAMIC;

-- -----------------------------------------------------
-- Table `friendsdb`.`reaction`
-- -----------------------------------------------------
DROP TABLE IF EXISTS `friendsdb`.`reactionb` ;

CREATE TABLE IF NOT EXISTS `friendsdb`.`reactionb` (
  `id` INT NOT NULL AUTO_INCREMENT,
  `user_idhash` DECIMAL(25,0) NOT NULL,
  `post_id` VARCHAR(256) NOT NULL,
  `comment_id` VARCHAR(256) NULL,
  `type` VARCHAR(128) NULL,
  PRIMARY KEY (`id`))
ENGINE = InnoDB DEFAULT CHARSET=utf8 ROW_FORMAT=DYNAMIC;


-- -----------------------------------------------------
-- Table `friendsdb`.`tag`
-- -----------------------------------------------------
DROP TABLE IF EXISTS `friendsdb`.`tagb` ;

CREATE TABLE IF NOT EXISTS `friendsdb`.`tagb` (
  `id` INT NOT NULL AUTO_INCREMENT,
  `post_id` VARCHAR(256) NOT NULL,
  `comment_id` VARCHAR(256) NULL,
  `type` VARCHAR(128) NULL,
  `user_idhash` DECIMAL(25,0) NULL,
  `page_id` VARCHAR(128) NULL,
  PRIMARY KEY (`id`))
ENGINE = InnoDB DEFAULT CHARSET=utf8 ROW_FORMAT=DYNAMIC;


SET SQL_MODE=@OLD_SQL_MODE;
SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS;
SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS;
