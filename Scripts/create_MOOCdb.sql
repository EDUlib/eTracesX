
CREATE DATABASE IF NOT EXISTS MOOCdb_XXXXX;
USE MOOCdb_XXXXX;

SET SQL_MODE="NO_AUTO_VALUE_ON_ZERO";
SET time_zone = "+00:00";

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
DROP TABLE IF EXISTS feedbacks;
DROP TABLE IF EXISTS questions;
DROP TABLE IF EXISTS answers;
DROP TABLE IF EXISTS surveys;
DROP TABLE IF EXISTS collaborations;
DROP TABLE IF EXISTS collaboration_types;
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


-- --------------- COMMON --------------- --
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

-- course_metadata table -- From MIT Coursea script... Why we need that? Not in MOOCdb definition!
-- CREATE TABLE course_metadata (
--   title varchar(255) DEFAULT NULL,
--   start_date date DEFAULT NULL,
--   wrap_up_date date DEFAULT NULL,
--   last_release_date date DEFAULT NULL,
--   midterm_exam_resource_id int(11) DEFAULT NULL,
--   final_exam_resource_id int(11) DEFAULT NULL,
--   release_periodicity enum(all_at_course_start,weekly,biweekly) DEFAULT NULL,
--   uses_peer_grading int(1) DEFAULT NULL,
--   uses_self_grading int(1) DEFAULT NULL,
--   uses_staff_grading int(1) DEFAULT NULL,
--   has_problems int(1) DEFAULT NULL,
--   has_in_video_quizzes int(1) DEFAULT NULL,
--   has_open_ended_assignments int(1) DEFAULT NULL,
--   uses_soft_deadlines int(1) DEFAULT NULL,
--   uses_hard_deadlines int(1) DEFAULT NULL,
--   allows_drop_in int(1) DEFAULT NULL,
--   offers_certificates int(1) DEFAULT NULL,
--   offers_verified_certificates int(1) DEFAULT NULL,
--   uses_video_pip int(1) DEFAULT NULL,
--   uses_annotated_slide_instruction int(1) DEFAULT NULL,
--   uses_static_slides_instruction int(1) DEFAULT NULL,
--   uses_board_style_instruction int(1) DEFAULT NULL
-- ) ENGINE=InnoDB;


-- --------------- OBSERVED EVENTS --------------- --
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
-- Dumping data for table `resource_types` -- GENERATED by the MOOCdb pipeline
-- INSERT INTO `resource_types` (`resource_type_id`, `resource_type_content`, `resource_type_medium`) VALUES
-- (1, 'content_section', 'text'),
-- (2, 'tutorial', 'video'),
-- (3, 'informational', 'video'),
-- (4, 'problem', 'text'),
-- (5, 'testing', 'text'),
-- (6, 'wiki', 'text'),
-- (7, 'forum', 'text'),
-- (8, 'profile', 'text'),
-- (9, 'index', 'text'),
-- (10, 'book', 'text'),
-- (11, 'survey', 'text'),
-- (12, 'home', 'text'),
-- (13, 'other', 'text'),
-- (14, 'exam', 'text'),
-- (15, 'lecture', 'video');

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
--  KEY resource_uri_idx (resource_uri),
--  KEY resource_type_idx (resource_type_id),
--  KEY resource_parent_id_idx (resource_parent_id)
) ENGINE=InnoDB;

-- resources urls table
CREATE TABLE resources_urls (
  resources_urls_id int(11) NOT NULL PRIMARY KEY,
  resource_id int(11) NOT NULL,
  url_id int(11) NOT NULL,
  FOREIGN KEY(resource_id) REFERENCES resources(resource_id) ON DELETE CASCADE,
  FOREIGN KEY(url_id) REFERENCES urls(url_id) ON DELETE CASCADE
--  KEY url_id_fk_idx (url_id),
--  KEY resources_id_fk_idx (resource_id)
) ENGINE=InnoDB;

-- observed_event_types table -- From MIT Coursea script... Why we need that? Not in MOOCdb definition!
-- CREATE TABLE observed_event_types (
--   observed_event_type_id int(11) NOT NULL PRIMARY KEY,
--   observed_event_type_name varchar(40) NOT NULL,
--   observed_event_type_activity_mode varchar(10) NOT NULL
-- ) ENGINE=InnoDB;
-- Dumping data for table observed_event_types
-- INSERT INTO observed_event_types (observed_event_type_id, observed_event_type_name, observed_event_type_activity_mode) VALUES
-- (1, index_visit, passive),
-- (2, tutorial_visit, passive),
-- (3, test_visit, passive),
-- (4, test_submission, active),
-- (5, problem_visit, passive),
-- (6, problem_submission, active),
-- (7, forum_visit, passive),
-- (8, forum_post, active),
-- (9, forum_post_read, passive),
-- (10, forum_comment, active),
-- (11, forum_vote, active),
-- (12, wiki_visit, passive),
-- (13, wiki_edit, active),
-- (14, video_play, passive),
-- (15, video_pause, passive),
-- (16, video_seek_back, passive),
-- (17, video_seek_forward, passive),
-- (18, video_speed_change, passive),
-- (19, activity_start, passive);

-- observed events table
CREATE TABLE observed_events (
  observed_event_id char(36) NOT NULL PRIMARY KEY,
--  observed_event_type_id int(11) NOT NULL,
  user_id char(40) NOT NULL,
  url_id int(11) NOT NULL,
  observed_event_timestamp datetime(6) NOT NULL,
--  observed_event_data longtext NOT NULL,
  observed_event_duration int(11) DEFAULT NULL,
  observed_event_ip char(3) DEFAULT NULL,
  observed_event_os int(11) DEFAULT NULL,
  observed_event_agent int(11) DEFAULT NULL,
  observed_event_type_id varchar(255) NOT NULL,
  FOREIGN KEY(url_id) REFERENCES resources(resource_id) ON DELETE CASCADE,
  FOREIGN KEY(observed_event_os) REFERENCES os(os_id) ON DELETE CASCADE,
  FOREIGN KEY(observed_event_agent) REFERENCES agent(agent_id) ON DELETE CASCADE
--  FOREIGN KEY(observed_event_type_id) REFERENCES observed_event_types(observed_event_type_id) ON DELETE CASCADE
--  KEY user_id_idx (user_id)
) ENGINE=InnoDB;


-- --------------- SUBMISSIONS --------------- --
-- problem types table
CREATE TABLE problem_types (
  problem_type_id int(10) NOT NULL PRIMARY KEY,
  problem_type_name varchar(255) NOT NULL
) ENGINE=InnoDB;
-- Dumping data for table `problem_types`
INSERT INTO `problem_types` (`problem_type_id`, `problem_type_name`) VALUES
(1, 'multipart'),
(2, 'question_mc_single'),
(3, 'question_mc_multiple'),
(4, 'question_free_text'),
(5, 'question_group'),
(6, 'quiz'),
(7, 'assignment'),
(8, 'assignment_part');

-- problems table
CREATE TABLE problems (
  problem_id int(11) NOT NULL PRIMARY KEY,
  problem_name varchar(127) NOT NULL,
  problem_parent_id int(11) DEFAULT NULL,
  problem_child_number int(11) DEFAULT NULL,
  problem_type_id int(11) NOT NULL,
  problem_release_timestamp datetime(6) DEFAULT NULL,
  problem_soft_deadline datetime(6) DEFAULT NULL,
  problem_hard_deadline datetime(6) DEFAULT NULL,
  problem_max_submission int(11) DEFAULT NULL,
  problem_max_duration int(11) DEFAULT NULL,
  problem_weight int(11) DEFAULT NULL,
  resource_id int(11) DEFAULT NULL,
  FOREIGN KEY(problem_parent_id) REFERENCES problems(problem_id) ON DELETE CASCADE,
  FOREIGN KEY(problem_type_id) REFERENCES problem_types(problem_type_id) ON DELETE CASCADE,
  FOREIGN KEY(resource_id) REFERENCES resources(resource_id) ON DELETE CASCADE
--  KEY problem_name_idx (problem_name),
--  KEY problem_parent_id_idx (problem_parent_id),
--  KEY problem_type_id_idx (problem_type_id),
--  KEY resource_id_idx (resource_id)
) ENGINE=InnoDB;

-- submissions table
CREATE TABLE submissions (
  submission_id char(36) NOT NULL PRIMARY KEY,
  user_id char(40) NOT NULL,
  problem_id int(11) NOT NULL,
  submission_timestamp datetime(6) NOT NULL,
  submission_attempt_number int(11) NOT NULL,
  submission_answer text NOT NULL,
  submission_is_submitted int(1) NOT NULL,
  submission_ip char(3) DEFAULT NULL,
  submission_os int(11) DEFAULT NULL,
  submission_agent int(11) DEFAULT NULL,
  FOREIGN KEY(problem_id) REFERENCES problems(problem_id) ON DELETE CASCADE,
  FOREIGN KEY(submission_os) REFERENCES os(os_id) ON DELETE CASCADE,
  FOREIGN KEY(submission_agent) REFERENCES agent(agent_id) ON DELETE CASCADE
--  KEY user_id (user_id,problem_id),
--  KEY user_idx (user_id),
--  KEY problem_idx (problem_id)
) ENGINE=InnoDB;

-- assessments table
CREATE TABLE assessments (
  assessment_id char(36) NOT NULL PRIMARY KEY,
  submission_id char(36) NOT NULL,
  assessment_feedback text,
  assessment_grade double DEFAULT NULL,
--  assessment_max_grade double DEFAULT NULL,
  assessment_grade_with_penalty double DEFAULT NULL,
  assessment_grader_id varchar(63) NOT NULL,
  assessment_timestamp datetime(6) DEFAULT NULL,
  FOREIGN KEY(submission_id) REFERENCES submissions(submission_id) ON DELETE CASCADE
--  KEY `submission_id_idx` (`submission_id`),
--  KEY `grader_id_idx` (`assessment_grader_id`)
) ENGINE=InnoDB;


-- --------------- COLLABORATIONS --------------- --
-- collaboration_types table
CREATE TABLE collaboration_types (
  collaboration_type_id int(11) NOT NULL PRIMARY KEY,
  collaboration_type_name varchar(45) NOT NULL
) ENGINE=InnoDB;
-- Dumping data for table `collaboration_types`
INSERT INTO `collaboration_types` (`collaboration_type_id`, `collaboration_type_name`) VALUES
(1, 'forum_post'),
(2, 'forum_answer'),
(3, 'forum_comment'),
(4, 'forum_vote'),
(5, 'wiki_edit');

-- collaborations table
CREATE TABLE collaborations (
  collaboration_id char(36) NOT NULL PRIMARY KEY,
  user_id char(40) NOT NULL,
  collaboration_type_id int(11) NOT NULL,
  collaboration_content text NULL,
  collaboration_timestamp datetime(6) NOT NULL,
  collaboration_parent_id int(11) DEFAULT NULL,
  collaboration_child_number int(11) DEFAULT NULL,
  collaborations_ip char(3) DEFAULT NULL,
  collaborations_os int(11) DEFAULT NULL,
  collaborations_agent int(11) DEFAULT NULL,
  resource_id int(11) DEFAULT NULL,
  FOREIGN KEY(collaboration_type_id) REFERENCES collaboration_types(collaboration_type_id) ON DELETE CASCADE
--  KEY user_id_idx (user_id),
--  KEY collaboration_type_id_idx (collaboration_type_id),
--  KEY collaboration_parent_idx (collaboration_parent_id),
--  KEY resource_id_idx (resource_id)
) ENGINE=InnoDB;

-- collaboration_content table -- From MIT Coursea script... Why we need that? Not in MOOCdb definition!
-- CREATE TABLE collaboration_content (
--   collaboration_id int(11) NOT NULL PRIMARY KEY,
--   collaboration_content longtext,
--   FOREIGN KEY(collaboration_id) REFERENCES collaborations(collaboration_id) ON DELETE CASCADE  
-- ) ENGINE=InnoDB;


-- --------------- FEEDBACKS --------------- --
-- surveys table
CREATE TABLE surveys (
  survey_id int(11) NOT NULL PRIMARY KEY,
  survey_start_timestamp datetime(6) DEFAULT NULL,
  survey_end_timestamp datetime(6) DEFAULT NULL
) ENGINE=InnoDB;

-- answers table
CREATE TABLE answers (
  answer_id int(11) NOT NULL PRIMARY KEY,
  answer_content text
) ENGINE=InnoDB;

-- questions table
CREATE TABLE questions (
  question_id int(11) NOT NULL PRIMARY KEY,
  question_content text,
  question_type int(11) DEFAULT NULL,
  question_reference int(11) DEFAULT NULL,
  survey_id int(11) DEFAULT NULL,
  FOREIGN KEY(survey_id) REFERENCES surveys(survey_id) ON DELETE CASCADE
--  KEY survey_fk_idx (survey_id)
) ENGINE=InnoDB;

-- feedbacks table
CREATE TABLE feedbacks (
  feedback_id int(11) NOT NULL PRIMARY KEY,
  user_id int(11) NOT NULL,
  answer_id int(11) NOT NULL,
  question_id int(11) NOT NULL,
  feedback_timestamp datetime(6) DEFAULT NULL,
  FOREIGN KEY(answer_id) REFERENCES answers(answer_id) ON DELETE CASCADE,
  FOREIGN KEY(question_id) REFERENCES questions(question_id) ON DELETE CASCADE
--  KEY user_id_fk_idx (user_id),
--  KEY question_id_fk_idx (question_id),
--  KEY answer_id_fk_idx (answer_id)
) ENGINE=InnoDB;


-- --------------- USERS --------------- --
-- user_types table -- From MIT Coursea script... Why we need that?
-- CREATE TABLE user_types (
--   user_type_id int(11) NOT NULL PRIMARY KEY,
--   user_type_name varchar(45) DEFAULT NULL,
-- ) ENGINE=InnoDB;
-- Dumping data for table `user_types`
-- INSERT INTO `user_types` (`user_type_id`, `user_type_name`) VALUES
-- (1, 'Administrator'),
-- (2, 'Instructor'),
-- (3, 'Teaching Staff'),
-- (4, 'Student'),
-- (5, 'Blocked'),
-- (6, 'Student Access'),
-- (7, 'Community TA'),
-- (8, 'School Administrator'),
-- (9, 'Student (Forum Banned)');

-- user table
CREATE TABLE users (
  user_id char(40) NOT NULL PRIMARY KEY
--   user_name varchar(30) DEFAULT NULL,
--   user_email text NOT NULL,
--   user_gender tinyint(4) DEFAULT NULL,
--   user_birthdate date DEFAULT NULL,
--   user_country varchar(3) DEFAULT NULL,
--   user_ip int(10) unsigned DEFAULT NULL,
--   user_timezone_offset int(11) DEFAULT NULL,
--   user_final_grade double DEFAULT NULL,
--   user_join_timestamp datetime(6) DEFAULT NULL,
--   user_os int(11) DEFAULT NULL,
--   user_agent int(11) DEFAULT NULL,
--   user_language int(11) DEFAULT NULL,
--   user_screen_resolution varchar(45) DEFAULT NULL,
--   user_type_id int(11) DEFAULT NULL,
--   FOREIGN KEY(user_type_id) REFERENCES user_types(user_type_id) ON DELETE CASCADE,
--   KEY username (user_name),
--   KEY id (user_id),
--   KEY user_type_id_fk_idx (user_type_id)
) ENGINE=InnoDB;

-- user_pii table -- From MIT Coursea script... Why we need that? Not in MOOCdb definition!
-- CREATE TABLE user_pii (
--   user_id char(40) NOT NULL PRIMARY KEY,
--   user_name varchar(255) DEFAULT NULL,
--   user_email varchar(80) DEFAULT NULL,
--   user_gender varchar(20) DEFAULT NULL,
--   user_birthdate date DEFAULT NULL,
--   user_country varchar(3) DEFAULT NULL,
--   user_ip int(10) unsigned DEFAULT NULL,
--   user_timezone_offset int(11) DEFAULT NULL
-- ) ENGINE=InnoDB;


-- Load the data
LOCK TABLES feedbacks WRITE, questions WRITE, answers WRITE, surveys WRITE, collaborations WRITE, collaboration_types WRITE, assessments WRITE, submissions WRITE, problems WRITE, problem_types WRITE, observed_events WRITE, resources_urls WRITE, resources WRITE, resource_types WRITE, urls WRITE, agent WRITE, os WRITE;
-- /*!40000 ALTER TABLE feedbacks DISABLE KEYS */;
-- /*!40000 ALTER TABLE questions DISABLE KEYS */;
-- /*!40000 ALTER TABLE answers DISABLE KEYS */;
-- /*!40000 ALTER TABLE surveys DISABLE KEYS */;
-- /*!40000 ALTER TABLE collaborations DISABLE KEYS */;
-- /*!40000 ALTER TABLE collaboration_types DISABLE KEYS */;
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
-- LOAD DATA LOCAL INFILE 'problem_types.csv' IGNORE INTO TABLE problem_types FIELDS OPTIONALLY ENCLOSED BY '"' TERMINATED BY ','; 
LOAD DATA LOCAL INFILE 'problems.csv' IGNORE INTO TABLE problems FIELDS OPTIONALLY ENCLOSED BY '"' TERMINATED BY ','; 
LOAD DATA LOCAL INFILE 'submissions.csv' IGNORE INTO TABLE submissions FIELDS OPTIONALLY ENCLOSED BY '"' TERMINATED BY ','; 
LOAD DATA LOCAL INFILE 'assessments.csv' IGNORE INTO TABLE assessments FIELDS OPTIONALLY ENCLOSED BY '"' TERMINATED BY ','; 
-- LOAD DATA LOCAL INFILE 'collaboration_types.csv' IGNORE INTO TABLE collaboration_types FIELDS OPTIONALLY ENCLOSED BY '"' TERMINATED BY ','; 
LOAD DATA LOCAL INFILE 'collaborations.csv' IGNORE INTO TABLE collaborations FIELDS OPTIONALLY ENCLOSED BY '"' TERMINATED BY ','; 
LOAD DATA LOCAL INFILE 'surveys.csv' IGNORE INTO TABLE surveys FIELDS OPTIONALLY ENCLOSED BY '"' TERMINATED BY ','; 
LOAD DATA LOCAL INFILE 'answers.csv' IGNORE INTO TABLE answers FIELDS OPTIONALLY ENCLOSED BY '"' TERMINATED BY ','; 
LOAD DATA LOCAL INFILE 'questions.csv' IGNORE INTO TABLE questions FIELDS OPTIONALLY ENCLOSED BY '"' TERMINATED BY ','; 
LOAD DATA LOCAL INFILE 'feedbacks.csv' IGNORE INTO TABLE feedbacks FIELDS OPTIONALLY ENCLOSED BY '"' TERMINATED BY ','; 
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
/*!40000 ALTER TABLE collaboration_types ENABLE KEYS */;
/*!40000 ALTER TABLE collaborations ENABLE KEYS */;
/*!40000 ALTER TABLE surveys ENABLE KEYS */;
/*!40000 ALTER TABLE answers ENABLE KEYS */;
/*!40000 ALTER TABLE questions ENABLE KEYS */;
/*!40000 ALTER TABLE feedbacks ENABLE KEYS */;
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

