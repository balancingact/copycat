cp init.d/copycat-agent.service /usr/lib/systemd/system/

yum -y install epel-release
yum -y install python-pip python-twisted-web
pip install --upgrade pip
pip install pymysql sortedcontainers

firewall-cmd --permanent --zone=public --add-rich-rule="rule family="ipv4" source address="192.168.41.181" port protocol="tcp" port="23456" accept"
firewall-cmd --reload

systemctl enable copycat-agent
systemctl start copycat-agent