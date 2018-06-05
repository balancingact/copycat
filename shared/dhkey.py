"""Python implementation of DiffieHellman key exchange."""

import hashlib
from random import randint
from binascii import hexlify


class DiffieHellman(object):
    """DiffieHellman class."""

    predefined_p = (
        "BF264BACD9687876666DE89A1C2D4AEA32D4C8CCC4D5AD3E1A9D98CC1D2BB59B5B7E9A5D1B4A79A3A1D24A9E4A1D2C6B97A4A1D2E"
        "34C8D9B3B2D1A36A4C8D9EA1C2D3B6D8E4A4D1C2B3D6E8A4A1D23C6B6D4D8A69E64A1AD1A3D7C7E7E41B3C32A21A5D9E98E5E451D"
        "2C3D5D7E8E4E2D3C15D7B8A1D2C35D9E9E963D1C1A4D8E85D1A3D2C1DDA2A1B3D3D5A4C12E2D4A47D86D2D1C3D2D2A4B44D4D14C1"
        "A3D35D5E8E96D5D3A1D2C1D1DC15D8D5B5D3A1D1E41E4D8D86A1D1C2B4D77E58C1D1A13DB58D5A1D2D5D8E5D5D2E2E2C4D47D7A9A"
        "694B1D2D5A74D1C2D54E2E3D1C5D4D2E1E3E6E9E97787654A1A3D2A1DB1B1B1DC1D1E2A31CD2A3B1DF1F1F3DF6D97AC13DF798AA3"
        "A2D498EEE3E31C1DF32DF3D57F93D21E32C1E3F9D87FB3D1BA32BA3D21AC6E1EA3CE3CA2D6ADCCDA13A3D55D44A44D4A67A48112D"
        "7C7D132165798125181C5D92C54D3CA7DA3B738AD73BA1E1E1A1D4D7D78D5D11C2A2CA4D77A9C8CA7CA7AC799AC46AC1AC11E3E12"
        "1E1AE645AE798978A3C13AD2B3ABAB44A4DA76F7F77FF45E5EE2C21C1C4D47D7ECED32C1E32D1CE65D4C9E8DEDF6541ED11D1D11D"
        "111D11D3D35D67E76E23D12D1C33DC557C7E7C9EC3C3C33C4D4D447D7D79D7D4D11D2ED13D54E6C41A33A33C3D34E11E23F5498D7"
        "63C21D32C6D879C1D951D95F1DF13D21BD1B2D43797C08F4DF435C93402849236C3FAB4D27C7026C1D4DCB2602646DEC9751E763D"
        "BA37BDF8FF9406AD9E530EE5DB382F413001AEB06A53ED9027D831179727B0865A8918DA3EDBEBCF9B14ED44CE6CBACED4BB1BDB7"
        "F1447E6CC254B332051512BD7AF426FB8F401378CD2BF5983CA01C64B92ECF032EA15D1721D03F482D7CE6E74FEF6D55E702F4698"
        "0C82B5A84031900B1C9E59E7C97FBEC7E8F323A97A7E36CC88BE0F1D45B7FF585AC54BD407B22B4154AACC8F6D7EBF48E1D814CC5"
        "ED20F8037E0A79715EEF29BE32806A1D58BB7C5DA76F550AA3D8A1FBFF0EB19CCB1A313D55CDA56C9EC2EF29632387FE8D76E3C04"
        "68043E8F663F4860EE12BF2D5B0B7474D6E694F91E6DCC4024FFFFFFFFFFFFFFFF"
    )
    predefined_g = 2

    # p, g, and publicKey should be open to the other party
    def __init__(self, p=None, g=None, privateKey=None, publicKey=None):
        """Initialize key exchange."""
        self.p = p
        self.g = g
        if p is None or g is None:
            self.p = int(self.predefined_p, 16)
            self.g = self.predefined_g
        if privateKey is None or publicKey is None:
            self.privateKey = self.generatePriKey()
            self.publicKey = self.generatePubKey()
        else:
            self.privateKey = privateKey
            self.publicKey = publicKey

    def generatePriKey(self):
        """Return private key."""
        return randint(2, self.p - 1)

    def generatePubKey(self):
        """Return public key."""
        return pow(self.g, self.privateKey, self.p)

    def generateKey(self, anotherKey):
        """Generate Keys."""
        self.sharedSecret = pow(anotherKey, self. privateKey, self.p)
        s = hashlib.sha256()
        s.update(str(self.sharedSecret))
        self.key = s.digest()

    def getKey(self):
        """Return hex formatted key."""
        return hexlify(self.key)

    def getKeySize(self):
        """Return key size."""
        return len(self.key) * 8

    def showDHKeyExchange(self):
        """Print Key exchange information."""
        print "Prime (p): ", self.p
        print "Generator (g): ", self.g
        print "Private key: ", self.privateKey
        print "Public key: ", self.publicKey
        print "Shared secret: ", self.sharedSecret
        print "Shared key: ", self.getKey()
        print "Size of the key (bits):", self.getKeySize()


if __name__ == '__main__':

    # TEST SET : DiffieHellman Key Exchange
    # alice = DiffieHellman(0x7fffffff, 2)
    # bob = DiffieHellman(0x7fffffff, 2)

    alice = DiffieHellman()
    bob = DiffieHellman()

    alice.generateKey(bob.publicKey)
    bob.generateKey(alice.publicKey)

    if(alice.getKey() == bob.getKey()):
        print "=============== Alice ==============="
        alice.showDHKeyExchange()
        print "===============  Bob  ==============="
        bob.showDHKeyExchange()
    else:
        print "Something is wrong!! Shared keys does not match!!"
