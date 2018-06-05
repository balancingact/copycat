cp init.d/copycat-master.service /usr/lib/systemd/system/

yum -y install epel-release
yum -y install mariadb-server mariadb
systemctl enable mariadb
systemctl start mariadb
mysql_secure_installation

echo "Setup powerdns mysql database?[Y/n]"
read create
if [ "$create" == "" ] || [ "$create" == "Y" ] || [ "$create" == "y" ] ; then
	echo "Creating powerdns database"
	mysql -u root -p < pdns_integrate.sql
else
	echo "Skipping creation of powerdns database"
fi

yum -y install python-pip python-twisted-web
pip install --upgrade pip
pip install pymysql sortedcontainers

while : ; do
	ip=""
	port=""
	echo "IP address of agent [ENTER to finish]"
	read ip
	[[ -n $ip ]] || break
	echo "Port of agent [ENTER to cancel]"
	read port
	[[ -n $port ]] || continue

	firewall-cmd --permanent --zone=public --add-rich-rule="rule family="ipv4" source address="$ip" port protocol="tcp" port="$port" accept"
done
firewall-cmd --reload

systemctl enable copycat-master
systemctl start copycat-master