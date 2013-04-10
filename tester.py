import socket
import sys
import json
 
HOST = 'localhost'
PORT = 22001
 
try:
  sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
except socket.error, msg:
  sys.stderr.write("[ERROR] %s\n" % msg[1])
  sys.exit(1)
 
try:
  sock.connect((HOST, PORT))
except socket.error, msg:
  sys.stderr.write("[ERROR] %s\n" % msg[1])
  sys.exit(2)

print "Enter plugin name: ",
p = {'name':raw_input(),'type':'sync'}
print "--------------"
print
k,v = raw_input(),raw_input()

params = {}

while True:
	if k == "quit":
		break
	params[k] = v
	k,v = raw_input(),raw_input()
p['data'] = params
sock.send(json.dumps(p))
#sock.send(json.dumps({'name':'quit'}))

sock.close()

 
sys.exit(0)