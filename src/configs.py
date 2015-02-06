from icloak_lib import misc
import ileni_log, os
import binascii, codecs

class ConfigurationManager(object):
   def __init__(self, ileni):
      super(ConfigurationManager, self).__init__()
      self.ileni = ileni

      if ileni.in_icloak:
         ileni.conf_path = '/etc/icloak-tor-controller.conf'
      else:
         ileni.conf_path = ileni.app_path + '/data/ilenirc'

      if misc.file_exists(ileni.conf_path) and ileni.in_icloak:
         conf = misc.read_conf(ileni.conf_path)
      else:
         conf = _gen_default_json_conf(self)

      #with open('/dev/urandom', 'r') as f:
         #tp = ileni.tor_pass = base64.b64encode(f.read(64)).decode('utf-8')
      tp = binascii.hexlify(os.urandom(64))
      tp = codecs.decode(tp, 'utf-8')
      ileni.tor_pass = tp
      ileni.tor_pass_hash = _hash_tor_pass(tp)

      ileni.c = conf
      self.update_settings()

   def reset_settings(self):
      ileni = self.ileni
      ileni.c = _gen_default_json_conf()
      self.update_settings()

   #writes to ilenirc and updates variables
   #based on current ConfigurationManager state
   def update_settings(self):
      ileni = self.ileni
      c = ileni.c
      #print c

      tor_path = c['tor-path']
      torrc_path = c['torrc-path']

      misc.write_file(torrc_path, self._gen_torrc_str())
      #kkkkk misc.write_conf(ileni.conf_path, c)
      ileni.tor_launch_str = self._gen_tor_launch_str(tor_path, torrc_path)
   def _gen_tor_launch_str(self, tor_path, torrc_path):
      return '%s -f %s' % (tor_path, torrc_path)
   def _gen_torrc_str(self):
      ileni = self.ileni
      c = ileni.c
      torrc_str = ''
      if self.ileni.in_icloak:
         torrc_str = '\nDataDirectory /opt/tor-data' #%s/data/tor-data' % self.ileni.app_path
      torrc_str += '\nControlPort %i' % c['control-port']
      torrc_str += '\nSocksPort %i' % c['socks-port']
      torrc_str += '\nHashedControlPassword %s' % ileni.tor_pass_hash

      bs = c['bridges']
      ps = c['proxies']

      if bs is not None:

         bridge_str  = '\nUseBridges 1'
         bridge_str += '\nClientTransportPlugin obfs3 exec %s managed' % c['obfsproxy-path']

         for bridge in bs['manual']:
            bridge_str += '\nBridge ' + bridge
         torrc_str += bridge_str

      if ps is not None:
         #torrc_str += '\nTunnelDirConns 1' #kk
         pType = pUname = pPass = pAuth = None
         pType = ps['type']
         #pUname = misc.get_key(ps, 'uname')
         #pPass = misc.get_key(ps, 'pass_')
         #pPort = misc.get_key(ps, 'port')
         #pAddr = ps['addr']
         pUname = ps.get('uname', None)
         pPass  = ps.get('pass_', None)
         pPort  = ps.get('port', None)
         pAddr  = ps.get('addr', None)

         if pType == 'SOCKS4':
            pType = 'Socks4Proxy'

         elif pType == 'SOCKS5':
            pType = 'Socks5Proxy'
            if pType is not None and pPass is not None:
               if pAuth != '' and pPass != '':
                  pAuth  = '\nSocks5ProxyUsername ' + pUname
                  pAuth += '\nSocks5ProxyPassword ' + pPass

         elif pType == 'HTTPS':
            pType = 'HTTPSProxy'
            torrc_str += '\nReachableAddresses *:80,*:443'
            torrc_str += '\nReachableAddresses reject *:*'
            if pType is not None and pPass is not None:
               if pAuth != '' and pPass != '':
                  pAuth = '\nHTTPSProxyAuthenticator %s:%s' % (pUname, pPass)

         else:
            ileni_log.handle_error(
                  'CUSTOM', 'Unknown error',
                  msg='Unknown proxy type "%s"' % pType)

         proxy_str = '\n%s %s' % (pType, pAddr)
         if pPort is not None:
            proxy_str += ':' + pPort
         torrc_str += proxy_str
         if pAuth:
            torrc_str += pAuth

      torrc_str += '\n'
      return torrc_str

#

def _gen_default_json_conf(self):
   ileni = self.ileni
   app_path = ileni.app_path

   if ileni.in_icloak:
      browser_path = '/usr/bin/start-tor-browser'
      tor_path = '/usr/bin/icloak-tor'
   else:
      browser_path = app_path + '/data/browser-bundle/start-tor-browser'
      tor_path = '/usr/bin/tor'

   transports_path = app_path + '/data/transports'
   obfsproxy_path = transports_path + '/obfsproxy/bin/obfsproxy'

   return {
      'transports-path' : transports_path,
      'obfsproxy-path'  : obfsproxy_path,
      'updater-path'    : '/usr/bin/icloak-update-check',
      'tor-path'        : tor_path,
      'torrc-path'      : app_path + '/data/torrc',
      'browser-path'    : browser_path,
      'control-port'    : 9047,
      'socks-port'      : 9069,
      'proxies'         : None,
      'bridges'         : None
   }

def _hash_tor_pass(tor_pass):
   #TODO: easier with pexpect regex?
   pHash = misc.exec_get_stdout('tor --hash-password ' + tor_pass)
   pHash = codecs.decode(pHash[0].splitlines()[-1], 'utf-8')
   return pHash


