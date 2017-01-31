
CREATE DATABASE IF NOT EXISTS MOOCdb_XXXXX;
USE MOOCdb_XXXXX;

/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8 */;
/*!40103 SET @OLD_TIME_ZONE=@@TIME_ZONE */;
/*!40103 SET TIME_ZONE='+00:00' */;
/*!40014 SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0 */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;
/*!40111 SET @OLD_SQL_NOTES=@@SQL_NOTES, SQL_NOTES=0 */;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;

DROP TABLE IF EXISTS users;
DROP TABLE IF EXISTS assessments;
DROP TABLE IF EXISTS submissions;
DROP TABLE IF EXISTS problems;
DROP TABLE IF EXISTS problem_types;
DROP TABLE IF EXISTS observed_events;
DROP TABLE IF EXISTS resources_urls;
DROP TABLE IF EXISTS resources;
DROP TABLE IF EXISTS resource_types;
DROP TABLE IF EXISTS urls;
DROP TABLE IF EXISTS agent;
DROP TABLE IF EXISTS os;

-- OS types table
CREATE TABLE os (
  os_id int(11) NOT NULL PRIMARY KEY,
  os_name varchar(255) DEFAULT NULL
) ENGINE=InnoDB;

-- Agent types table
CREATE TABLE agent (
  agent_id int(11) NOT NULL PRIMARY KEY,
  agent_name varchar(255) DEFAULT NULL
) ENGINE=InnoDB;

-- urls types table
CREATE TABLE urls (
  url_id int(11) NOT NULL PRIMARY KEY,
  url varchar(255) DEFAULT NULL
) ENGINE=InnoDB;

-- resource types table
CREATE TABLE resource_types (
  resource_type_id int(11) NOT NULL PRIMARY KEY,
  resource_type_content varchar(40) NOT NULL,
  resource_type_medium varchar(40) NOT NULL
) ENGINE=InnoDB;

-- resources table
CREATE TABLE resources (
  resource_id int(11) NOT NULL PRIMARY KEY,
  resource_name varchar(555) NULL,
  resource_uri varchar(555) NULL,
  resource_type_id int(2) NOT NULL,
  resource_parent_id int(11) DEFAULT NULL,
  resource_child_number int(11) DEFAULT NULL,
  resource_relevant_week int(11) DEFAULT NULL,
  resource_release_date date DEFAULT NULL,
  FOREIGN KEY(resource_type_id) REFERENCES resource_types(resource_type_id) ON DELETE CASCADE,
  FOREIGN KEY(resource_parent_id) REFERENCES resources(resource_id) ON DELETE CASCADE
) ENGINE=InnoDB;

-- resources urls table
CREATE TABLE resources_urls (
  resources_urls_id int(11) NOT NULL PRIMARY KEY,
  resource_id int(11) NOT NULL,
  url_id int(11) NOT NULL,
  FOREIGN KEY(resource_id) REFERENCES resources(resource_id) ON DELETE CASCADE,
  FOREIGN KEY(url_id) REFERENCES urls(url_id) ON DELETE CASCADE
) ENGINE=InnoDB;

-- observed events table
CREATE TABLE observed_events (
  observed_event_id char(36) NOT NULL PRIMARY KEY,
  user_id char(40) NOT NULL,
  url_id int(11) NOT NULL,
  observed_event_timestamp datetime NOT NULL,
  observed_event_duration int(11) DEFAULT NULL,
  observed_event_ip char(3) DEFAULT NULL,
  observed_event_os int(11) DEFAULT NULL,
  observed_event_agent int(11) DEFAULT NULL,
  observed_event_type_id varchar(255) NOT NULL,
  FOREIGN KEY(url_id) REFERENCES resources(resource_id) ON DELETE CASCADE,
  FOREIGN KEY(observed_event_os) REFERENCES os(os_id) ON DELETE CASCADE,
  FOREIGN KEY(observed_event_agent) REFERENCES agent(agent_id) ON DELETE CASCADE
) ENGINE=InnoDB;

-- problem types table
CREATE TABLE problem_types (
  problem_type_id int(10) NOT NULL PRIMARY KEY,
  problem_type_name varchar(255) NOT NULL
) ENGINE=InnoDB;

-- problems table
CREATE TABLE problems (
  problem_id int(11) NOT NULL PRIMARY KEY,
  problem_name varchar(127) NOT NULL,
  problem_parent_id int(11) DEFAULT NULL,
  problem_child_number int(11) DEFAULT NULL,
  problem_type_id int(11) NOT NULL,
  problem_release_timestamp datetime DEFAULT NULL,
  problem_soft_deadline datetime DEFAULT NULL,
  problem_hard_deadline datetime DEFAULT NULL,
  problem_max_submission int(11) DEFAULT NULL,
  problem_max_duration int(11) DEFAULT NULL,
  problem_weight int(11) DEFAULT NULL,
  resource_id int(11) DEFAULT NULL,
  FOREIGN KEY(problem_parent_id) REFERENCES problems(problem_id) ON DELETE CASCADE,
  FOREIGN KEY(problem_type_id) REFERENCES problem_types(problem_type_id) ON DELETE CASCADE,
  FOREIGN KEY(resource_id) REFERENCES resources(resource_id) ON DELETE CASCADE
) ENGINE=InnoDB;

-- submissions table
CREATE TABLE submissions (
  submission_id char(36) NOT NULL PRIMARY KEY,
  user_id char(40) NOT NULL,
  problem_id int(11) NOT NULL,
  submission_timestamp datetime NOT NULL,
  submission_attempt_number int(11) NOT NULL,
  submission_answer text NOT NULL,
  submission_is_submitted int(1) NOT NULL,
  submission_ip char(3) DEFAULT NULL,
  submission_os int(11) DEFAULT NULL,
  submission_agent int(11) DEFAULT NULL,
  FOREIGN KEY(problem_id) REFERENCES problems(problem_id) ON DELETE CASCADE,
  FOREIGN KEY(submission_os) REFERENCES os(os_id) ON DELETE CASCADE,
  FOREIGN KEY(submission_agent) REFERENCES agent(agent_id) ON DELETE CASCADE
) ENGINE=InnoDB;

-- assessments table
CREATE TABLE assessments (
  assessment_id char(36) NOT NULL PRIMARY KEY,
  submission_id char(36) NOT NULL,
  assessment_feedback text,
  assessment_grade double DEFAULT NULL,
  assessment_grade_with_penalty double DEFAULT NULL,
  assessment_grader_id varchar(63) NOT NULL,
  assessment_timestamp datetime DEFAULT NULL,
  FOREIGN KEY(submission_id) REFERENCES submissions(submission_id) ON DELETE CASCADE
) ENGINE=InnoDB;

-- user table
CREATE TABLE users (
  user_id char(40) NOT NULL PRIMARY KEY
) ENGINE=InnoDB;

-- Load the data
LOCK TABLES assessments WRITE, submissions WRITE, problems WRITE, problem_types WRITE, observed_events WRITE, resources_urls WRITE, resources WRITE, resource_types WRITE, urls WRITE, agent WRITE, os WRITE;
-- /*!40000 ALTER TABLE assessments DISABLE KEYS */;
-- /*!40000 ALTER TABLE submissions DISABLE KEYS */;
-- /*!40000 ALTER TABLE problems DISABLE KEYS */;
-- /*!40000 ALTER TABLE problem_types DISABLE KEYS */;
-- /*!40000 ALTER TABLE observed_events DISABLE KEYS */;
-- /*!40000 ALTER TABLE resources_urls DISABLE KEYS */;
-- /*!40000 ALTER TABLE resources DISABLE KEYS */;
-- /*!40000 ALTER TABLE resource_types DISABLE KEYS */;
-- /*!40000 ALTER TABLE urls DISABLE KEYS */;
-- /*!40000 ALTER TABLE agent DISABLE KEYS */;
-- /*!40000 ALTER TABLE os DISABLE KEYS */;
SET sql_log_bin=0;
LOAD DATA LOCAL INFILE 'os.csv' IGNORE INTO TABLE os FIELDS OPTIONALLY ENCLOSED BY '"' TERMINATED BY ','; 
LOAD DATA LOCAL INFILE 'agent.csv' IGNORE INTO TABLE agent FIELDS OPTIONALLY ENCLOSED BY '"' TERMINATED BY ','; 
LOAD DATA LOCAL INFILE 'urls.csv' IGNORE INTO TABLE urls FIELDS OPTIONALLY ENCLOSED BY '"' TERMINATED BY ','; 
LOAD DATA LOCAL INFILE 'resource_types.csv' IGNORE INTO TABLE resource_types FIELDS OPTIONALLY ENCLOSED BY '"' TERMINATED BY ','; 
LOAD DATA LOCAL INFILE 'resources.csv' IGNORE INTO TABLE resources FIELDS OPTIONALLY ENCLOSED BY '"' TERMINATED BY ','; 
LOAD DATA LOCAL INFILE 'resources_urls.csv' IGNORE INTO TABLE resources_urls FIELDS OPTIONALLY ENCLOSED BY '"' TERMINATED BY ','; 
LOAD DATA LOCAL INFILE 'observed_events.csv' IGNORE INTO TABLE observed_events FIELDS OPTIONALLY ENCLOSED BY '"' TERMINATED BY ','; 
LOAD DATA LOCAL INFILE 'problem_types.csv' IGNORE INTO TABLE problem_types FIELDS OPTIONALLY ENCLOSED BY '"' TERMINATED BY ','; 
LOAD DATA LOCAL INFILE 'problems.csv' IGNORE INTO TABLE problems FIELDS OPTIONALLY ENCLOSED BY '"' TERMINATED BY ','; 
LOAD DATA LOCAL INFILE 'submissions.csv' IGNORE INTO TABLE submissions FIELDS OPTIONALLY ENCLOSED BY '"' TERMINATED BY ','; 
LOAD DATA LOCAL INFILE 'assessments.csv' IGNORE INTO TABLE assessments FIELDS OPTIONALLY ENCLOSED BY '"' TERMINATED BY ','; 
SET sql_log_bin=1;
/*!40000 ALTER TABLE os ENABLE KEYS */;
/*!40000 ALTER TABLE agent ENABLE KEYS */;
/*!40000 ALTER TABLE urls ENABLE KEYS */;
/*!40000 ALTER TABLE resource_types ENABLE KEYS */;
/*!40000 ALTER TABLE resources ENABLE KEYS */;
/*!40000 ALTER TABLE resources_urls ENABLE KEYS */;
/*!40000 ALTER TABLE observed_events ENABLE KEYS */;
/*!40000 ALTER TABLE problem_types ENABLE KEYS */;
/*!40000 ALTER TABLE problems ENABLE KEYS */;
/*!40000 ALTER TABLE submissions ENABLE KEYS */;
/*!40000 ALTER TABLE assessments ENABLE KEYS */;
UNLOCK TABLES;

INSERT INTO users SELECT DISTINCT user_id FROM observed_events;

/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;
/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;

