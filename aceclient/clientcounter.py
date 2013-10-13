'''
Simple Client Counter for VLC VLM
'''


class ClientCounter(object):

    def __init__(self):
        self.clients = dict()
        self.aces = dict()
        self.total = 0

    def get(self, id):
        return self.clients.get(id, (False,))[0]

    def add(self, id, ip):
        if self.clients.has_key(id):
            self.clients[id][0] += 1
            self.clients[id][1].append(ip)
        else:
            self.clients[id] = [1, [ip]]

        self.total += 1
        return self.clients[id][0]

    def delete(self, id, ip):
        if self.clients.has_key(id):
            self.total -= 1
            if self.clients[id][0] == 1:
                del self.clients[id]
                return False
            else:
                self.clients[id][0] -= 1
                self.clients[id][1].remove(ip)
        else:
            return False

        return self.clients[id][0]

    def getAce(self, id):
        return self.aces.get(id, False)

    def addAce(self, id, value):
        if self.aces.has_key(id):
            return False

        self.aces[id] = value
        return True

    def deleteAce(self, id):
        if not self.aces.has_key(id):
            return False

        del self.aces[id]
        return True
