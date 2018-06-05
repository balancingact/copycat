rm -rf copycat-master.zip
rm -rf copycat-agent.zip
rm -rf copycat
mkdir copycat

cp master/agent.py copycat/
cp master/copycat-master.py copycat/
cp master/emailer.py copycat/
cp master/filters.json copycat/
cp master/install.sh copycat/
cp master/master.cfg copycat/
cp master/README copycat/

cp shared/communicator.py copycat/
cp shared/dhkey.py copycat/
cp shared/filters.py copycat/
cp shared/records.py copycat/
cp ../../Templates/Python/util.py copycat/

mkdir copycat/init.d
cp master/init.d/copycat-master.service copycat/init.d/

zip -r copycat-master.zip copycat

rm -rf copycat
mkdir copycat

cp agent/agent.cfg copycat/
cp agent/copycat-agent.py copycat/
cp agent/install.sh copycat/

cp shared/communicator.py copycat/
cp shared/dhkey.py copycat/
cp shared/filters.py copycat/
cp shared/records.py copycat/
cp ../../Templates/Python/util.py copycat/

mkdir copycat/init.d
cp agent/init.d/copycat-agent.service copycat/init.d/

zip -r copycat-agent.zip copycat

rm -rf copycat