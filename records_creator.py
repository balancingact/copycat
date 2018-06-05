#!/usr/bin/python

############################## Records Creator ##################################
#                                                                               #
#   Script to create dummy records in the powerdns database.                    #
#                                                                               #
# Author: J Lyons                                                               #
# Created: 10/20/2016                                                           #
# Last Update: 10/20/2016                                                       #
#                                                                               #
#################################################################################

import pymysql
import records
from string import ascii_lowercase

def insertDB(name, t, content, cursor):
    cursor.execute("""INSERT INTO `records`
                (`domain_id`,`name`, `type`, `content`, `ttl`, `prio`, `change_date`, `disabled`, `ordername`, `auth`)
            VALUES
                (7, '""" + name + """', '""" + t + """', '""" + content + """', 60, NULL, 2016100510, 0, NULL, 1)""")
    
one = 127
two = 0
three = 0
four = 1

conn = pymysql.connect(host='localhost', port=3306, user='root', password='32alpha#', db='powerdns', autocommit=True)
cur = conn.cursor()


for a in ascii_lowercase:
    for b in ascii_lowercase:
        for c in ascii_lowercase:
            insertDB("byub.local", "NS", str(one) + "." + str(two) + "." + str(three) + "." + str(four), cur)
            for i in range(0, 10):
                insertDB("byub-" + a + b + c + ".byu.edu", "A", str(one) + "." + str(two) + "." + str(three) + "." + str(four), cur)
                insertDB(str(four) + "." + str(three) + "." + str(two) + "." + str(one) + ".in-addr.arpa", "PTR", "byub-" + a + b + c, cur)
                four += 1
                if four == 256:
                    four %= 255
                    three += 1
                    if three == 256:
                        three %= 255
                        two += 1