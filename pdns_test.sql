--
-- Database: `powerdns`
--

USE powerdns;

-- --------------------------------------------------------

--
-- Table structure for table `domains`
--

CREATE TABLE IF NOT EXISTS `domains` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `name` varchar(255) NOT NULL,
  `master` varchar(128) DEFAULT NULL,
  `last_check` int(11) DEFAULT NULL,
  `type` varchar(6) NOT NULL,
  `notified_serial` int(11) DEFAULT NULL,
  `account` varchar(40) DEFAULT NULL,
  PRIMARY KEY (`id`)
);

--
-- Dumping data for table `domains`
--

INSERT INTO `domains` (`id`, `name`, `master`, `last_check`, `type`, `notified_serial`, `account`) VALUES
(7, 'byub.local', NULL, NULL, 'NATIVE', NULL, NULL),
(14, 'byub.edu', NULL, NULL, 'NATIVE', NULL, NULL),
(15, '71.168.192.in-addr.arpa', NULL, NULL, 'NATIVE', NULL, NULL);


--
-- Table structure for table `records`
--

CREATE TABLE IF NOT EXISTS `records` (
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

--
-- Dumping data for table `records`
--

INSERT INTO `records` (`id`,`domain_id`,`name`, `type`, `content`, `ttl`, `prio`, `change_date`, `disabled`, `ordername`, `auth`) VALUES
(1, 7,	'byub.local', 'NS', '192.168.21.78', 60, NULL, 2016091300, 0, NULL, 1),
(2, 7,	'byub.local', 'NS', '192.168.21.79', 60, NULL, 2016091300, 0, NULL, 1),
(3, 14,	'media.storage.byu.edu', 'NS', '192.168.80.169', 3600, NULL, 2016091400, 0, NULL, 1),
(4, 14,	'junk.byu.edu', 'A', '192.168.10.252', 60, NULL, 2016091400, 0, NULL, 1),
(5, 14,	'junk1.byu.edu', 'A', '192.168.10.252', 60, NULL, 2016091400, 0, NULL, 1),
(6, 15,	'71.168.192.in-addr.arpa', 'NS', '192.168.21.78', 60, NULL, 2016092900, 0, NULL, 1),
(7, 15,	'71.168.192.in-addr.arpa', 'NS', '192.168.21.79', 60, NULL, 2016092900, 0, NULL, 1),
(8, 15,	'4.71.168.192.in-addr.arpa', 'PTR', 'byub-encode.byu.edu', 60, NULL, 2016092900, 0, NULL, 1),
(9, 15,	'11.71.168.192.in-addr.arpa', 'PTR', 'byub-mbms-proxy.byu.edu', 60, NULL, 2016092900, 0, NULL, 1),
(10, 15,	'19.71.168.192.in-addr.arpa', 'PTR', 'byub-mam-app1.byu.edu', 60, NULL, 2016092900, 0, NULL, 1),
(11, 15,	'20.71.168.192.in-addr.arpa', 'PTR', 'byub-mam-app2.byu.edu', 60, NULL, 2016092900, 0, NULL, 1),
(12, 15,	'21.71.168.192.in-addr.arpa', 'PTR', 'byub-mam-app3.byu.edu', 60, NULL, 2016092900, 0, NULL, 1),
(13, 15,	'22.71.168.192.in-addr.arpa', 'PTR', 'byub-mam-app4.byu.edu', 60, NULL, 2016092900, 0, NULL, 1),
(14, 15,	'24.71.168.192.in-addr.arpa', 'PTR', 'byub-mam-gw.byu.edu', 60, NULL, 2016092900, 0, NULL, 1),
(15, 15,	'27.71.168.192.in-addr.arpa', 'PTR', 'byub-kirk.byu.edu', 60, NULL, 2016092900, 0, NULL, 1),
(16, 15,	'29.71.168.192.in-addr.arpa', 'PTR', 'byub-spock.byu.edu', 60, NULL, 2016092900, 0, NULL, 1),
(17, 15,	'31.71.168.192.in-addr.arpa', 'PTR', 'byub-scotty.byu.edu', 60, NULL, 2016092900, 0, NULL, 1),
(18, 15,	'50.71.168.192.in-addr.arpa', 'PTR', 'byub-render-0', 60, NULL, 2016092900, 0, NULL, 1),
(19, 15,	'51.71.168.192.in-addr.arpa', 'PTR', 'byub-render-01', 60, NULL, 2016092900, 0, NULL, 1),
(20, 15,	'52.71.168.192.in-addr.arpa', 'PTR', 'byub-render-02', 60, NULL, 2016092900, 0, NULL, 1),
(21, 15,	'53.71.168.192.in-addr.arpa', 'PTR', 'byub-render-03', 60, NULL, 2016092900, 0, NULL, 1),
(22, 15,	'54.71.168.192.in-addr.arpa', 'PTR', 'byub-render-04', 60, NULL, 2016092900, 0, NULL, 1),
(23, 15,	'55.71.168.192.in-addr.arpa', 'PTR', 'byub-render-05', 60, NULL, 2016092900, 0, NULL, 1),
(24, 15,	'56.71.168.192.in-addr.arpa', 'PTR', 'byub-render-06', 60, NULL, 2016092900, 0, NULL, 1),
(25, 15,	'57.71.168.192.in-addr.arpa', 'PTR', 'byub-render-07', 60, NULL, 2016092900, 0, NULL, 1),
(26, 15,	'58.71.168.192.in-addr.arpa', 'PTR', 'byub-render-08', 60, NULL, 2016092900, 0, NULL, 1),
(27, 15,	'59.71.168.192.in-addr.arpa', 'PTR', 'byub-render-09', 60, NULL, 2016092900, 0, NULL, 1),
(28, 15,	'60.71.168.192.in-addr.arpa', 'PTR', 'byub-render-10', 60, NULL, 2016092900, 0, NULL, 1),
(29, 15,	'61.71.168.192.in-addr.arpa', 'PTR', 'byub-render-11', 60, NULL, 2016092900, 0, NULL, 1);
