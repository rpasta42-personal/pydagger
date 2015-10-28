function get_file(path, callback, encoding) {
   if ( !encoding )
      encoding = 'utf8';
   global.fs.readFile(path, encoding, callback);
}

function init() {
	var $ = global.$;
   global.__dirname = __dirname;
   global.user = null;
   global.session = null;
   global.fs = require('fs');
   var path = require('path');
   var onering = require('updater');
   var server_path = path.resolve(global.__dirname + '/../bin/OneRingServer/Linux/OneRing');

   function on_init_app() {
      if ( global.user == null ) {
         $(window).trigger("active-page", "page-create-account");
      } else {
         $(window).trigger("active-page", "page-login");
      }
   }

	$(global.window.document).ready(function(){
      // stdio transport for communicating with server
      var keyring = new onering(server_path, ['service', '-s', '--path', '/tmp/test_keyring']); // this is the api wrapper
      global.keyring = keyring; // making it available to everything
      console.log(keyring);
      // Catch all error when rpc call errors occur
      keyring.on("error", function(error) {
         console.log("UNHANDLED CALL ERROR", error);
      });

      // Once api is connected we start here
      keyring.on("connected", function() {
         keyring.get_api_version()
            .result(function(data) {
               console.log("onering api version: ", data);
            })
            .error(function(error) {
               console.log("error!", error);
            });

         keyring.list_accounts()
            .result(function(data) {
               if ( data.length > 0 ) {
                  global.user = data[0];
                  $("#login-user").text(global.user);
                  keyring.start_session(global.user, "")
                     .result(function(data) {
                        global.session = data;
                        on_init_app();
                     })
                     .error(function(error) {
                        console.log(error);
                     });
               } else {
                  global.user = 'default';
                  keyring.create_account(global.user)
                     .result(function(data) {
                        keyring.start_session(global.user, "")
                           .result(function(data) {
                              global.session = data;
                              on_init_app();
                           })
                           .error(function(error) {
                              console.log(error);
                           });
                     })
                     .error(function(error) {
                        console.log(error)
                     });
               }

            })
            .error(function(error) {
               // TODO: Handle api call error
               console.log(error);
            });

      });

      keyring.start();

	});
}

