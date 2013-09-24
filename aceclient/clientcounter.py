'''
Simple Client Counter for VLC VLM
'''

class ClientCounter:
  def __init__(self):
    self.clients = dict()
    self.aces = dict()
    
  def get(self, id):
    return self.clients.get(id, False)
    
  def add(self, id):
    if self.clients.has_key(id):
      self.clients[id] += 1
    else:
      self.clients[id] = 1
      
    return self.clients[id]
  
  def delete(self, id):
    if self.clients.has_key(id):
      if self.clients[id] == 1:
	del self.clients[id]
	return False
      else:
	self.clients[id] -= 1
    else:
      return False
	
    return self.clients[id]
  
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