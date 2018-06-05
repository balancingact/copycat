from dhkey import DiffieHellman

class Agent():
    """
    Class for handling and containing individual agent information.
    
    @type   alive:      boolean
    @ivar   alive:      Whether the agent is alive or not. Defaults to False.
    @type   name:       string
    @ivar   name:       The unique name of the agent
    @type   addr:       string
    @ivar   addr:       Address of this agent (i.e. '192.168.0.2:23456')
    @type   agent_key:  DiffieHellman()
    @ivar   agent_key:  This agent's DiffieHellman key
    """
    alive = False
    name = ""
    addr = ""
    agent_key = DiffieHellman()
    
    def __init__(self, addr, name, alive=True):
        self.addr = "http://" + addr
        self.name = name
        self.alive = alive
        
    def getAddress(self):
        return self.addr
    
    def getAddr(self):
        return self.addr.split("http://")[1]
    
    def getName(self):
        return self.name
    
    def setStatus(self, alive):
        self.alive = alive
    
    def isAlive(self):
        return self.alive
    
    def generateKey(self, publicKey):
        self.agent_key.generateKey(publicKey)
    
    def generateNewKey(self):
        self.agent_key = DiffieHellman()
    
    def getPublicKey(self):
        return self.agent_key.publicKey
    
    def getKey(self):
        return self.agent_key.getKey()
    
    def getDict(self):
        return {'name': self.name, 'addr': self.addr, 'alive': self.alive}
    
    def __str__(self):
        return self.name + "\n\tAddress: " + self.addr + "\t\t" + str(self.alive)
        
    def __nonzero__(self):
        return self.alive