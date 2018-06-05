DROP DATABASE IF EXISTS powerdns;
CREATE DATABASE powerdns;

GRANT ALL PRIVILEGES ON powerdns.* TO 'powerdns'@'localhost' IDENTIFIED BY 'powerdnsPassword';

USE powerdns;

CREATE TABLE domains (
  `id` INT auto_increment,
  `name` VARCHAR(255) NOT NULL,
  `master` VARCHAR(128) DEFAULT NULL,
  `last_check` INT DEFAULT NULL,
  `type` VARCHAR(6) NOT NULL,
  `notified_serial` INT DEFAULT NULL,
  `account` VARCHAR(40) DEFAULT NULL,
  PRIMARY KEY (`id`)
);

CREATE UNIQUE INDEX name_index ON domains(`name`);

CREATE TABLE records (
  `id` INT auto_increment,
  `domain_id` INT DEFAULT NULL,
  `name` VARCHAR(255) DEFAULT NULL,
  `type` VARCHAR(6) DEFAULT NULL,
  `content` VARCHAR(255) DEFAULT NULL,
  `ttl` INT DEFAULT NULL,
  `prio` INT DEFAULT NULL,
  `change_date` INT DEFAULT NULL,
  `disabled` tinyint(1) DEFAULT NULL,
  `ordername` varchar(255) DEFAULT NULL,
  `auth` tinyint(1) DEFAULT NULL,
  PRIMARY KEY (`id`)
);

CREATE INDEX rec_name_index ON records(`name`);
CREATE INDEX nametype_index ON records(`name`, `type`);
CREATE INDEX domain_id ON records(`domain_id`);

CREATE TABLE supermasters (
  `ip` VARCHAR(25) NOT NULL,
  `nameserver` VARCHAR(255) NOT NULL,
  `account` VARCHAR(40) DEFAULT NULL
);

CREATE TABLE IF NOT EXISTS `records_add` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `domain_id` int(11) DEFAULT NULL,
  `name` varchar(255) DEFAULT NULL,
  `type` varchar(10) DEFAULT NULL,
  `content` varchar(64000) DEFAULT NULL,
  `ttl` int(11) DEFAULT NULL,
  `prio` int(11) DEFAULT NULL,
  `change_date` int(11) DEFAULT NULL,
  `disabled` tinyint(1) DEFAULT NULL,
  `ordername` varchar(255) DEFAULT NULL,
  `auth` tinyint(1) DEFAULT NULL,
  PRIMARY KEY (`id`)
);

CREATE TABLE IF NOT EXISTS `records_remove` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `domain_id` int(11) DEFAULT NULL,
  `name` varchar(255) DEFAULT NULL,
  `type` varchar(10) DEFAULT NULL,
  `content` varchar(64000) DEFAULT NULL,
  `ttl` int(11) DEFAULT NULL,
  `prio` int(11) DEFAULT NULL,
  `change_date` int(11) DEFAULT NULL,
  `disabled` tinyint(1) DEFAULT NULL,
  `ordername` varchar(255) DEFAULT NULL,
  `auth` tinyint(1) DEFAULT NULL,
  PRIMARY KEY (`id`)
);


CREATE TRIGGER TRG_RecordsDeleteClean
BEFORE DELETE ON records
FOR EACH ROW
  DELETE FROM records_remove WHERE id = OLD.id LIMIT 1;

CREATE TRIGGER TRG_RecordsDelete
AFTER DELETE ON records
FOR EACH ROW
  INSERT INTO records_remove
      VALUES (OLD.id, OLD.domain_id, OLD.name, OLD.type, OLD.content, OLD.ttl, OLD.prio, (SELECT DATE_FORMAT(NOW(), "%Y%m%d%H")), OLD.disabled, OLD.ordername, OLD.auth); 

DELIMITER //

CREATE TRIGGER TRG_RecordsUpdateClean
BEFORE UPDATE ON records
FOR EACH ROW BEGIN
  DELETE FROM records_remove WHERE id = OLD.id LIMIT 1;
  DELETE FROM records_add WHERE id = OLD.id LIMIT 1;
END

//

DELIMITER ;

DELIMITER //

CREATE TRIGGER TRG_RecordsUpdate
AFTER UPDATE ON records
FOR EACH ROW BEGIN
  INSERT INTO records_add
      VALUES (NEW.id, NEW.domain_id, NEW.name, NEW.type, NEW.content, NEW.ttl, NEW.prio, (SELECT DATE_FORMAT(NOW(), "%Y%m%d%H")), NEW.disabled, NEW.ordername, NEW.auth);
  INSERT INTO records_remove
      VALUES (OLD.id, OLD.domain_id, OLD.name, OLD.type, OLD.content, OLD.ttl, OLD.prio, (SELECT DATE_FORMAT(NOW(), "%Y%m%d%H")), OLD.disabled, OLD.ordername, OLD.auth); 
END

//

DELIMITER ;

CREATE TRIGGER TRG_RecordsInsert
AFTER INSERT ON records
FOR EACH ROW
  INSERT INTO records_add
      VALUES (NEW.id, NEW.domain_id, NEW.name, NEW.type, NEW.content, NEW.ttl, NEW.prio, (SELECT DATE_FORMAT(NOW(), "%Y%m%d%H")), NEW.disabled, NEW.ordername, NEW.auth); 

CREATE USER
  'python_usr'@'localhost' IDENTIFIED BY 'python_usr_pass';
  
GRANT SELECT ON `powerdns`.`records` TO 'python_usr'@'localhost';
GRANT ALL PRIVILEGES ON `powerdns`.`records_remove` TO 'python_usr'@'localhost';
GRANT ALL PRIVILEGES ON `powerdns`.`records_add` TO 'python_usr'@'localhost';