var child_process = require('child_process')
var child = 0;

function log(data, lvl) {
   console.log(data);
}

function send(data) {
   if (child == 0)
      log('error: python child is null');
   child.stdin.write(JSON.stringify(data) + '\n');
}

function init(on_data) {
   child = child_process.spawn(__dirname + '/py_stdcom.py')
   //child.stdin.write(data);
   child.stderr.on('data', function(data) {
      log('js: got error from python:' + String(data));
   });
   child.stdout.on('data', function(data) {
      //document.write(data);
      var msg = JSON.parse(data);
      if (msg['magic'] != 'gentoo_sicp_rms')
         log('error: bad python message');
      on_data(JSON.stringify(msg));
   });
}

exports.init = init
exports.send = send
